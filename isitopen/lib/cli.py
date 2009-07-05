import os
import email as E

import paste.script

class Command(paste.script.command.Command):
    parser = paste.script.command.Command.standard_parser(verbose=True)
    parser.add_option('-c', '--config', dest='config',
            default='development.ini', help='Config file to use.')
    parser.add_option('-f', '--file',
        action='store',
        dest='file_path',
        help="File to dump results to (if needed)")
    default_verbosity = 1
    group_name = 'isitopen'

    def _load_config(self):
        from paste.deploy import appconfig
        from isitopen.config.environment import load_environment
        if not self.options.config:
            msg = 'No config file supplied'
            raise self.BadCommand(msg)
        self.filename = os.path.abspath(self.options.config)
        conf = appconfig('config:' + self.filename)
        load_environment(conf.global_conf, conf.local_conf)

    def _setup_app(self):
        cmd = paste.script.appinstall.SetupCommand('setup-app') 
        cmd.run([self.filename]) 


class ManageDb(Command):
    '''Perform various tasks on the database.
    
    db create # create tables
    db clean
    db rebuild # clean + create
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = 1

    def command(self):
        self._load_config()
        from isitopen import model

        cmd = self.args[0]
        if cmd == 'create':
            model.repo.create_db()
        elif cmd == 'clean':
            model.repo.clean_db()
        elif cmd == 'rebuild':
            model.repo.clean_db()
            model.repo.create_db()
        else:
            print 'Command %s not recognized' % cmd

class Fixtures(Command):
    '''Create some fixture data.
    
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = 0

    user_email = u'testing@isitopen.org'
    to = u'testing@enquiries.com'
    sender = u'me@iwantopendata.org'
    email = E.message_from_string(u'')
    email2 = E.message_from_string(u'A second message')

    def command(self):
        self._load_config()
        self.create()
        print 'Created fixtures'

    @classmethod
    def create(self):
        from isitopen import model
        user = model.User(email=self.user_email)
        enq = model.Enquiry(owner=user)
        self.email['To'] = self.to
        self.email['Subject'] = u'testing email'
        mess = model.Message(enquiry=enq)
        mess.sender = self.sender
        mess.mimetext = self.email.as_string()

        self.email2['To'] = self.user_email
        self.email2['Subject'] = u'testing email response'
        mess2 = model.Message(enquiry=enq, mimetext=self.email2.as_string())
        model.Session.commit()
        enq_id = enq.id
        mess_id = mess.id
        model.Session.remove()
        return (enq_id, mess_id)

    @classmethod
    def remove(self):
        from isitopen import model
        model.repo.rebuild_db()

