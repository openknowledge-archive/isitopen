import logging
import email as E

from pylons import config
from isitopen.lib.base import *
import isitopen.lib.mailer as mailer

log = logging.getLogger(__name__)

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
            # Initialising the enquiry form.
            self._receive_enquiry(formvars)
            self._validate_enquiry()
            c.is_step1 = True
        elif not self._is_logged_in():
            # Initialising the enquiry form.
            self._receive_enquiry(self._defaults())
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
            (action_name, action_data) = pending_action.retrieve()
            c.enquiry_to = action_data['enquiry_to']
            c.enquiry_subject = action_data['enquiry_subject']
            c.enquiry_body = action_data['enquiry_body']
            self._validate_enquiry()
            if not c.error:
                c.is_step2 = True
                class MockMessage: pass
                c.message = MockMessage()
                c.message.to = c.enquiry_to
                c.message.subject = c.enquiry_subject
                c.message.body = c.enquiry_body
            else:
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
            # Just initialising the enquiry form.
            self._receive_enquiry(self._defaults())
            c.is_step1 = True
        return render('enquiry/start.html')

    def _defaults(self):
        body_data = {}
        if self._is_logged_in():
            fullname = '%s %s' % (c.user.firstname, c.user.lastname)
        else:
            fullname = '**Put Your Name Here**'
        body_data['fullname'] = fullname 
        defaults = {}
        defaults['to'] = ''
        defaults['subject'] = 'Data Openness Enquiry'
        defaults['body'] = template_2 % body_data
        return defaults

    def _receive_enquiry(self, formvars):
        c.enquiry_to = formvars.get('to')
        c.enquiry_subject = formvars.get('subject')
        c.enquiry_body = formvars.get('body')

    def _validate_enquiry(self):
        c.error = ''
        if not c.enquiry_to:
            c.error = 'You have not specified to whom the enquiry should be sent.'
        elif not c.enquiry_subject:
            c.error = 'The summary of the enquiry is missing.'
        elif not c.enquiry_body:
            c.error = 'The body of the enquiry is missing.'
        elif c.enquiry_body == self._defaults()['body'].replace('\n','\r\n'):
            c.error = 'The body of the enquiry has not been changed.'
        else:
            self._validate_email_address(c.enquiry_to)

    def _start_enquiry(self):
        email = _make_email((c.enquiry_body + enquiry_footer).encode('utf8'),
            to=c.enquiry_to, subject=c.enquiry_subject
        )
        # if response_to existing message add references and in-reply-to
        #original = model.Message.query.get(c.response_to)
        #if original:
        #    tmsgid = original.email['Message-Id']
        #    email['In-Reply-To'] = tmsgid
        #    refs = original.email.get('References', '')
        #    refs += ' <%s>' % tmsgid
        #    email['References'] = refs
        c.message = model.Message(
            mimetext=email.as_string(),
            status=model.MessageStatus.not_yet_sent,
            sender=c.user.email
        )
        c.enquiry = model.Enquiry()
        c.enquiry.summary = unicode(c.message.subject, 'utf8')
        c.enquiry.owner = c.user
        c.message.enquiry = c.enquiry
        model.Session.commit()

    def _create_pending_action(self):
        pending_action = model.PendingAction()
        pending_action.store(name='start-enquiry', enquiry_to=c.enquiry_to,
            enquiry_subject=c.enquiry_subject, enquiry_body=c.enquiry_body
        )
        model.Session.commit()
        return pending_action

    def sent(self, id=None):
        c.enquiry = model.Enquiry.query.get(id)
        return render('message/sent.html')



default_from = config['enquiry.from']
def _make_email(text, **headers):
    msg = E.message_from_string(text)
    for k,v in headers.items():
        msg[k.capitalize()] = v
    if not 'From' in msg:
        msg['From'] = msg['Reply-To'] = default_from
    return msg


follow_up_email = '''It might also be good to apply a specific 'open data' licence --
you can find examples of such licenses at: ...
'''

template_2 = \
'''Dear Sir or Madam,

I am **insert pertinent information about yourself, e.g. I am a researcher in field X**.

I am writing to seek clarification of the 'openness' [1] of this data:

**insert details and perhaps an example link here**.  

I wasn't able to find an explicit statement that the data was open such as a reference to an open knowledge or data license [2] so I'm writing to find out what the exact situation is. In particular we would like to know whether the material can be made available under an open license of some kind.

Thank you very much for your time and I look forward to receiving your response.

Regards,

%(fullname)s

[1] <http://www.opendefinition.org/1.0/>  
[2] <http://www.opendefinition.org/licenses/>  
'''

enquiry_footer = '''
--  
Sent by "Is It Open?" (<http://isitopen.ckan.net/about/>)  
A service which helps scholars (and others) to request information
about the status and licensing of information.
'''
