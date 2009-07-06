import nose
from nose.tools import *

import imaplib
from isitopen.lib.gmail import Gmail

class TestGmailLogin:    
    
    def setup(self):
        from pylons import config
        
        self.host = config['enquiry.imap_host']
        self.usr = config['enquiry.imap_user']
        self.pwd = config['enquiry.imap_pwd']
        self.imap = imaplib.IMAP4_SSL(self.host)
    
    def teardown(self):
        self.imap.logout()
    
    def test_login(self):
        gm = Gmail(self.imap, self.usr, self.pwd)
        assert gm.logged_in
    
    @raises(imaplib.IMAP4.error)
    def test_login_fail(self):
        gm = Gmail(self.imap, self.usr, 'notthepassword')
        
class TestGmail:
    
    def setup(self):
        # [TODO]: factor this IMAP setup out of here into something a little 
        #         more reusable.
        
        import os, imaplib
        
        msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        msg2 = "Delivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>\r\nFrom: John Doe <john.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n"

        self.structure = {
            'allMail': [ (msg1, '()'), (msg2, '(\Seen)') ],
            'thread': {
                '1234': [ (msg1, '()'), (msg2, '(\Seen)') ],
                '2345': [],
                '3456': [],
                '4567': []
            }
        }

        from pylons import config
        
        # To run these tests successfully you will need to set these parameters
        # in your `test.ini`. I strongly recommend setting up a local IMAP4 server
        # (for example, dovecot) as running the tests directly against Gmail is
        # a) dog slow and b) prone to failure if another developer tries to run
        # against the same account.
        host = config['enquiry.imap_host']
        usr =  config['enquiry.imap_user']
        pwd =  config['enquiry.imap_pwd']

        self.imap = imaplib.IMAP4_SSL(host)
        self.imap.login(usr, pwd)
        
        self.gmail = Gmail(imaplib.IMAP4_SSL(host), usr, pwd)        
        self.gmail.allmail = 'allMail'
        
        def structure_create(imap, struct, path=''):
            for f in struct:
                imap.create(path + f)
                if isinstance(struct[f], dict):
                    structure_create(imap, struct[f], f + self.gmail.delim)
                elif isinstance(struct[f], list):
                    for msg, flags in struct[f]:
                        stat, data = imap.append(path + f, flags, None, msg)

        structure_create(self.imap, self.structure)
        
    def teardown(self):
        def structure_destroy(imap, struct, path=''):
            for f in struct:
                imap.create(path + f)
                if isinstance(struct[f], dict):
                    imap.delete(path + f);
                    structure_destroy(imap, struct[f], f + self.gmail.delim)
                else:
                    imap.delete(path + f);
        
        structure_destroy(self.imap, self.structure)
        
        self.imap.logout()
    
    def test_threads(self):
        assert_equal( self.gmail.threads(), ['1234', '2345', '3456', '4567'] )
    
    def test_unread(self):
        assert_equal( self.gmail.unread(), {} )
        
    def test_messages_for_mailbox(self):
        assert_equal( len(self.gmail.messages_for_mailbox('thread/1234', 'Seen')), 1 )
        assert_equal( len(self.gmail.messages_for_mailbox('thread/1234')), 2 )
        assert_equal( len(self.gmail.messages_for_mailbox('INBOX')), 0 )
        
    def test_messages_have_email_properties(self):
        msgs = self.gmail.messages_for_mailbox('thread/1234')
        
        assert_equal( msgs['1']['subject'], "Message 1 subject line" )
        assert_equal( msgs['2']['subject'], "Message 2 subject line" )
        
        assert_equal( msgs['1']['message-id'], "<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>" )
        assert_equal( msgs['2']['message-id'], "<83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>" )
        
        assert msgs['1'].get_payload().startswith("The body of message 1"), \
            "Message 1 doesn't start with the right string!"
        assert msgs['2'].get_payload().startswith("The body of message 2"   ), \
            "Message 2 doesn't start with the right string!"
    
    def test_get_message(self):        
        n1, msg1 = self.gmail.get_message("<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>")
        n2, msg2 = self.gmail.get_message("<83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>")
        
        assert_equal( msg1['Message-Id'], '<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>' )
        assert_equal( msg2['Message-Id'], '<83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>' )
        
        assert_equal( self.gmail.get_message("nonexistent"), None )
    
if __name__ == '__main__':
    nose.main()

