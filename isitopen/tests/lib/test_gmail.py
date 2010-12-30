import nose
from nose.tools import *

import imaplib
from isitopen.lib.gmail import IMAP
from email import message_from_string

# To run these tests successfully you will need to set the following parameters
# in your `test.ini`. I strongly recommend setting up a local IMAP4 server
# (for example, dovecot) as running the tests directly against Gmail is
# a) a bit slow and b) prone to failure if another developer tries to run
# against the same account:
#
#enquiry.imap_host = IMAP_HOST_NAME
#enquiry.imap_user = IMAP_USER_NAME
#enquiry.imap_pwd = IMAP_USER_PASS
#

class TestImapAccount:    
    
    def test_login(self):
        imap = IMAP()
        assert imap.logged_in
    
    @raises(imaplib.IMAP4.error)
    def test_login_fail(self):
        imap = IMAP(pwd='notthepassword')

class TestImapInterface:
    
    def setup(self, inbox_mailbox_name='FIXTURE', allmail_mailbox_name='allMail'):
        self.imap = IMAP()        
        self.imap.INBOX = inbox_mailbox_name
        self.imap.ALL_MAIL = allmail_mailbox_name
        
        msg1 = "Delivered-To: mockuser@gmail.com\r\nSender: Jane Doe <jane.doe@example.com>\r\nMessage-Id: <6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>\r\nFrom: Jane Doe <jane.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 1 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 1\r\n"
        msg2 = "Delivered-To: mockuser@gmail.com\r\nSender: John Doe <john.doe@example.com>\r\nMessage-Id: <83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>\r\nFrom: John Doe <john.doe@example.com>\r\nTo: 'Mock User' <mockuser@gmail.com>\r\nContent-Type: text/plain;\r\n\tcharset=us-ascii;\r\n\tformat=flowed\r\nContent-Transfer-Encoding: 7bit\r\nX-Mailer: A Mail Client v1.0\r\nMime-Version: 1.0\r\nSubject: Message 2 subject line\r\nDate: Thu, 19 Mar 2009 10:58:21 +0000\r\n\r\nThe body of message 2\r\n"

        self.structure = {
            allmail_mailbox_name: [ (msg1, '()'), (msg2, '(\Seen)') ],
            'thread': {
                '1234': [ (msg1, '()'), (msg2, '(\Seen)') ],
                '2345': [],
                '3456': [],
                '4567': []
            }
        }

        def structure_create(imap, struct, path=''):
            for f in struct:
                imap.conn.create(path + f)
                if isinstance(struct[f], dict):
                    structure_create(imap, struct[f], f + imap.delim)
                elif isinstance(struct[f], list):
                    for msg, flags in struct[f]:
                        stat, data = imap.conn.append(path + f, flags, None, msg)
        structure_create(self.imap, self.structure)
        
    def teardown(self):
        def structure_destroy(imap, struct, path=''):
            for f in struct:
                imap.conn.create(path + f)
                if isinstance(struct[f], dict):
                    imap.conn.delete(path + f);
                    structure_destroy(imap, struct[f], f + imap.delim)
                else:
                    imap.conn.delete(path + f);
        structure_destroy(self.imap, self.structure)
        self.imap = None
    
    def test_get_mailbox_ids(self):
        # Check normal list.
        mailbox_ids = self.imap.get_mailbox_ids('thread/1234')
        assert_equal(len(mailbox_ids), 2)
        # Check all list.
        all_mailbox_ids = self.imap.get_mailbox_ids('thread/1234', 'ALL')
        assert_equal(len(all_mailbox_ids), 2)
        # Check normal list equals all list.
        assert_equal(mailbox_ids, all_mailbox_ids)
        # Check seen list.
        seen_mailbox_ids = self.imap.get_mailbox_ids('thread/1234', 'SEEN')
        assert_equal(len(seen_mailbox_ids), 1)
        # Check unseen list.
        unseen_mailbox_ids = self.imap.get_mailbox_ids('thread/1234', 'UNSEEN')
        assert_equal(len(unseen_mailbox_ids), 1)
        # Check seen list not equal to unseen list.
        assert seen_mailbox_ids != unseen_mailbox_ids
        # Check unread list.
        unread_mailbox_ids = self.imap.get_unread_mailbox_ids('thread/1234')
        assert_equal(len(unread_mailbox_ids), 1)
        # Check unseen list equals unread list.
        assert_equal(unseen_mailbox_ids, unread_mailbox_ids)

    def test_get_mailbox_message(self):
        mailbox_ids = self.imap.get_mailbox_ids('thread/1234')
        # Check messages (with newest message at the start of list).
        mailbox_message = self.imap.get_mailbox_message(mailbox_ids[0])
        email_message = message_from_string(mailbox_message)
        assert_equal(email_message['Subject'], "Message 2 subject line")
        assert_equal(email_message['Message-ID'], "<83D15878-C804-428D-9D2B-28416DA22F5C@gmail.com>")
        assert email_message.get_payload().startswith("The body of message 2") 
        mailbox_message = self.imap.get_mailbox_message(mailbox_ids[1])
        email_message = message_from_string(mailbox_message)
        assert_equal(email_message['Subject'], "Message 1 subject line")
        assert_equal(email_message['Message-ID'], "<6AE15752-B604-712D-8A42-13782DBC2FF9@gmail.com>")
        assert email_message.get_payload().startswith("The body of message 1")

    def test_mark_read(self):
        unread_mailbox_ids = self.imap.get_unread_mailbox_ids('thread/1234')
        assert_equal(len(unread_mailbox_ids), 1)
        self.imap.mark_read(unread_mailbox_ids[0])
        unread_mailbox_ids = self.imap.get_unread_mailbox_ids('thread/1234')
        assert_equal(len(unread_mailbox_ids), 0)
 
