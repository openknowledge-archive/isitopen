import smtplib
import email
from isitopen.lib.gmail import IMAP 
import isitopen.lib.helpers as h
import isitopen.model as model
import logging

log = logging.getLogger(__name__)


class Mailer(object):
    """
    Writes, sends and receives IsItOpen system email (models "Thunderbird").
    """

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
        self.smtp_host = config['enquiry.smtp_host']
        if not self.smtp_host:
            errmsg = "Missing 'enquiry.smtp_host' in config."
            raise Exception, errmsg
        self.smtp_port = config.get('enquiry.smtp_port', 587)
        self.smtp_user = config['enquiry.smtp_user']
        self.smtp_pwd = config['enquiry.smtp_pwd']
        self.smtp = None

    def init_smtp(self):
        """Create and initialise SMTP connection."""
        if self.smtp == None:
            self.smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
            # not required in python >= 2.6 as part of starttls
            self.smtp.ehlo()
            self.smtp.starttls()
            # not required in python >= 2.6 as part of starttls
            self.smtp.ehlo()
            self.smtp.login(self.smtp_user, self.smtp_pwd)
            return True
        return False
        
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

    def send_email_confirmation_request(self, user, code):
        """Create and dispatch confirmation request."""
        message = self.write_email_confirmation_request(user, code)
        self.send(message)

    def send_unsent(self):
        """Dispatch unsent messages in model."""
        messages = model.Message.query.filter_by(
            status=model.Message.NOT_SENT).all()
        results = []
        for message in messages:
            mimetext = message.mimetext.encode('utf8')
            email_message = email.message_from_string(mimetext)
            email_message[self.ISITOPEN_HEADER_ID] = message.id
            if message.sender:
                # use bcc to ensure recipient replies to isitopen not sender
                email_message['Bcc'] = str(message.sender)
            try:
                self.send(email_message)
            except Exception, inst:
                results.append('ERROR: %s' % inst)
            else:
                message.status = model.Message.JUST_SENT
                model.Session.commit()
                results.append([message.id, message.status])
        return results

    def reread_sent(self):
        """Refresh message objects (SMTP adds Message-ID header)."""
        messages = model.Message.query.filter_by(
            status=model.Message.JUST_SENT
        ).all()
        results = []
        imap = IMAP()
        if not len(messages):
            return results
        justsent = {}
        for message in messages:
            justsent[message.id] = message
        mailbox_ids = imap.get_mailbox_ids(imap.SENT_MAIL)
        for mailbox_id in mailbox_ids:
            mailbox_message = imap.get_mailbox_message(mailbox_id)
            email_message = email.message_from_string(mailbox_message)
            header_id = email_message[self.ISITOPEN_HEADER_ID]
            if header_id in justsent:
                message = justsent.pop(header_id)
                message.mimetext = email_message.as_string().decode('utf8')
                message.status = model.Message.SENT_REREAD
                model.Session.commit()
                results.append([message.id, message.status])
            if len(justsent) == 0:
                break
        return results

    def pull_unread(self, mailbox_name=None):
        """Read received messages into model."""
        import isitopen.lib.finder
        finder = isitopen.lib.finder.Finder()
        imap = IMAP()
        results = []
        # Identify new email messages.
        mailbox_ids = imap.get_unread_mailbox_ids(mailbox_name)
        for mailbox_id in mailbox_ids:
            # Fetch message.
            mailbox_message = imap.get_mailbox_message(mailbox_id)
            # Parse email.
            email_message = email.message_from_string(mailbox_message)
            email_from = email_message['From']
            email_message_id = email_message['Message-Id']
            # Ignore bounce.
            if 'mailer-daemon@googlemail.com' in email_from:
                results.append([email_message_id, 'Skip: looks like bounce'])
                imap.mark_read(mailbox_id)
                continue
            enquiry = finder.enquiry_for_message(email_message)
            if not enquiry:
                results.append([email_message_id, 'Skip: found no related enquiry'])
                continue
            message = model.Message(
                status=model.Message.JUST_RESPONSE,
                enquiry=enquiry,
                mimetext=email_message.as_string().decode('utf8')
            )
            model.Session.commit()
            try:
                imap.mark_read(mailbox_id)
            except Exception, inst:
                results.append([email_message_id, 'ERROR: %s' % inst])
            else:
                results.append([email_message_id, message.status, message.id])
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

