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
        assert message['Subject'].decode('utf8') == self.subject
        assert self.body in message.as_string().decode('utf8')

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
        body = u"This is an enquiry\xfc"
        email_message = self.mailer.write(body, to=to, subject=summary)
        enquiry = model.Enquiry.start_new(user, summary, email_message)
        assert len(enquiry.messages) == 1
        message = enquiry.messages[0]
        results = self.mailer.send_unsent()
        assert len(results) == 1
        assert_equal(results[0][0], message.id)
        assert_equal(results[0][1], u'Sent But Not Synced')

    def test_reread_sent(self):
        self.setup_sync_fixtures()
        try:
            results = self.mailer.reread_sent()
            result = results[0]
            message_id = result[0]
            message_status = result[1]
            assert message_id == self.justsent_id, (message_id, self.justsent_id)
            assert message_status == model.Message.SENT_REREAD, (message_status, model.Message.SENT_REREAD)
            message = model.Message.query.get(self.justsent_id)
            print "Original mimetext fixture:\n %s" % repr(self.msg1)
            print "Reread message mimetext:\n %s" % repr(message.mimetext)
            assert message.mimetext == self.msg1, (message.mimetext, self.msg1)
            #assert message.mimetext[:20] == self.msg1[:20]
        finally:
            self.teardown_sync_fixtures()

    def test_pull_unread(self):
        # Set up test fixtures.
        self.setup_sync_fixtures()
        try:
            enquiry = model.Enquiry.query.first()
            # Check the fixtures.
            assert len(enquiry.messages) == 2, len(enquiry.messages)
            message_count = model.Message.query.count()
            assert message_count == 3
            # Read unread email test fixtures.
            results = self.mailer.pull_unread('FIXTURE')
            print "Pulled unread: %s" % results
            # Read results reported by mailer.
            result_smtp_ids = []
            message_ids = []
            for result in results:
                result_smtp_id = result[0].split('@')[0][1:] # <(SMTPID)@google.com>
                result_smtp_ids.append(result_smtp_id)
                result_status = result[1]
                if result_status == model.Message.JUST_RESPONSE:
                    message_id = result[2]
                    message_ids.append(message_id)
            # Check mailer reported seeing email fixtures.
            assert len(result_smtp_ids) == 2, (result_smtp_ids, results)
            assert len(message_ids) == 2, (message_ids, results)
            assert self.email_msgid_3 in result_smtp_ids, (self.email_msgid_3, result_smtp_ids)
            # Check mailer created reported messages.
            for message_id in message_ids:
                message = model.Message.query.get(message_id)
                assert message, "No message for message_id: %s" % message_id
                assert message.status == model.Message.JUST_RESPONSE
                assert message.enquiry == enquiry
            # Check mailer created messages from email fixtures.
            smtp_ids = []
            for message in enquiry.messages:
                if message.email['Message-Id']:
                    smtp_id = message.email['Message-Id'].split('@')[0][1:] # <(SMTPID)@google.com>
                    smtp_ids.append(smtp_id)
            assert self.email_msgid_3 in smtp_ids, smtp_ids
            # Check mailer didn't create any other messages.
            assert len(enquiry.messages) == 4, len(enquiry.messages)
            message_count = model.Message.query.count()
            assert message_count == 5
        finally:
            self.teardown_sync_fixtures()

    def setup_sync_fixtures(self):
        email_msgid = model.Message.query.get(self.msg_id).email['Message-Id']
        justsent = model.Message(status=model.Message.JUST_SENT)
        model.Session.commit()
        self.justsent_id = justsent.id
        
        host = config['enquiry.imap_host']
        usr = config['enquiry.imap_user']
        pwd = config['enquiry.imap_pwd']
       
        import imaplib 
        self.imap = imaplib.IMAP4_SSL(host)
        self.imap.login(usr, pwd)
        self.imap.create('FIXTURE')
       
        # Todo: Change these fixtures, don't need \r\n to new line headers (only the payload). 
        #self.msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <%s@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        self.msg1 = "Delivered-To: mockuser@gmail.com\nSender: Jane Doe <jane.doe@example.com>\nMessage-Id: <%s@gmail.com>\nFrom: Jane Doe <jane.doe@example.com>\nTo: 'Mock User' <mockuser@gmail.com>\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\nContent-Transfer-Encoding: 7bit\nX-Mailer: A Mail Client v1.0\nMime-Version: 1.0\nSubject: Message 1 subject line\nDate: Thu, 19 Mar 2009 10:58:21 +0000\n\nThe body of message 1\r\n"
        self.msg1 = self.msg1 % model.make_uuid().upper()
        self.msg1 = '%s: %s\n' % (self.mailer.ISITOPEN_HEADER_ID, self.justsent_id) + self.msg1
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
