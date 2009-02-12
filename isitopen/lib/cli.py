import os

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

    to = u'testing@enquiries.com'

    def command(self):
        self._load_config()
        self.create()

    @classmethod
    def create(self):
        from isitopen import model
        subj = u'testing email'
        enq = model.Enquiry(
                to=self.to,
                subject=subj)
        model.Session.commit()
        model.Session.clear()

    @classmethod
    def remove(self):
        from isitopen import model
        for enq in model.Enquiry.query.filter_by(to=self.to).all():
            model.Session.delete(enq)
            model.Session.commit()
            model.Session.remove()

