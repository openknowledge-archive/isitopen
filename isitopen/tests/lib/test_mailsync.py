import uuid
import os, imaplib

import nose
from nose.tools import *

from pylons import config

from isitopen.tests import *
import isitopen.lib.mailsync as ms
from isitopen.lib.mailer import Mailer

class TestMailSync:
    
    @classmethod
    def setup_class(self):
        self.enq_id, self.msg_id = Fixtures.create()
        email_msgid = model.Message.query.get(self.msg_id).email['Message-Id']
        notsynced = model.Message(status=model.MessageStatus.sent_not_synced)
        model.Session.commit()
        self.notsynced_id = notsynced.id
        
        host = config['enquiry.imap_host']
        usr = config['enquiry.imap_user']
        pwd = config['enquiry.imap_pwd']
        
        self.imap = imaplib.IMAP4_SSL(host)
        self.imap.login(usr, pwd)
        self.imap.create('FIXTURE')
        
        self.msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <%s@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        self.msg1 = self.msg1 % model.make_uuid().upper()
        self.msg1 = '%s: %s\r\n' % (ms.ISITOPEN_HEADER_ID, self.notsynced_id) + self.msg1
        # response to our first Fixture message (using references)
        msg2 = "Delivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <%s@gmail.com>\r\nReferences: %s\r\nFrom: John Doe <john.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n"
        msg2 = msg2 % (model.make_uuid().upper(), email_msgid)
        # response to our first Fixture message (using in-reply-to)
        msg3 = "In-Reply-To: %s\r\nDelivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <%s@gmail.com>\r\nFrom: John Doe <john.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n"
        self.email_msgid_3 = model.make_uuid().upper()
        msg3 = msg3 % (email_msgid, self.email_msgid_3)
        
        self.imap.append('[Google Mail]/Sent Mail', None, None, self.msg1)
        for m in [msg2, msg3]:
            self.imap.append('FIXTURE', None, None, m)

    @classmethod
    def teardown_class(self):
        self.imap.delete('FIXTURE')
        self.imap.logout()
        model.repo.rebuild_db()

    def test_1_sync_sent_mail(self):
        out = ms.sync_sent_mail()
        assert out[0] == [self.notsynced_id, u'Sent'], out
        now_synced = model.Message.query.get(self.notsynced_id)
        print now_synced.mimetext
        print self.msg1
        # for some reason not exactly the same
        # assert now_synced.mimetext == self.msg1
        assert now_synced.mimetext[:20] == self.msg1[:20]

    def test_3_check_for_responses(self):
        e = model.Enquiry.query.first()
        startnum = model.Message.query.count()
        assert len(e.messages) == 2, len(e.messages)
        out = ms.check_for_responses('FIXTURE')
        endnum = model.Message.query.count() 
        assert endnum == startnum + 2, endnum
        assert len(e.messages) == 4, len(e.messages)
        msgids = [ m.email['Message-Id'].split('@')[0][1:] for m in e.messages if
                m.email['Message-Id'] ]
        assert self.email_msgid_3 in msgids, msgids
        ourid = [ res[2] for res in out if res[1] == 'Synced' and
                res[0][1:].startswith(self.email_msgid_3) ]
        ourmsg = model.Message.query.get(ourid) 
        assert ourmsg.status == model.MessageStatus.response_no_notification


# These tests write (smtp) as well as read (imap)
# TODO: make them functional (ned 
class TestMailerRelated:
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
    
    def test_send_pending(self):
        out = ms.send_pending()
        # assert_equal( out[0][1], u'Sent But Not Synced' )
        # FIXME .. currently no fixtures pending.

    def test_send_response_notifications(self):
        mailer = Mailer()
        out = ms.send_response_notifications(mailer)
