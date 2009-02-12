from isitopen.lib.base import *

import isitopen.lib.gmail

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
        if not 'commit' in request.params:
            return render('enquiry/create.html')

        # must be a commit
        return self.send()

    def send(self):
        c.error = ''
        if not c.to:
            c.error = 'You have not specified to whom the enquiry should ' + \
                    'be sent.'
            return render('enquiry/sent.html')

        enq = model.Enquiry(
                to=c.to,
                subject=c.subject,
                body=c.body
                )
        model.Session.commit()
        c.enquiry = enq
        return render('enquiry/sent.html')

    def send_pending(self):
        # need to get back the gmail id
        gmail = isitopen.lib.gmail.Gmail.default()
        msg = isitopen.lib.gmail.create_msg(c.body,
            to=c.to,
            subject=c.subject
            )
        gmail.send(msg)

    def list(self):
        c.enquiries = model.Enquiry.query.all()
        return render('enquiry/list.html')

    def view(self, id=''):
        enq = model.Enquiry.query.get(id)
        if enq is None:
            abort(404)
        c.enquiry = enq
        # annoying but needed for the template
        c.to = c.enquiry.to
        c.subject = c.enquiry.subject
        c.body = c.enquiry.body
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

