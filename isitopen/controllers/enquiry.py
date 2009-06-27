from isitopen.lib.base import *

import isitopen.lib.mailer as mailer

class EnquiryController(BaseController):

    def index(self):
        return self.list()
    
    def choose(self):
        return render('enquiry/choose.html')

    def create(self, template=''):
        c.to = request.params.get('to', '')
        c.subject = request.params.get('subject', 'Data Openness Enquiry')
        c.sender = request.params.get('sender', '')
        c.body = request.params.get('body', template_2)

        if 'preview' in request.params:
            c.preview = True
        if not 'send' in request.params:
            return render('enquiry/create.html')

        # must be a commit
        return self.save()

    def save(self):
        c.error = ''
        if not c.to:
            c.error = 'You have not specified to whom the enquiry should ' + \
                    'be sent.'
            return render('enquiry/sent.html')
        enq = model.Enquiry()
        email_msg = mailer.Mailer.message_from_default(
            c.body,
            to=c.to,
            subject=c.subject
            )
        message = model.Message(enquiry=enq, mimetext=email_msg.as_string())
        model.Session.commit()
        h.redirect_to(controller='enquiry', action='sent', id=enq.id)
    
    def sent(self, id):
        c.enquiry = model.Enquiry.query.get(id)
        return render('enquiry/sent.html')

    def send_pending(self):
        pending = model.Message.query.filter_by(
                status=model.MessageStatus.not_yet_sent
                ).all()
        results = []
        for message in pending:
            try:
                # TODO: need to get back the gmail id
                # TODO: bcc sender ... 
                m = mailer.Mailer.default()
                m.send(message.email)
                message.status = model.MessageStatus.sent
                model.Session.commit()
                results.append([message.id, 'OK'])
            except:
                results.append('ERROR')
                break
        return '%s' % results

    def list(self):
        c.enquiries = model.Enquiry.query.all()
        return render('enquiry/list.html')

    def view(self, id):
        enq = model.Enquiry.query.get(id)
        if enq is None:
            abort(404)
        c.enquiry = enq
        return render('enquiry/view.html')

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

