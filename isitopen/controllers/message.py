import logging
import email as E

from pylons import config
from isitopen.lib.base import *
import isitopen.lib.mailer as mailer

log = logging.getLogger(__name__)

class MessageController(BaseController):

    def index(self):
        return render('message/index.html')

    def create(self, template=''):
        class MockMessage:
            pass
        c.message = MockMessage()
        c.message.to = request.params.get('to', '')
        c.message.subject = request.params.get('subject', 'Data Openness Enquiry')
        c.message.body = request.params.get('body', template_2)
        c.sender = request.params.get('sender', '')
        c.enquiry_id = request.params.get('enquiry_id')
        if 'preview' in request.params:
            c.preview = True

        if not 'send' in request.params:
            return render('message/create.html')

        # must be a commit
        return self.save()

    def save(self):
        c.error = ''
        if not c.message.to:
            c.error = 'You have not specified to whom the enquiry should ' + \
                    'be sent.'
            return render('message/sent.html')
        email_msg = _make_email(
            c.message.body,
            to=c.message.to,
            subject=c.message.subject
            )
        message = model.Message(mimetext=email_msg.as_string(),
                status=model.MessageStatus.not_yet_sent)

        model.Session.commit()
        h.redirect_to(controller='enquiry', action='sent', id=c.enquiry_id,
                message_id=message.id)
    
    def sent(self, id):
        c.enquiry = model.Enquiry.query.get(id)
        return render('message/sent.html')


default_from = config['enquiry.from']
def _make_email(text, **headers):
    from_ = config['enquiry.from']
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
'''Dear **...**,

I am **insert information about yourself, e.g. I am a researcher in field X**.

I am writing on behalf of the Open Scientific Data Working Group of the Open Knowledge Foundation [1]. We are seeking clarification of the 'openness' of the scientific data associated with your publications such as **insert information or link here**.  

We weren't able to find an explicit statement of this fact such as a reference to an open knowledge or data license [2] so we're writing to find out what the exact situation is. In particular we would like to know whether the material can be made available under an open license of some kind [3].

Regards,

**Put Your Name Here**

[1] <http://www.okfn.org/wiki/wg/science/>  
[2] <http://www.opendefinition.org/licenses/>  
[3] <http://www.opendefinition.org/1.0/>  
'''

