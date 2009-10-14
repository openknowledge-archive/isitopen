import logging

from isitopen.lib.base import *
import isitopen.lib.mailer as mailer

log = logging.getLogger(__name__)

class EnquiryController(BaseController):

    def index(self):
        return self.list()
    
    def choose(self):
        return render('enquiry/choose.html')

    def create(self, id=None):
        h.redirect_to(controller='message', action='create', enquiry_id='new')

    def sent(self, id):
        msgid = request.params.get('message_id', '')
        # if not msgid:
        #    log.warn('No message id in sent! Enquiry id: %s' % id)
        #    msg = None
        # else:
        msg = model.Message.query.get(msgid)
        if id == 'new':
            c.enquiry = model.Enquiry()
            c.enquiry.summary = unicode(msg.subject, 'utf8')
            sender = msg.sender.strip()
            if sender:
                user = model.User.query.filter_by(email=sender).first()
                if not user:
                    user = model.User(email=sender)
                c.enquiry.owner = user
        else:
            c.enquiry = model.Enquiry.query.get(id)
        msg.enquiry = c.enquiry
        model.Session.commit()
        return render('enquiry/sent.html')

    def send_pending(self):
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

        results = sync.send_response_notifications()
        out += 'Sending response notifications\n'
        out += '%s\n' % pprint.pformat(results)

        out += '</pre>'
        return out

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

