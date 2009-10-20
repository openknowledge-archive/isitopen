import logging
import email as E

from pylons import config
from isitopen.lib.base import *
import isitopen.lib.mailer as mailer

log = logging.getLogger(__name__)

class MessageController(BaseController):

    def index(self):
        return render('message/index.html')

    def _defaults(self):
        original = model.Message.query.get(c.response_to)
        defaults = {}
        if original:
            defaults['to'] = original.email['From']
            # add Re: ?
            defaults['subject'] = 'Re: %s' % original.subject
            defaults['body'] = '\n\n\n> ' + '\n> '.join(original.body.splitlines())
        else:
            defaults['to'] = ''
            defaults['subject'] = 'Data Openness Enquiry'
            defaults['body'] = template_2
        return defaults

    def create(self, template=''):
        class MockMessage:
            pass
        c.message = MockMessage()

        c.sender = request.params.get('sender', '')
        c.enquiry_id = request.params.get('enquiry_id', 'new')
        c.response_to = request.params.get('response_to', '')

        # a bit complicated here because need to support previewing
        defaults = self._defaults()

        c.message.to = request.params.get('to', defaults['to'])
        c.message.subject = request.params.get('subject', defaults['subject'])
        c.message.body = request.params.get('body', defaults['body'])

        if 'preview' in request.params:
            c.preview = True

        if not 'send' in request.params:
            return render('message/create.html')
        else: # must be a commit
            return self.save()

    def save(self):
        c.error = ''
        if not c.message.to:
            c.error = 'You have not specified to whom the enquiry should ' + \
                    'be sent.'
            return render('message/sent.html')
        import formalchemy.validators
        to = c.message.to
        try:
            formalchemy.validators.email(to)
        except formalchemy.validators.ValidationError, inst:
            c.error = u'Invalid email address: %s' % inst
            return render('message/sent.html')

        body = c.message.body
        body += enquiry_footer
        email_msg = _make_email(
            body.encode('utf8'),
            to=c.message.to,
            subject=c.message.subject
            )
        # if response_to existing message add references and in-reply-to
        original = model.Message.query.get(c.response_to)
        if original:
            tmsgid = original.email['Message-Id']
            email_msg['In-Reply-To'] = tmsgid
            refs = original.email.get('References', '')
            refs += ' <%s>' % tmsgid
            email_msg['References'] = refs

        message = model.Message(mimetext=email_msg.as_string(),
                status=model.MessageStatus.not_yet_sent,
                sender=c.sender)

        model.Session.commit()
        h.redirect_to(controller='enquiry', action='sent', id=c.enquiry_id,
                message_id=message.id)
    
    def sent(self, id):
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

I am **insert information about yourself, e.g. I am a researcher in field X**.

I am writing to seek clarification of the 'openness' [1] of this data:

**insert details and perhaps an example link here**.  

I wasn't able to find an explicit statement that the data was open such as a reference to an open knowledge or data license [2] so I'm writing to find out what the exact situation is. In particular we would like to know whether the material can be made available under an open license of some kind.

Thank you very much for your time and I look forward to receiving your response.

Regards,

**Put Your Name Here**

[1] <http://www.opendefinition.org/1.0/>  
[2] <http://www.opendefinition.org/licenses/>  
'''

enquiry_footer = '''
--  
Sent by "Is It Open?" (<http://isitopen.ckan.net/about/>)  
A service which helps scholars (and others) to request information
about the status and licensing of information.
'''
