from isitopen.lib.base import *

class EnquiryController(BaseController):

    def index(self, environ, start_response):
        return self.list(environ, start_response)

    def list(self, environ, start_response):
        formvars = self._receive(environ)
        c.enquiries = model.Enquiry.query.all()
        return render('enquiry/list.html')

    def view(self, environ, start_response, id):
        formvars = self._receive(environ)
        enq = model.Enquiry.query.get(id)
        if enq is None:
            abort(404)
        c.enquiry = enq
        return render('enquiry/view.html')

    def start(self, environ, start_response, id=None):
        formvars = self._receive(environ)
        if formvars.get('start'):
            # Just submitted new enquiry.
            self._receive_enquiry(formvars)
            self._validate_enquiry()
            if c.error:
                c.is_step1 = True
            else:
                if not self._is_logged_in():
                    pending_action = self._create_pending_action()
                    self._redirect_to_login(code=pending_action.id)
                    return
                c.is_step2 = True
                class MockMessage: pass
                c.message = MockMessage()
                c.message.to = c.enquiry_to
                c.message.subject = c.enquiry_subject
                c.message.body = c.enquiry_body
        elif formvars.get('restart'):
            # Reinitialising the enquiry form with submitted values.
            self._receive_enquiry(formvars)
            self._validate_enquiry()
            c.is_step1 = True
        elif not self._is_logged_in():
            # Initialising the enquiry form with default values.
            self._receive_enquiry(self._default_formvars())
            c.is_step1 = True
        elif self._is_logged_in() and not self._is_account_activated():
            # Forgotten to confirm account.
            # Todo: Support for pending enquiries in this case.
            self._redirect_to_confirm_account()
            return
        elif formvars.get('code'):
            # Restoring pending enquiry.
            code = formvars.get('code')
            pending_action = model.PendingAction.query.get(code)
            if pending_action:
                if pending_action.type == model.PendingAction.START_ENQUIRY:
                    enquiry_data = pending_action.retrieve()
                    # Initialise with previously submitted values.
                    c.enquiry_to = enquiry_data['enquiry_to']
                    c.enquiry_subject = enquiry_data['enquiry_subject']
                    c.enquiry_body = enquiry_data['enquiry_body']
                    self._validate_enquiry()
                    if not c.error:
                        # Show confirmation request.
                        c.is_step2 = True
                        class MockMessage: pass
                        c.message = MockMessage()
                        c.message.to = c.enquiry_to
                        c.message.subject = c.enquiry_subject
                        c.message.body = c.enquiry_body
                    else:
                        # Show error on form.
                        c.is_step1 = True
                else:
                    raise Exception, "Wrong action type: %s" % repr(pending_action)
            else:
                # Error, initialise with default values.
                self._receive_enquiry(self._default_formvars())
                c.is_step1 = True
        elif formvars.get('confirm'):
            # Confirming enquiry.
            self._receive_enquiry(formvars)
            self._validate_enquiry()
            if not c.error:
                self._start_enquiry()
                self._redirect_to_start_enquiry(id=c.enquiry.id)
                return
            c.is_step1 = True
        elif id:
            # Finished making new enquiry.
            c.enquiry = model.Enquiry.query.get(id)
            c.is_step3 = True
        else:
            # Initialising the enquiry form with default values.
            self._receive_enquiry(self._default_formvars())
            c.is_step1 = True
        return render('enquiry/start.html')

    def _default_formvars(self):
        to = ''
        subject = u'Data Openness Enquiry'
        if self._is_logged_in():
            fullname = u'%s %s' % (c.user.firstname, c.user.lastname)
        else:
            fullname = u'**Put Your Name Here**'
        body = self._mailer().enquiry_body_template % {'fullname': fullname}
        formvars = {
            'to': to,
            'subject': subject.encode('utf8'),
            'body': body.encode('utf8'),
        }
        return formvars

    def _receive_enquiry(self, formvars):
        c.enquiry_to = formvars.get('to')
        c.enquiry_subject = formvars.get('subject').decode('utf8')
        c.enquiry_body = formvars.get('body').decode('utf8')

    def _validate_enquiry(self):
        c.error = ''
        if not c.enquiry_to:
            c.error = u'You have not specified to whom the enquiry should be sent.'
        elif not c.enquiry_subject:
            c.error = u'The summary of the enquiry is missing.'
        elif not c.enquiry_body:
            c.error = u'The body of the enquiry is missing.'
        elif c.enquiry_body == self._default_formvars()['body'].decode('utf8').replace('\n','\r\n'):
            c.error = u'The body of the enquiry has not been changed.'
        else:
            self._validate_email_address(c.enquiry_to)

    def _start_enquiry(self):
        body = c.enquiry_body + self._mailer().enquiry_footer
        to = c.enquiry_to
        subject = c.enquiry_subject
        email_message = self._mailer().write(body, to=to, subject=subject)
        # if response_to existing message add references and in-reply-to
        #original = model.Message.query.get(c.response_to)
        #if original:
        #    tmsgid = original.email['Message-Id']
        #    email['In-Reply-To'] = tmsgid
        #    refs = original.email.get('References', '')
        #    refs += ' <%s>' % tmsgid
        #    email['References'] = refs
        c.message = model.Message(
            mimetext=email_message.as_string(),
            status=model.MessageStatus.not_yet_sent,
            sender=c.user.email
        )
        c.enquiry = model.Enquiry()
        c.enquiry.summary = c.message.subject
        c.enquiry.owner = c.user
        c.message.enquiry = c.enquiry
        model.Session.commit()

    def _create_pending_action(self):
        type = model.PendingAction.START_ENQUIRY
        pending_action = model.PendingAction(type=type)
        pending_action.store(
            enquiry_to=c.enquiry_to,
            enquiry_subject=c.enquiry_subject,
            enquiry_body=c.enquiry_body,
        )
        model.Session.commit()
        return pending_action

    def sent(self, id=None):
        c.enquiry = model.Enquiry.query.get(id)
        return render('message/sent.html')

    def send_pending(self, environ, start_response):
        formvars = self._receive(environ)
        import isitopen.lib.mailsync as sync
        import pprint
        out = '<pre>'

        out += 'Sending pending\n'
        results = sync.send_pending()
        out += '%s\n' % pprint.pformat(results)

        results = sync.sync_sent_mail()
        out += 'Syncing sent mail\n'
        out += '%s\n' % pprint.pformat(results)

        results = sync.check_for_responses()
        out += 'Syncing responses\n'
        out += '%s\n' % pprint.pformat(results)

        results = sync.send_response_notifications(self._mailer())
        out += 'Sending response notifications\n'
        out += '%s\n' % pprint.pformat(results)

        out += '</pre>'
        return out


