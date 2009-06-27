from meta import *
from enquiry import *
from user import *

class Repository(object):
    def __init__(self, ourmetadata, oursession):
        self.metadata = ourmetadata
        self.session = oursession

    def create_db(self):
        self.metadata.create_all(bind=self.metadata.bind)    

    def clean_db(self):
        self.metadata.drop_all(bind=self.metadata.bind)

    def rebuild_db(self):
        self.clean_db()
        self.create_db()

repo = Repository(metadata, Session)

