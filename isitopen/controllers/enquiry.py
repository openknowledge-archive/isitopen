from isitopen.lib.base import *
import pprint

class EnquiryController(BaseController):

    def index(self, environ, start_response):
        self._redirect_to_enquiry_list()

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
        c.can_resolve_enquiry = self._can_resolve_enquiry()
        c.can_follow_up_enquiry = self._can_follow_up_enquiry()
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

    def followup(self, environ, start_response, id=None):
        formvars = self._receive(environ)
        c.enquiry = model.Enquiry.query.get(id)
        if not self._can_follow_up_enquiry():
            self._redirect_to_enquiry(id=id)
            return
        if formvars.get('confirm'):
            c.is_step3 = True
            self._receive_follow_up(formvars)
            self._follow_up_enquiry()
        elif formvars.get('followup'):
            c.is_step2 = True
            self._receive_follow_up(formvars)
            class MockMessage: pass
            c.message = MockMessage()
            c.message.to = c.follow_up_to
            c.message.subject = c.follow_up_subject
            c.message.body = c.follow_up_body
        else:
            c.follow_up_subject = c.enquiry.summary
            c.is_step1 = True
        return render('enquiry/followup.html')

    def resolve(self, environ, start_response, id=None):
        formvars = self._receive(environ)
        c.enquiry = model.Enquiry.query.get(id)
        if self._can_resolve_enquiry():
            resolution = formvars['resolution'] or ''
            resolution = resolution.decode('utf8')
            closed_statuses = [
                model.Enquiry.STARTED,
                model.Enquiry.RESOLVED_OPEN,
                model.Enquiry.RESOLVED_CLOSED,
                model.Enquiry.RESOLVED_NOT_KNOWN,
            ]
            if resolution not in closed_statuses:
                raise Exception, "Resolution '%s' not valid Enquiry status." % resolution
            c.enquiry.status = resolution
            model.Session.commit()
            self._redirect_to_enquiry(id=c.enquiry.id)
        else:
            self._redirect_home()
            return

    def _can_follow_up_enquiry(self):
        return self._can_update_enquiry()

    def _can_resolve_enquiry(self):
        return self._can_update_enquiry()

    def _can_update_enquiry(self):
        if not c.enquiry:
            return False
        elif not self._is_logged_in():
            return False
        elif c.user.email == c.enquiry.owner.email:
            return True
        elif self._is_admin_logged_in():
            return True
        else:
            return False

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

    def _receive_follow_up(self, formvars):
        c.follow_up_to = formvars.get('to')
        c.follow_up_subject = formvars.get('subject').decode('utf8')
        c.follow_up_body = formvars.get('body').decode('utf8')

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
        to = c.enquiry_to
        subject = c.enquiry_subject
        body = c.enquiry_body + self._mailer().enquiry_footer
        email_message = self._mailer().write(body, to=to, subject=subject)
        c.enquiry = model.Enquiry.start_new(
            owner=c.user, 
            summary=c.enquiry_subject,
            email_message=email_message,
        )
        c.message = c.enquiry.messages[0]

    def _follow_up_enquiry(self):
        to = c.follow_up_to
        subject = c.follow_up_subject
        body = c.follow_up_body + self._mailer().enquiry_footer
        email_message = self._mailer().write(body, to=to, subject=subject)
        c.message = model.Message(
            mimetext=email_message.as_string().decode('utf8'),
            status=model.Message.NOT_SENT,
            sender=c.enquiry.owner.email,
            enquiry=c.enquiry,
        )
        model.Session.commit()

#    def _start_enquiry(self):
#        c.enquiry = model.Enquiry(
#            summary=c.enquiry_subject,
#            owner=c.user,
#        )
#        # Todo: Create the Mimetext later, store raw data ron object.
#        email_message = self._mailer().write(
#            c.enquiry_body + self._mailer().enquiry_footer
#            to=c.enquiry_to
#            subject=c.enquiry_subject
#        )
#        # if response_to existing message add references and in-reply-to
#        #original = model.Message.query.get(c.response_to)
#        #if original:
#        #    tmsgid = original.email['Message-Id']
#        #    email['In-Reply-To'] = tmsgid
#        #    refs = original.email.get('References', '')
#        #    refs += ' <%s>' % tmsgid
#        #    email['References'] = refs
#        c.message = model.Message(
#            mimetext=email_message.as_string(),
#            status=model.Message.NOT_SENT,
#            sender=c.user.email,
#            enquiry=c.enquiry
#        )
#        model.Session.commit()

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
        # Deprecated in favour of:
        self.flush(environ, start_response)

    # Todo: Move this to the message controller?
    def flush(self, environ, start_response):
        """Send unsent and receive unread email messages."""
        self._receive(environ)
        if self._is_admin_logged_in():
            mailer = self._mailer()
            out = '<pre>'

            out += 'Pushing unsent mail\n'
            results = mailer.send_unsent()
            out += '%s\n' % pprint.pformat(results)

            results = mailer.reread_sent()
            out += 'Pulling sent mail\n'
            out += '%s\n' % pprint.pformat(results)

            results = mailer.pull_unread()
            out += 'Syncing responses\n'
            out += '%s\n' % pprint.pformat(results)

            results = mailer.send_response_notifications()
            out += 'Sending response notifications\n'
            out += '%s\n' % pprint.pformat(results)

            out += '</pre>'
            return out

