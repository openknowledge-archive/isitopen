import smtplib
import email
from email.mime.text import MIMEText

class Mailer(object):
    def __init__(self, conn, user, pwd):
        self.conn = conn
        self.user = user
        self.pwd = pwd
        print user, pwd
        if user and pwd:
            self.conn.starttls()
            self.conn.login(self.user, self.pwd)
        
    def send(self, msg):
        to_hdrs = ['To', 'Cc', 'Bcc']
        recipients = [msg.get(hdr, False) for hdr in to_hdrs if msg.get(hdr, False)]
        self.conn.sendmail(msg['From'], recipients, msg.as_string())
        return self
        
    def quit(self):
        self.conn.quit()
    
    @classmethod
    def message_from_default(cls, text, **headers):
        msg = MIMEText(text)
        msg['From'] = msg['Reply-To'] = '"Is It Open enquiry service" <data-enquire@okfn.org>'
        for k,v in headers.items():
            msg[k.capitalize()] = v
        return msg
        
    @classmethod
    def default(cls):
        '''Return a default Mailer instance based on config in your ini file.'''        
        from pylons import config

        host = config['enquiry.smtp_host']
        port = config['enquiry.smtp_port']
        usr = config['enquiry.smtp_user']
        pwd = config['enquiry.smtp_pwd']
                
        if not host:
            raise Exception, "Need SMTP host to be specified in config."
        
        conn = smtplib.SMTP(host, port or 587)        
        instance = cls(conn, usr, pwd)
        return instance
