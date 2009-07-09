import nose
from nose.tools import *

import smtplib
from isitopen.lib.mailer import Mailer
from email.mime.text import MIMEText

import time

class _TestMailerLogin:
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
        self.m = Mailer.default()
        self.example = MIMEText("Just some message.\n\nRegards,\nBloke")
        self.example['To'] = 'sender@example.com'
        self.example['Bcc'] = 'boo@aaargh.com'
        self.example['From'] = 'user@example.org'
    
    def test_send(self):
        self.m.send(self.example)
        res = self.pipe.recv()
        assert_equal( res[0][1], 'user@example.org')
        assert_equal( res[0][2].sort(), ['boo@aargh.com', 'sender@example.com'].sort())

if __name__ == '__main__':
    nose.main()
