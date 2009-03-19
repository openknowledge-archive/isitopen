import imaplib
import smtplib
import email
from email.mime.text import MIMEText

from pylons import config

def create_msg(text, **kwargs):
    msg = MIMEText(text)
    from_email = 'data-enquire@okfn.org'
    msg['From'] = from_email
    msg['Reply-To'] = from_email
    for k,v in kwargs.items():
        msg[k.capitalize()] = v
    return msg

class Gmail(object):
    '''Inteface to gmail via imap and smtp.'''
    def __init__(self, conn, user, pwd):
        self.thread_mailbox = 'thread'
        
        self.logged_in = False
        self.conn = conn
        self.user = user
        self.pwd = pwd
        self.login()
    
    def login(self):
        if self.logged_in:
            return True
        else:
            try:
                stat, msg = self.conn.login(self.user, self.pwd)
                if stat == "OK":
                    self.logged_in = True
                    return True
            except imaplib.IMAP4.error:
                return False
    
    def threads(self):
        assert self.logged_in
        stat, boxes = self.conn.list(self.thread_mailbox)
        assert stat == 'OK'
        
        threads = []
        for box in boxes:
            # TODO don't assume the hierarchy delimiter has length 1
            thread = box.split(' ')[-1].strip("\"")[len(self.thread_mailbox) + 1:]
            if thread != "": threads.append(thread)
        
        return threads
    
    def unread(self):         
        return self.messages_for_mailbox('INBOX', 'UNSEEN')
    
    def messages_for_mailbox(self, mailbox, condition = 'ALL'):
        self.conn.select(mailbox)
        
        stat, indices = self.conn.search(None, condition)
        assert stat == 'OK'

        results = {}
        for index in indices[0].split():
            stat, data = self.conn.fetch(index, '(RFC822)')
            assert stat == 'OK'
            
            msg = email.message_from_string(data[0][1])
            results[index] = msg
            
        return results
    
    def logout(self):
        self.conn.close()
        self.conn.logout()

    def send(self, msg):
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(self.user, self.pwd)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        # Should be s.quit(), but that crashes...
        s.close()

    @classmethod
    def default(self):
        '''Return a default Gmail instance based on config in your ini file.'''
        if config.get('enquiry.email_user', ''):
            USER = config['enquiry.email_user']
            PWD = config['enquiry.email_pwd']
            return Gmail(USER, PWD)
        else:
            return None
