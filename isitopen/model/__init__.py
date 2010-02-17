from meta import *
from enquiry import *


import isitopen.migration
class Repository(object):
    migrate_repository = isitopen.migration.__path__[0]

    def __init__(self, ourmetadata, oursession):
        self.metadata = ourmetadata
        self.session = oursession

    def create_db(self):
        self.metadata.create_all(bind=self.metadata.bind)    
        self.setup_migration_version_control(self.latest_migration_version())
        # creation this way worked fine for normal use but failed on test with
        # OperationalError: (OperationalError) no such table: user 
        # self.upgrade_db()

    def clean_db(self):
        self.metadata.drop_all(bind=self.metadata.bind)

    def latest_migration_version(self):
        import migrate.versioning.api as mig
        version = mig.version(self.migrate_repository)
        return version

    def setup_migration_version_control(self, version=None):
        import migrate.versioning.exceptions
        import migrate.versioning.api as mig
        # set up db version control (if not already)
        try:
            mig.version_control(self.metadata.bind.url,
                    self.migrate_repository, version)
        except migrate.versioning.exceptions.DatabaseAlreadyControlledError:
            pass

    def upgrade_db(self, version=None):
        '''Upgrade db using sqlalchemy migrations.

        @param version: version to upgrade to (if None upgrade to latest)
        '''
        import migrate.versioning.api as mig
        self.setup_migration_version_control()
        mig.upgrade(self.metadata.bind.url, self.migrate_repository,
                version=version)

    def rebuild_db(self):
        self.clean_db()
        self.create_db()

repo = Repository(metadata, Session)

