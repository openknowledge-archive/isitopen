from isitopen.tests.customer.base import *

class TestDispatchDataOpennessEnquiry(TestController):
    """
    Send enquiry regarding data openness to data handler.
    """

    def test_165(self):
        """
        The system shall regularly send pending data openness enquiry messages through a secure email account.
        """
        res = self.login()
        msg_ids1 = set([m.id for m in model.Message.query.all()])
        self.assert_account_is_activated(res)
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_confirm_enquiry(res)
        res = self.submit_form_for_confirm_enquiry(res)
        self.assert_indicator_for_confirmed_enquiry(res)
        # Check message was generated.
        msg_ids2 = set([m.id for m in model.Message.query.all()])
        res = self.get(controller="message", action="send_unsent")
        self.assert_checkpoint('send-unsent', res)
        assert len(msg_ids2 - msg_ids1) == 1
        # Check message was sent.
        msg_id = (msg_ids2 - msg_ids1).pop()
        msg_status = model.Message.JUST_SENT
        msg_checkstring = "[u'%s', u'%s']" % (msg_id, msg_status)
        assert msg_checkstring in res
        # Check message was reread.
        msg_status = model.Message.SENT_REREAD
        msg_checkstring = "[u'%s', u'%s']" % (msg_id, msg_status)
        assert msg_checkstring in res
        #raise Exception, str(res)
        # Todo: Check the Sent Items via IMAP.
        # Todo: Check the email is received.

    def test_185(self):
        """
        The system shall notify enquiry owner when pending enquiry messages are sent.
        """
        # This is implemented as a Bcc in the Mailer.send_unsent() method.
        # Todo: Figure out a way to test this.
        pass


class TestReceiveEnquiryResponse(TestController):
    """
    Receive data openness enquiry response.
    """
    def test_191(self):
        """
        The system shall regularly receive new data openness enquiry messages from a secure email account.
        """
        # Todo: Create our own unread messages (see Gmail setup).
        # Todo:  - 1 well formed data handler response.
        # Todo:  - 1 bounce reported by google-daemon.
        # Todo:  - 1 spam message.
        from isitopen.tests.lib.test_gmail import TestImapInterface
        testCase = TestImapInterface()
        INBOX = 'INBOX'
        ALL_MAIL = '[Google Mail]/All Mail'
        testCase.setup(inbox_mailbox_name=INBOX, allmail_mailbox_name=INBOX)
        unseen_mailbox_ids = testCase.imap.get_mailbox_ids(mailbox_name=INBOX, condition='UNSEEN')
        assert_equal(len(unseen_mailbox_ids), 1)
        mailbox_id = unseen_mailbox_ids[0]
        mailbox_message = testCase.imap.get_mailbox_message(mailbox_id)
        from email import message_from_string
        email_message = message_from_string(mailbox_message)
        smtp_id = email_message['Message-Id']
        msg_status = 'Skip: found no related enquiry'
        msg_checkstring = "['%s', '%s']" % (smtp_id, msg_status)
        try:
            self.login()
            res = self.get(controller="message", action="receive_unread")
            self.assert_checkpoint('receive_unread', res)
            if msg_checkstring not in res:
                raise Exception('Msg check %s not found in response:\n\n%s.\n\n' % (msg_checkstring, res))
        finally:
            testCase.teardown()

