import imaplib
import email

class IMAP(object):
    '''IMAP interface to Google Mail.'''

    INBOX = 'INBOX'
    ALL_MAIL = '[Google Mail]/All Mail'
    SENT_MAIL = '[Google Mail]/Sent Mail'
    TRASH = '[Google Mail]/Trash'
    
    def __init__(self, conn=None, user=None, pwd=None, host=None):
        """
        Initialise IMAP interface with given connection or account details.
        
        conn should be an instance of imaplib.{IMAP4,IMAP4_SSL} or an object
        that behaves similarly.
        """
        self.allmail = self.ALL_MAIL
        self.sent = self.SENT_MAIL
        self.logged_in = False
        self.conn = conn
        self.user = user
        self.pwd = pwd
        self.host = host
        if self.conn == None:
            if self.user == None or self.pwd == None or self.host == None:
                from pylons import config
            if self.user == None:
                self.user = config['enquiry.imap_user']
            if self.host == None:
                self.host = config['enquiry.imap_host']
            if self.pwd == None:
                self.pwd = config['enquiry.imap_pwd']
            if not self.host:
                raise Exception, "Need IMAP host to be specified in config."
            if not self.user:
                raise Exception, "Need IMAP user to be specified in config."
            if not self.pwd:
                raise Exception, "Need IMAP pwd to be specified in config."
        self.login()
        self.delim = self._delimiter()
        
    def login(self):
        """Login to the server. This is called by default on instantiation."""
        if not self.conn:
            self.conn = imaplib.IMAP4_SSL(self.host, 993)
            self.logged_in = False
        if not self.logged_in:
            # The following raises on failure.
            self.conn.login(self.user, self.pwd) 
            self.logged_in = True
    
    def get_mailbox_ids(self, mailbox_name='', condition='ALL'):
        """Returns list of mailbox ids in given mailbox.""" 
        self._select_mailbox(mailbox_name)
        return self._search_mailbox(condition)

    def _select_mailbox(self, mailbox_name):
        """Change selected mailbox."""
        if not mailbox_name:
            mailbox_name = self.INBOX 
        mailbox_name = self.delim.join(mailbox_name.split('/')) # ?
        stat, data = self.conn.select(mailbox_name)
        self._check("select mailbox '%s'" % mailbox_name, stat)

    def _search_mailbox(self, condition):
        """Return list of mailbox ids in previously selected mailbox.""" 
        stat, data = self.conn.search(None, condition)
        if stat != 'OK':
            msg = "Couldn't search mailbox (return status: '%s')." % stat
            raise Exception, msg
        try:
            mailbox_ids = data[0].split()
        except Exception, inst:
            raise Exception, "Couldn't read mailbox search data: %s: %s" (repr(data), inst)
        mailbox_ids.reverse()
        return mailbox_ids
 
    def get_mailbox_message(self, mailbox_id):
        stat, data = self.conn.fetch(mailbox_id, '(RFC822)')
        purpose = "fetch mailbox message '%s'" % mailbox_id
        self._check(purpose, stat, data)
        try:
            return data[0][1]
        except Exception, inst:
            raise Exception, "Couldn't read mailbox message data: %s: %s" (repr(data), inst)
        raise Exception, "Could read mailbox message data: %s: %s" (repr(data), inst)

    def get_unread_mailbox_ids(self, mailbox_name='', condition='UNSEEN'):
        return self.get_mailbox_ids(mailbox_name, condition)
 
    def mark_read(self, mailbox_id):
        self.conn.store(mailbox_id, '+FLAGS', '\\Seen')

    def _delimiter(self):
        stat, data = self.conn.list()
        self._check('determine mailbox delimeter', stat, data)
        return data[0].split()[1].strip("\"")
    
    def _check(self, attempting_to, stat, data=[]):
        assert stat == 'OK', "Could not " + attempting_to + ": " + ', '.join(data); 
    
    def logout(self):
        """Logout from the server. The connection cannot be reopened."""
        self.conn.logout()
        self.conn = None
        self.logged_in = False
    
    def __del__(self):
        """Destroy IMAP interface."""
        # Close IMAP connection.
        if self.logged_in:
            self.logout()
    
