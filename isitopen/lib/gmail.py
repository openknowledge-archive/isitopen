import imaplib
import email

from pylons import config

class Gmail(object):
    '''Inteface to gmail via IMAP and SMTP.'''
    
    def __init__(self, conn, user, pwd):
        """
        Create a new Gmail instance based on an IMAP connection and login
        credentials.
        
        conn should be an instance of imaplib.{IMAP4,IMAP4_SSL} or an object
        that behaves similarly.
        """
        self.thread_mailbox = 'thread'
        self.logged_in = False
        self.conn = conn
        self.user = user
        self.pwd = pwd
        self.login()
    
    def login(self):
        """Login to the server. This is called by default on instantiation."""
        if not self.logged_in:
            # The following raises on failure.
            self.conn.login(self.user, self.pwd) 
            self.logged_in = True
            
        return self.logged_in
    
    def threads(self):
        """
        Return a list of threads.
        
        In this context, threads are children of the mailbox with a name equal
        to self.thread_mailbox, which is "thread" by default. This does not in
        any way correspond to Gmail's "conversation" feature.
        """
        assert self.logged_in, "Not logged in."
        
        stat, boxes = self.conn.list(self.thread_mailbox)
        assert stat == 'OK'
        
        threads = []
        for box in boxes:
            # TODO don't assume the hierarchy delimiter has length 1
            thread = box.split(' ')[-1].strip("\"")[len(self.thread_mailbox) + 1:]
            if thread != "": threads.append(thread)
        
        return threads
    
    def inbox_unread(self):
        """Return a dict {msgId: email, ...} of unread messages in the INBOX."""
        assert self.logged_in, "Not logged in."
        return self.messages_for_mailbox('INBOX', 'UNSEEN')
    
    def messages_for_mailbox(self, mailbox, condition='ALL'):
        """Return a dict {msgId: email, ...} of messages in `mailbox` matching `condition`."""
        assert self.logged_in, "Not logged in."
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
        """Logout from the server. The connection cannot be reopened."""
        self.conn.close()
        self.conn.logout()
        self.logged_in = False

    @classmethod
    def default(cls):
        '''Return a default Gmail instance based on config in your ini file.'''
        if config.get('enquiry.email_user', ''):
            USER = config['enquiry.email_user']
            PWD = config['enquiry.email_pwd']
            return cls(imaplib.IMAP4_SSL('imap.gmail.com', 993), USER, PWD)
        else:
            return None
