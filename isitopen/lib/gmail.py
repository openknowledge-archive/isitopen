import imaplib
import email

class Gmail(object):
    '''Interface to gmail via IMAP and SMTP.'''
    
    def __init__(self, conn, user, pwd):
        """
        Create a new Gmail instance based on an IMAP connection and login
        credentials.
        
        conn should be an instance of imaplib.{IMAP4,IMAP4_SSL} or an object
        that behaves similarly.
        """
        
        self.thread_mailbox = 'thread'
        
        self.inbox = 'INBOX'
        self.allmail = '[Google Mail]/All Mail'
        self.sent = '[Google Mail]/Sent Mail'
        
        self.logged_in = False
        self.conn = conn
        self.user = user
        self.pwd = pwd
        self.login()
        self.delim = self._delimiter()
        
    def __del__(self):
        """Logout from the server. The connection cannot be reopened."""
        self.conn.logout()
        self.logged_in = False
    
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
        stat, boxes = self.conn.list(self.thread_mailbox)
        assert stat == 'OK'
        
        threads = []
        for box in boxes:
            # TODO don't assume the hierarchy delimiter has length 1
            print box
            thread = box.split(' ')[-1].strip("\"")[len(self.thread_mailbox) + 1:]
            if thread != "": threads.append(thread)
        
        return threads
    
    def unread(self, mailbox=None):
        """Return a dict {msgId: email, ...} of unread messages in the given mailbox."""
        if mailbox is None:
            mailbox = self.inbox
            
        return self.messages_for_mailbox(mailbox, 'UNSEEN')
    
    def messages_for_mailbox(self, mailbox, condition='ALL'):
        """Return a dict {msgId: email, ...} of messages in `mailbox` matching `condition`."""
        mailbox = self.delim.join(mailbox.split('/'))
        self._check("select mailbox '" + mailbox + "'", *self.conn.select(mailbox))
        
        stat, indices = self.conn.search(None, condition) 
        
        results = {}
        
        if indices[0]:
            for index in indices[0].split():
                stat, data = self.conn.fetch(index, '(RFC822)')
                self._check('fetch message ' + index + ' from mailbox ' + mailbox,
                            stat, data)
                                
                msg = email.message_from_string(data[0][1])
                results[index] = msg
            
        return results
                                         
    def get_message(self, message_id):
        """Return a message object corresponding to the given `message_id`. Searches
           Gmail's 'All Mail' folder."""        
        msgs = self.messages_for_mailbox(self.allmail, "(HEADER Message-Id " + message_id + ")")
        ids = msgs.keys()

        if len(ids) > 1:
            raise Exception, "Expected at most one message returned. Non-unique message ids?"
        elif len(ids) == 1:
            return ids[0], msgs[ids[0]]
            
    def mark_read(self, message):
        self.conn.select(self.allmail)
        num, msg = self.get_message(message['Message-Id'])
        self.conn.store(num, '+FLAGS', '\\Seen')
        
    def gmail_label(self, message, label):
        pass
        # something a little like...
        # num, msg = self.get_message(message['Message-Id'])
        # # check for mailbox corresponding to label and create if necessary
        # self.conn.copy(num, mbox_for_label)

    def _delimiter(self):
        stat, data = self.conn.list()
        self._check('determine mailbox delimeter', stat, data)
        return data[0].split()[1].strip("\"")
    
    def _check(self, attempting_to, stat, data):
        assert stat == 'OK', "Could not " + attempting_to + ": " + ', '.join(data); 
    
    @classmethod
    def default(cls):        
        '''Return a default Gmail instance based on config in your ini file.'''
        
        from pylons import config

        host = config['enquiry.imap_host']
        usr = config['enquiry.imap_user']
        pwd = config['enquiry.imap_pwd']
        
        if not (host and usr and pwd):
            raise Exception, "Need IMAP host/user/pwd to be specified in config."
        
        conn = imaplib.IMAP4_SSL(host, 993)
        
        instance = cls(conn, usr, pwd)
        instance.thread_mailbox = 'enquiry'
        
        if config['debug']:
            instance.inbox = "FIXTURE"
        
        return instance
        
        
