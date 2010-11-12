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
    
    db create # create db (upgrade to latest version)
    db upgrade version # upgrade to version
    db clean
    db rebuild # clean + create
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = 1
    migrate_repository = 'isitopen/migration/'

    def command(self):
        self._load_config()
        from isitopen import model

        cmd = self.args[0]
        if cmd == 'create':
            model.repo.create_db()
        elif cmd == 'clean':
            model.repo.clean_db()
        elif cmd == 'rebuild':
            model.repo.rebuild_db()
        elif cmd == 'upgrade':
            version = self.args[1] if len(self.args) >= 2 else None 
            model.repo.upgrade_db(version)

        else:
            print 'Command %s not recognized' % cmd


class Fixtures(Command):
    '''Create some fixture data.
    
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = None
    min_args = 0

    summary = u'Our first enquiry'
    user_email = u'testing@isitopen.ckan.net'
    to = u'testing@enquiries.isitopen.ckan.net'
    sender = u'me@iwantopendata.org'
    body = 'a body'
    email = E.message_from_string(body)
    email2 = E.message_from_string(u'A second message')

    def command(self):
        self._load_config()
        self.create()
        print 'Created fixtures'

    @classmethod
    def create(self):
        from isitopen import model
        # Warning: The emails and passwords are used as login credentials in the customer tests.
        self.create_user(u'Mark\xfc',u'Smith\xfc',u'mark.smith@appropriatesoftware.net',u'mark\xfc',True)
        self.create_user(u'Robert\xfc',u'Smith\xfc',u'bob.smith@appropriatesoftware.net',u'bob\xfc')
        user = self.create_user(u'IsItOpen\xfc',u'Tester\xfc',self.user_email,u'pass\xfc',True)
        enq = model.Enquiry(owner=user, summary=self.summary)
        enq.extras = { 'ckan-package' :  u'xyz' } 
        self.email['To'] = self.to
        self.email['Subject'] = u'testing email'
        self.email['Message-Id'] = '<%s@gmail.com>' % model.make_uuid()
        mess = model.Message(enquiry=enq)
        mess.sender = self.sender
        mess.mimetext = self.email.as_string().decode('utf8')
        mess.status = model.Message.SENT_REREAD

        self.email2['To'] = self.user_email
        self.email2['Subject'] = u'testing email response'
        self.email2['From'] = self.to
        mess2 = model.Message(enquiry=enq, mimetext=self.email2.as_string().decode('utf8'),
                status=model.Message.JUST_RESPONSE)

        model.Session.commit()
        enq_id = enq.id
        mess_id = mess.id
        model.Session.remove()
        return (enq_id, mess_id)

    @classmethod
    def create_user(self, firstname, lastname, email, password, is_confirmed=False):
        from isitopen import model
        user = model.User(firstname=firstname, lastname=lastname, email=email, password=password, is_confirmed=is_confirmed)
        model.Session.commit()
        return user

    @classmethod
    def remove(self):
        from isitopen import model
        model.repo.rebuild_db()

