import smtplib
import email
from isitopen.lib.gmail import Gmail 
import isitopen.lib.helpers as h
import isitopen.model as model
import logging

log = logging.getLogger(__name__)


class Mailer(object):

    email_confirmation_template = u"""
Hi %(firstname)s,

Your account has been created. To confirm your email address, follow the link below:
%(confirm_url)s
(If clicking on the link doesn't work, try copying it into your browser.)

If you did not enter this address, please disregard this message.

Take a look at the guide if you have any questions:
%(guide_url)s 

Thanks,
The Is It Open Data? Team
"""

    enquiry_body_template = u"""
Dear Sir or Madam,

I am **insert pertinent information about yourself, e.g. I am a researcher in field X**.

I am writing to seek clarification of the 'openness' [1] of this data:

**insert details and perhaps an example link here**.  

I wasn't able to find an explicit statement that the data was open such as a reference to an open knowledge or data license [2] so I'm writing to find out what the exact situation is. In particular we would like to know whether the material can be made available under an open license of some kind.

Thank you very much for your time and I look forward to receiving your response.

Regards,

%(fullname)s

[1] <http://www.opendefinition.org/1.0/>  
[2] <http://www.opendefinition.org/licenses/>  
"""

    enquiry_footer = u"""
--  
Sent by "Is It Open Data?" (<http://isitopen.ckan.net/about/>)  
A service which helps scholars (and others) to request information
about the status and licensing of information.
"""

    response_notification_template = u"""
Hi %(firstname)s,

You have received a response to your enquiry "%(enquiry_summary)s" 

Here's a link to your enquiry where you can respond:
%(write_reply_url)s

Enquiry ref: %(enquiry_id)s

Thanks,
The Is It Open Data? Team
"""

    ISITOPEN_HEADER_ID = 'X-IsItOpen-Message-Id'

    def __init__(self, site_url=None):
        """Set up attributes of mailer."""
        from pylons import config
        self.site_url = site_url
        if not self.site_url:
            self.site_url = config.get('site_url', 'http://127.0.0.1:5000')
        self.host = config['enquiry.smtp_host']
        if not self.host:
            errmsg = "Missing 'enquiry.smtp_host' in config."
            raise Exception, errmsg
        self.port = config.get('enquiry.smtp_port', 587)
        self.user = config['enquiry.smtp_user']
        self.pwd = config['enquiry.smtp_pwd']
        self.smtp = None

    def init_smtp(self):
        """Create and initialise SMTP connection."""
        if self.smtp == None:
            self.smtp = smtplib.SMTP(self.host, self.port)
            # not required in python >= 2.6 as part of starttls
            self.smtp.ehlo()
            self.smtp.starttls()
            # not required in python >= 2.6 as part of starttls
            self.smtp.ehlo()
            self.smtp.login(self.user, self.pwd)
            return True
        return False
        
    def send(self, email_message):
        """Dispatch email message object via SMTP."""
        from_addr = email_message['From']
        to_addrs = []
        for header in ['To', 'Cc', 'Bcc']:
            if email_message[header]:
                to_addrs.append(email_message[header])
        del email_message['Bcc'] # Remove any Bcc header.
        hangup = self.init_smtp()
        msg = email_message.as_string()
        # Todo: Protect this call (it can raise an exception), and examine
        # return value, see http://docs.python.org/library/smtplib.html.
        self.smtp.sendmail(from_addr, to_addrs, msg)
        if hangup:
            self.smtp.close()
            self.smtp = None
        
    def write(self, body, **headers):
        """Create and return new email message object."""
        if type(body) == unicode:
            body = body.encode('utf8')
        headers['Content-Type'] = 'text/plain; charset="utf-8"'
        message = email.message_from_string(body)
        for name, value in headers.items():
            if type(value) == unicode:
                value = value.encode('utf8')
            message[name.capitalize()] = value
        return message

    def send_email_confirmation_request(self, user, code):
        """Create and dispatch confirmation request."""
        message = self.write_email_confirmation_request(user, code)
        self.send(message)

    def write_email_confirmation_request(self, user, code):
        """Write user account email confirmation request."""
        to = user.email
        subject = u'Is It Open Data? email address confirmation'
        confirm_url = h.url_for('confirm-account', code=code)
        guide_url = h.url_for('guide')
        template_vars = {
            'firstname': user.firstname,
            'confirm_url': self.site_url + confirm_url,
            'guide_url': self.site_url + guide_url,
        }
        body = self.email_confirmation_template % template_vars
        return self.write(body, to=to, subject=subject)

    def send_unsent(self):
        """Dispatch unsent messages in model."""
        pending = model.Message.query.filter_by(
            status=model.Message.NOT_SENT).all()
        results = []
        for message in pending:
            try:
                e = message.email
                e[self.ISITOPEN_HEADER_ID] = message.id
                if message.sender:
                    # use bcc to ensure recipient replies to isitopen not sender
                    e['Bcc'] = message.sender
                    
                self.send(message.email)
                message.status = model.Message.JUST_SENT
                model.Session.commit()
                
                results.append([message.id, message.status])
            except Exception, inst:
                results.append('ERROR: %s' % inst)
        return results

    def reread_sent(self):
        """Refresh message model (SMTP adds headers)."""
        tosync = model.Message.query.filter_by(
            status=model.Message.JUST_SENT
        ).all()
        results = []
        g = Gmail.default()
        for message in tosync:
            try:
                emails = g.messages_for_mailbox(g.sent)
                for emailobj in emails.values():
                    if emailobj[self.ISITOPEN_HEADER_ID] == message.id:
                        message.mimetext = emailobj.as_string()
                        message.status = model.Message.SENT_REREAD
                        model.Session.commit()
                results.append([message.id, message.status])
            except Exception, inst:
                results.append([message.id, 'ERROR: %s' % inst])
        return results

    def pull_unread(self, mailbox=None):
        """Read received messages into model."""
        import isitopen.lib.finder
        finder = isitopen.lib.finder.Finder()
        g = Gmail.default()
        results = []
        msgs_dict = g.unread(mailbox)
        # log.debug('check_for_responses: no. of items = %s' % len(msgs_dict))
        for mboxid, message in msgs_dict.items():
            # log.debug('check_for_responses: %s, %s, %s' % (mboxid, message['from'],
            #    message['subject']) )
            # ignore bounces ....
            if 'From' in message and 'mailer-daemon@googlemail.com' in message['From']:
                results.append([message['Message-Id'], 'Skip: looks like bounce'])
                continue
            try:
                # TODO: extract timestamp etc
                enquiry = finder.enquiry_for_message(message)
                if not enquiry:
                    results.append([message['Message-Id'], 'Skip: found no related enquiry'])
                    continue

                m = model.Message(
                    status=model.Message.JUST_RESPONSE,
                    enquiry=enquiry,
                    mimetext = message.as_string()
                    )
                model.Session.commit()
                results.append([message['Message-Id'], 'Synced', m.id])
                g.mark_read(mboxid)
                # g.gmail_label(message, 'enquiry/' + m.enquiry.id) # get message from imap via MIME Message-Id, copy to "enquiry/<enq_id>"
            except Exception, inst:
                results.append([message['Message-Id'], 'ERROR: %s' % inst])
        return results

    def send_response_notifications(self):
        """Send notifications of responses to enquirer."""
        # Todo: Actually send the response with the notification (avoids frustration).
        pending = model.Message.query.filter_by(
                status=model.Message.JUST_RESPONSE
                ).all()
        results = []
        for message in pending:
            try:
                enquiry = message.enquiry
                if not enquiry.owner or not enquiry.owner.email:
                    continue
                self.send_response_notification(enquiry)
                message.status = model.Message.RESPONSE_NOTIFIED
                model.Session.commit()
                results.append([message.id, message.status])
            except Exception, inst:
                results.append('ERROR: %s' % inst)
        return results

    def send_response_notification(self, enquiry):
        """Create and dispatch response notification."""
        email_message = self.write_response_notification(enquiry)
        self.send(email_message)

    def write_response_notification(self, enquiry):
        """Write notification of response to request."""
        to = enquiry.owner.email
        subject = u'Re: %s' % enquiry.summary
        write_reply_url = h.url_for(controller='enquiry', action='view', id=enquiry.id)
        template_vars = {
            'firstname': enquiry.owner.firstname,
            'enquiry_summary': enquiry.summary,
            'write_reply_url': self.site_url + write_reply_url,
            'enquiry_id': enquiry.id,
        }
        body = self.response_notification_template % template_vars
        return self.write(body, to=to, subject=subject)

