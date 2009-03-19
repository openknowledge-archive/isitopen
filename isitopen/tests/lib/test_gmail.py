import isitopen.lib.gmail as G

import imaplib

imapError = imaplib.IMAP4.error

class MockGmail(object):
    
    def login(self, user, pwd):
        """Login to the mock IMAP server"""
        if user == "mockuser" and pwd == "mockpasswd":
            return ('OK', ['[CAPABILITY IMAP4rev1 LITERAL+ SASL-IR LOGIN-REFERRALS ID ENABLE SORT THREAD=REFERENCES MULTIAPPEND UNSELECT IDLE CHILDREN NAMESPACE UIDPLUS LIST-EXTENDED I18NLEVEL=1 CONDSTORE QRESYNC ESEARCH ESORT SEARCHRES WITHIN CONTEXT=SEARCH] Logged in'])
        else:
            raise imapError("Authentication failed")
    
    def logout(self):
        pass
    
    def list(self, path):
        """List available mailboxes at given path"""
        # TODO add INBOX here so we can mock filtering messages to the appropriate threads.
        if path == "thread":
            return  ('OK', ['(\\HasChildren) "/" "thread"', 
                            '(\\HasNoChildren) "/" "thread/1234"',
                            '(\\HasNoChildren) "/" "thread/2345"',
                            '(\\HasNoChildren) "/" "thread/3456"',
                            '(\\HasNoChildren) "/" "thread/4567"'])
        else:
            return ('OK', [None])
    
    def select(self, box="INBOX"):
        """Select a mailbox"""
        self.mailbox = box
        if box == "thread/1234":
            return ('OK', ['2'])
        else:
            return ('OK', ['0'])
            
    def search(self, charset, criteria):
        """Search for messages matching criteria"""
        if self.mailbox == 'thread/1234' and criteria.upper() == "ALL":
            return ('OK', ['1 2'])
        else:
            return ('OK', [''])
        
    def fetch(self, number, what):
        # TODO return some messages here!
        pass
        
    def close(self):
        pass

class TestGmailLogin:    
    
    def test_login(self):
        gm = G.Gmail(MockGmail(), 'mockuser', 'mockpasswd')
        assert gm.logged_in
        gm.logout()
        
    def test_login_fail(self):
        gm = G.Gmail(MockGmail(), 'mockuser', 'notthepassword')
        assert not gm.logged_in
        gm.logout()
        
    # TODO test fail on other operations when not logged in.

class TestGmailThread:
    
    @classmethod
    def setup_class(self):
        self.gmail = G.Gmail(MockGmail(), 'mockuser', 'mockpasswd')
        assert self.gmail.logged_in
        
    @classmethod
    def teardown_class(self):
        self.gmail.logout()
    
    def test_threads(self):
        assert self.gmail.threads() == ['1234', '2345', '3456', '4567']
    
    def test_unread(self):
        assert self.gmail.unread() == {}
    
    # def _test_unread(self):
    #         m1 = self.out[0]
    #         assert len(self.out) == 2
    #         assert m1.is_multipart()
    #         ctype = m1.get_content_type()
    #         assert ctype == 'multipart/alternative'
    #         # first part is text/plain, 2nd part is text/html
    #         submsg = m1.get_payload(0)
    #         body = submsg.get_payload()
    #         assert body.startswith('Messages that are easy to find'), body
    #         msgid = m1['message-id']
    #         assert msgid == '<b9df8f3e0901090812k69ed71b0x@mail.gmail.com>', msgid
    #     
    def _test_unread_2(self):
        m2 = self.out[1]
        assert not m2.is_multipart()
        ctype = m2.get_content_type()
        assert ctype == 'text/plain'
        body = m2.get_payload()
        assert body == 'testing python api\r\n', '"%s"' % body


