from isitopen.tests import *

from isitopen.lib.mailer import Mailer

class TestMailer(object):

    to = 'mark.smith@appropriatesoftware.net'
    subject = u'Some message subject\xfc'
    body = u'Some message body\xfc'

    @classmethod
    def setup_class(self):
        Fixtures.create()
        self.mailer = Mailer()

    @classmethod
    def teardown_class(self):
        self.mailer.quit()
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

    def _find_user(self):
        user = model.User.query.filter_by(email=self.to).first()
        if not user:
            msg = "Can't find user by email '%s'." % self.to
            msg += " All users:\n%s\nEND" % (
                "\n".join([repr(u) for u in model.User.query.all()]))
            raise Exception, msg
        return user

# Old "dummy" tests below:

#import nose
#from nose.tools import *
#
#import smtplib
#from isitopen.lib.mailer import Mailer
#from email.mime.text import MIMEText
#
#import time
#
#class _TestMailerLogin:
#    @classmethod
#    def setup_class(self):
#        import isitopen.tests.helpers.dummysmtp as dsmtp
#        from processing import Process, Pipe
#        
#        self.pipe, pipe_remote = Pipe()
#        
#        self.p = Process(target=dsmtp.loop, args=(pipe_remote,))
#        self.p.start()
#        
#        ready = False
#        
#        while not ready:
#            try:
#                ready = self.pipe.recv()
#            except EOFError:
#                time.sleep(0.1)
#    
#    @classmethod
#    def teardown_class(self):
#        self.p.terminate()
#        
#    def setup(self):
#        self.m = Mailer()
#        self.example = MIMEText("Just some message.\n\nRegards,\nBloke")
#        self.example['To'] = 'sender@example.com'
#        self.example['Bcc'] = 'boo@aaargh.com'
#        self.example['From'] = 'user@example.org'
#    
#    def test_send(self):
#        self.m.send(self.example)
#        res = self.pipe.recv()
#        assert_equal( res[0][1], 'user@example.org')
#        assert_equal( res[0][2].sort(), ['boo@aargh.com', 'sender@example.com'].sort())
#
#if __name__ == '__main__':
#    nose.main()
