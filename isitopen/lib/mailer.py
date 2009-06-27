import smtplib
import email
from email.mime.text import MIMEText

class Mailer(object):
    def __init__(self, conn, user, pwd):
        self.conn = conn
        self.user = user
        self.pwd = pwd
        self.conn.starttls()
        self.conn.login(self.user, self.pwd)
        
    def send(self, msg):
        self.conn.sendmail(msg['From'], msg['To'], msg.as_string())
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
        if config.get('enquiry.email_user', ''):
            USER = config['enquiry.email_user']
            PWD = config['enquiry.email_pwd']
            return cls(smtplib.SMTP('smtp.gmail.com', 587), USER, PWD)
        else:
            return None
