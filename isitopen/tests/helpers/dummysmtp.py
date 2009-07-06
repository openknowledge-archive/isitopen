import smtpd, os, time, asyncore

class DummySMTP(smtpd.DebuggingServer):
    def __init__(self, port, pipe):
        smtpd.SMTPServer.__init__(self, ('', port), None)
        self.pipe = pipe
        self.pipe.send("UP")
        print 'DummySMTP listening on port ' + str(port) + '.'
    
    def process_message(self, *args, **kwargs):
        smtpd.DebuggingServer.process_message(self, *args, **kwargs)
        self.pipe.send( (args, kwargs) )

def loop(pipe):
    x = DummySMTP(8025, pipe)
    try:
        asyncore.loop(timeout=2)
    except KeyboardInterrupt:
        print 'Shutting down.'
    x.close()

if __name__=='__main__':
    loop()