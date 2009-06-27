import nose
from nose.tools import *

from isitopen.tests import *
import isitopen.lib.mailsync as ms

class TestMailSync:
    
    def setup(self):
        import os, imaplib
        self.imap = imaplib.IMAP4('localhost', 8143)
        self.imap.login(os.environ['USER'], 'pass')
        self.imap.create('FIXTURE')
        msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        msg2 = "Delivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>\r\nFrom: John Doe <john.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n"
        self.imap.append('FIXTURE', None, None, msg1)
        self.imap.append('FIXTURE', None, None, msg2)
        Fixtures.create()

    def teardown(self):
        self.imap.delete('FIXTURE')
        self.imap.logout()
        model.repo.rebuild_db()
    
    def test_check_mail(self):
        e = model.Enquiry.query.first()
        assert_equal( len(e.messages), 1 )
        ms.check_mail()
        assert_equal( len(e.messages), 3 )
        assert_equal( e.messages[1].email['Message-Id'], "<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>" )
