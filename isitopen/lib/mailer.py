import smtplib
import email
import isitopen.lib.helpers as h

class Mailer(object):

    def __init__(self, conn=None, user=None, pwd=None, site_url=None):
        self.conn = conn
        self.user = user
        self.pwd = pwd
        self.site_url = site_url
        from pylons import config
        if not self.conn:
            host = config['enquiry.smtp_host']
            if not host:
                raise Exception, "Need SMTP host to be specified in config."
            port = config.get('enquiry.smtp_port', 587)
            self.conn = smtplib.SMTP(host, port)
        if not self.user:
            self.user = config['enquiry.smtp_user']
        if not self.pwd:
            self.pwd = config['enquiry.smtp_pwd']
        if self.user and self.pwd:
            # not required in python >= 2.6 as part of starttls
            self.conn.ehlo()
            self.conn.starttls()
            # not required in python >= 2.6 as part of starttls
            self.conn.ehlo()
            self.conn.login(self.user, self.pwd)
        if not self.site_url:
            self.site_url = config.get('site_url', 'http://127.0.0.1:5000')
        
    def write(self, body, **headers):
        if type(body) == unicode:
            body = body.encode('utf8')
        headers['Content-Type'] = 'text/plain; charset="utf-8"'
        message = email.message_from_string(body)
        for name, value in headers.items():
            if type(value) == unicode:
                value = value.encode('utf8')
            message[name.capitalize()] = value
        return message

    def write_email_confirmation_request(self, user, code):
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

    def write_response_notification(self, enquiry):
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

    def send(self, message):
        recipients = []
        for header in ['To', 'Cc', 'Bcc']:
            if message[header]:
                recipients.append(message[header])
        del message['Bcc'] # Remove any Bcc header.
        # Todo: Protect this call (it can raise an exception), and examine
        # return value, see http://docs.python.org/library/smtplib.html.
        self.conn.sendmail(message['From'], recipients, message.as_string())
        return self
        
    def quit(self):
        self.conn.quit()
    
    def send_email_confirmation_request(self, user, code):
        message = self.write_email_confirmation_request(user, code)
        self.send(message)

    def send_response_notification(self, enquiry):
        email_message = self.write_response_notification(enquiry)
        self.send(email_message)

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

