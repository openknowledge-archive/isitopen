import nose
from nose.tools import *

from isitopen.tests import *
import isitopen.lib.mailsync as ms

class TestMailSync:
    
    @classmethod
    def setup_class(self):
        import isitopen.tests.helpers.dummysmtp as dsmtp
        from processing import Process, Pipe
        
        self.pipe, pipe_remote = Pipe()
        
        self.p = Process(target=dsmtp.loop, args=(pipe_remote,))
        self.p.start()
        
        ready = False
        
        while not ready:
            try:
                ready = self.pipe.recv()
            except EOFError:
                time.sleep(0.1)
                
    @classmethod
    def teardown_class(self):
        self.p.terminate()
    
    def setup(self):
        import os, imaplib
        from pylons import config
        
        host = config['enquiry.imap_host']
        usr = config['enquiry.imap_user']
        pwd = config['enquiry.imap_pwd']
        
        self.imap = imaplib.IMAP4_SSL(host)
        self.imap.login(usr, pwd)
        self.imap.create('FIXTURE')
        
        msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        msg2 = "Delivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>\r\nFrom: John Doe <john.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n"
        
        for m in [msg1, msg2]:
            self.imap.append('FIXTURE', None, None, m)
        
        Fixtures.create()

    def teardown(self):
        self.imap.delete('FIXTURE')
        self.imap.logout()
        model.repo.rebuild_db()
    
    def test_check_mail(self):
        e = model.Enquiry.query.first()
        assert_equal( len(e.messages), 2 )
        ms.check_mail()
        assert_equal( len(e.messages), 4 )
        assert_equal( e.messages[2].email['Message-Id'], "<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>" )
    
    def test_send_pending(self):
        out = ms.send_pending()
        print out
        assert_equal( out[0][1], u'Sent But Not Synced' )
  