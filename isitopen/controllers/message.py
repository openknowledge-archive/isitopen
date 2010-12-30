from isitopen.lib.base import *
import pprint

class MessageController(BaseController):

    def index(self):
        """No purpose at this time."""
        self._redirect_to_home()

    def send_pending(self):
        out1 = self.send_unsent()
        out2 = self.receive_unread()
        return out1 + '\n\n' + out2

    def send_unsent(self):
        """Send unsent email messages."""
        self._receive()
        # no sensitive info here so no need to be admin
        #if not self._is_admin_logged_in():
        #    self._redirect_to_home()
        #    return
        mailer = self._mailer()
        send_results = mailer.send_unsent()
        reread_results = mailer.reread_sent()
        out = '<!--checkpoint:send-unsent-->'
        out += '<pre>'
        out += 'Pushing unsent mail\n'
        out += '%s\n' % pprint.pformat(send_results)
        out += 'Re-reading sent mail\n'
        out += '%s\n' % pprint.pformat(reread_results)
        out += '</pre>'
        return out

    def receive_unread(self):
        """Read and handle unseen email messages."""
        self._receive()
        # no sensitive info here so no need to be admin
        #if not self._is_admin_logged_in():
        #    self._redirect_to_home()
        #    return
        mailer = self._mailer()
        pull_results = mailer.pull_unread()
        notification_results = mailer.send_response_notifications()
        out = '<!--checkpoint:receive_unread-->'
        out += '<pre>'
        out += 'Syncing responses\n'
        out += '%s\n' % pprint.pformat(pull_results)
        out += 'Sending response notifications\n'
        out += '%s\n' % pprint.pformat(notification_results)
        out += '</pre>'
        return out

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

        message = model.Message(
                mimetext=email_msg.as_string().decode('utf8'),
                status=model.Message.NOT_SENT,
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
