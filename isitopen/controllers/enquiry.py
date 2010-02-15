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
            self._receive_enquiry(self._default_start_vars())
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
                self._receive_enquiry(self._default_start_vars())
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
            self._receive_enquiry(self._default_start_vars())
            c.is_step1 = True
        return render('enquiry/start.html')

    def followup(self, environ, start_response, id):
        formvars = self._receive(environ)
        c.enquiry = model.Enquiry.query.get(id)
        if not self._can_follow_up_enquiry():
            self._redirect_to_enquiry(id=id)
            return
        mid = formvars.get('mid')
        if mid:
            c.message = model.Message.query.get(mid)
        else:
            c.message = None
        if c.message:
            c.is_step3 = True
        elif formvars.get('confirm'):
            self._receive_follow_up(formvars)
            self._validate_follow_up()
            if not c.error:
                self._follow_up_enquiry()
                self._redirect_to_follow_up_enquiry(id=c.enquiry.id, mid=c.message.id)
                return
            else:
                c.is_step1 = True
        elif formvars.get('followup'):
            c.is_step2 = True
            self._receive_follow_up(formvars)
            self._validate_follow_up()
            if not c.error:
                class MockMessage: pass
                c.message = MockMessage()
                c.message.to = c.follow_up_to
                c.message.subject = c.follow_up_subject
                c.message.body = c.follow_up_body
            else:
                c.is_step1 = True
        else:
            if formvars.get('edit'):
                self._receive_follow_up(formvars)
            else:
                self._receive_follow_up(self._default_follow_up_vars())
            c.is_step1 = True
        if c.is_step1:
            default_vars = self._default_follow_up_vars()
            to_example = default_vars['to']
            subject_example = default_vars['subject'].decode('utf8')
            c.follow_up_to_example = to_example
            c.follow_up_subject_example = subject_example
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

    def _default_start_vars(self):
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
        elif c.enquiry_body == self._default_start_vars()['body'].decode('utf8').replace('\n','\r\n'):
            c.error = u'The body of the enquiry has not been changed.'
        else:
            self._validate_email_address(c.enquiry_to)

    def _receive_follow_up(self, formvars):
        c.follow_up_to = formvars.get('to')
        c.follow_up_subject = formvars.get('subject').decode('utf8')
        c.follow_up_body = formvars.get('body').decode('utf8')

    def _default_follow_up_vars(self):
        message = c.enquiry.messages[0]
        to = message.to
        subject = u'Re: %s' % message.subject
        body = u'\n\n\n'
        body += '%s %s wrote:' % (c.user.firstname, c.user.lastname)
        body += '\n> ' + '\n> '.join(message.body.splitlines()) 
        formvars = {
            'to': to,
            'subject': subject.encode('utf8'),
            'body': body.encode('utf8'),
        }
        return formvars

    def _validate_follow_up(self):
        c.error = ''
        if not c.follow_up_to:
            c.error = u'You have not specified to whom the follow up should be sent.'
        elif not c.follow_up_subject:
            c.error = u'The summary of the follow up is missing.'
        elif not c.follow_up_body:
            c.error = u'The body of the follow up is missing.'
        elif c.follow_up_body.strip() == self._default_follow_up_vars()['body'].decode('utf8').replace('\n','\r\n').strip():
            c.error = u'The body of the follow up has not been changed.'
            # Wierdly seems to lose one leading new line per errorful submission.
            # Add new line to start of an unchanged follow up body.
            c.follow_up_body = "\n" + c.follow_up_body
        else:
            self._validate_email_address(c.follow_up_to)

    def _start_enquiry(self):
        to = c.enquiry_to
        subject = c.enquiry_subject
        body = c.enquiry_body + self._mailer().enquiry_footer
        from_addr = self._mailer().enquiry_from_addr
        email_message = self._mailer().write(body, To=to, Subject=subject, From=from_addr)
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
        from_addr = self._mailer().enquiry_from_addr
        email_message = self._mailer().write(body, To=to, Subject=subject, From=from_addr)
        original = c.enquiry.messages[0]
        email_message['In-Reply-To'] = original.email['Message-Id']
        refs = original.email.get('References', '')
        refs += ' <%s>' % original.email['Message-Id']
        email_message['References'] = refs
        c.message = model.Message(
            mimetext=email_message.as_string().decode('utf8'),
            status=model.Message.NOT_SENT,
            sender=c.enquiry.owner.email,
            enquiry=c.enquiry,
        )
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

