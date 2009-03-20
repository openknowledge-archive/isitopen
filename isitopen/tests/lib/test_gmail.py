import nose
from nose.tools import *

import imaplib
from isitopen.lib.gmail import Gmail

class TestGmailLogin:    
    
    def test_login(self):
        gm = Gmail(MockGmailIMAP(), 'mockuser', 'mockpasswd')
        assert gm.logged_in
    
    @raises(imaplib.IMAP4.error)
    def test_login_fail(self):
        gm = Gmail(MockGmailIMAP(), 'mockuser', 'notthepassword')
        
    def test_methods_raise_when_not_logged_in(self):
        gm = Gmail(MockGmailIMAP(), 'mockuser', 'mockpasswd')
        gm.logout()
        assert_raises(AssertionError, gm.threads)
        assert_raises(AssertionError, gm.inbox_unread)
        assert_raises(AssertionError, gm.messages_for_mailbox, 'INBOX')
        
        
class TestGmail:
    
    def setup(self):
        self.gmail = Gmail(MockGmailIMAP(), 'mockuser', 'mockpasswd')
        assert self.gmail.logged_in, "Not logged in!"
        
    def teardown(self):
        self.gmail.logout()
    
    def test_threads(self):
        assert_equal( self.gmail.threads(), ['1234', '2345', '3456', '4567'] )
    
    def test_inbox_unread(self):
        assert_equal( self.gmail.inbox_unread(), {} )
        
    def test_messages_for_mailbox(self):
        assert_equal( len(self.gmail.messages_for_mailbox('thread/1234')), 2 )
        assert_equal( len(self.gmail.messages_for_mailbox('thread/1234', 'UNSEEN')), 1 )
        assert_equal( len(self.gmail.messages_for_mailbox('INBOX')), 0 )
        
    def test_messages_have_email_properties(self):
        msgs = self.gmail.messages_for_mailbox('thread/1234')
        
        assert_equal( msgs['1']['subject'], "Message 1 subject line" )
        assert_equal( msgs['2']['subject'], "Message 2 subject line" )
        
        assert_equal( msgs['1']['message-id'], "<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>" )
        assert_equal( msgs['2']['message-id'], "<83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>" )
        
        assert msgs['1'].get_payload().startswith("The body of message 1"), \
            "Message 1 doesn't start with the right string!"
        assert msgs['2'].get_payload().startswith("The body of message 2"), \
            "Message 2 doesn't start with the right string!"

class MockGmailIMAP(object):
    # Make me as messy as you like. It really doesn't matter.
    """A mockup of an instance of `imaplib.IMAP` or similar."""

    def __init__(self):
        self.mailbox = 'INBOX'

    def login(self, user, pwd):
        """Login to the mock IMAP server"""
        if user == "mockuser" and pwd == "mockpasswd":
            return ('OK',['mockuser@gmail.com authenticated (Success)'])
        else:
            raise imaplib.IMAP4.error("Authentication failed")

    def logout(self): pass
    def close(self): pass

    def list(self, path):
        """List available mailboxes at given path"""
        # TODO add INBOX here so we can mock filtering messages to the appropriate threads.
        if path == "thread":
            return  ('OK', ['(\\Noselect \\HasChildren) "/" "thread"', 
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
        if self.mailbox == 'thread/1234':
            if criteria.upper() == "ALL":
                return ('OK', ['1 2'])
            elif criteria.upper() == "UNSEEN":
                return ('OK', ['2'])
        else:
            return ('OK', [''])

    def fetch(self, number, what):
        if self.mailbox == 'thread/1234':
            msgs = {
                '1': ('OK', [('1 (RFC822 {426}', 'Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: "Mock User" <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n'), ')']),
                '2': ('OK', [('2 (RFC822 {426}', 'Delivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>\r\nFrom: John Doe <john.doe@example.com>\r\nTo: "Mock User" <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n'), ')'])
            }
            return msgs[number]
        else:
            return ('OK', [None])

if __name__ == '__main__':
    nose.main()

