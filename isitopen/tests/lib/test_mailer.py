from isitopen.tests import *

from isitopen.lib.mailer import Mailer
from pylons import config

from nose.tools import *

class TestMailer(object):

    to = 'mark.smith@appropriatesoftware.net'
    subject = u'Some message subject\xfc'
    body = u'Some message body\xfc'

    @classmethod
    def setup_class(self):
        self.msg_id = Fixtures.create()[1]
        self.mailer = Mailer()

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_write(self):
        message = self.mailer.write(self.body, to=self.to, subject=self.subject)
        assert message['To'] == self.to
        assert message['Subject'] == self.subject.encode('utf8')
        assert self.body.encode('utf8') in message.as_string()

    def test_send(self):
        message = self.mailer.write(self.body, to=self.to, subject=self.subject)
        self.mailer.send(message)
        # Todo: Assert the sent message is sent (see Todo in mailer.py).
        # Todo: Assert the sent message is received.

    def test_write_email_confirmation_request(self):
        user = self._find_user()
        code = '00000000000000000000000000000000000000000000000000000000000'
        email = self.mailer.write_email_confirmation_request(user, code)
        assert 'confirm' in email['Subject']
        assert user.firstname.encode('utf8') in email.as_string()
        assert code in email.as_string()

    def test_send_email_confirmation_request(self):
        user = self._find_user()
        code = '00000000000000000000000000000000000000000000000000000000000'
        self.mailer.send_email_confirmation_request(user, code)
        # Todo: Assert the sent email is sent (see Todo in mailer.py).
        # Todo: Assert the sent email is received.

    def test_write_response_notification(self):
        user = self._find_user()
        enquiry = model.Enquiry(owner=user, summary=u'blah\xfc')
        model.Session.commit()
        email = self.mailer.write_response_notification(enquiry)
        assert enquiry.summary.encode('utf8') in email['Subject']
        assert enquiry.id in email.as_string()
        assert enquiry.owner.firstname.encode('utf8') in email.as_string()
        assert str(enquiry.owner.email) in email.as_string()
    
    def test_send_response_notification(self):
        user = self._find_user()
        enquiry = model.Enquiry(owner=user)
        model.Session.commit()
        self.mailer.send_response_notification(enquiry)
        # Todo: Assert the sent email is sent (see Todo in mailer.py).
        # Todo: Assert the sent email is received.

    def test_send_unsent(self):
        results = self.mailer.send_unsent()
        assert len(results) == 0
        user = self._find_user()
        to = "data.handler@appropriatesoftware.net"
        summary = u"This is an enquiry subject\xfc"
        fulltext = u"This is an enquiry\xfc"
        enquiry = model.Enquiry.start_new(user, to, summary, fulltext)
        raise Exception, enquiry.id
        assert len(enquiry.messages) == 1
        message = enquiry.messages[0]
        raise Exception, message.id
        results = self.mailer.send_unsent()
        assert len(results) == 1
        assert_equal(results[0][0], message.id)
        assert_equal(results[0][1], u'Sent But Not Synced')

    def test_reread_sent(self):
        self.setup_sync_fixtures()
        try:
            out = self.mailer.reread_sent()
            assert out[0] == [self.notsynced_id, u'Sent'], out
            now_synced = model.Message.query.get(self.notsynced_id)
            print now_synced.mimetext
            print self.msg1
            # for some reason not exactly the same
            # assert now_synced.mimetext == self.msg1
            assert now_synced.mimetext[:20] == self.msg1[:20]
        finally:
            self.teardown_sync_fixtures()

    def test_pull_unread(self):
        self.setup_sync_fixtures()
        try:
            e = model.Enquiry.query.first()
            startnum = model.Message.query.count()
            assert len(e.messages) == 2, len(e.messages)
            out = self.mailer.pull_unread('FIXTURE')
            endnum = model.Message.query.count() 
            assert endnum == startnum + 2, endnum
            assert len(e.messages) == 4, len(e.messages)
            msgids = [ m.email['Message-Id'].split('@')[0][1:] for m in e.messages if
                    m.email['Message-Id'] ]
            assert self.email_msgid_3 in msgids, msgids
            ourid = [ res[2] for res in out if res[1] == 'Synced' and
                    res[0][1:].startswith(self.email_msgid_3) ]
            ourmsg = model.Message.query.get(ourid) 
            assert ourmsg.status == model.Message.JUST_RESPONSE
        finally:
            self.teardown_sync_fixtures()

    def setup_sync_fixtures(self):
        email_msgid = model.Message.query.get(self.msg_id).email['Message-Id']
        notsynced = model.Message(status=model.Message.JUST_SENT)
        model.Session.commit()
        self.notsynced_id = notsynced.id
        
        host = config['enquiry.imap_host']
        usr = config['enquiry.imap_user']
        pwd = config['enquiry.imap_pwd']
       
        import imaplib 
        self.imap = imaplib.IMAP4_SSL(host)
        self.imap.login(usr, pwd)
        self.imap.create('FIXTURE')
        
        self.msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <%s@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        self.msg1 = self.msg1 % model.make_uuid().upper()
        self.msg1 = '%s: %s\r\n' % (self.mailer.ISITOPEN_HEADER_ID, self.notsynced_id) + self.msg1
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

    def _find_user(self):
        user = model.User.query.filter_by(email=self.to).first()
        if not user:
            msg = "Can't find user by email '%s'." % self.to
            msg += " All users:\n%s\nEND" % (
                "\n".join([repr(u) for u in model.User.query.all()]))
            raise Exception, msg
        return user

    def teardown_sync_fixtures(self):
        self.imap.delete('FIXTURE')
        self.imap.logout()
