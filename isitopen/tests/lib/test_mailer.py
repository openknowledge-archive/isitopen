import nose
from nose.tools import *

import smtplib
from isitopen.lib.mailer import Mailer

class TestMailerLogin:
    def test_me(self):
        assert False, "Write some tests, dammit!"

class MockGmailSMTP(object):
    # Make me as messy as you like. It really doesn't matter.
    """A mockup of an instance of `smtplib.SMTP` or similar."""

if __name__ == '__main__':
    nose.main()