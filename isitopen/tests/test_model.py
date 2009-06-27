import email as E

from isitopen.tests import *

import isitopen.model as model

class TestModel(object):
    @classmethod
    def setup_class(self):
        self.enq_id, self.mess_id = Fixtures.create()

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_fixtures(self):
        mess = model.Message.query.get(self.mess_id)
        enq = model.Enquiry.query.get(self.enq_id)
        assert mess.enquiry.id == self.enq_id
        tmp = E.message_from_string(mess.mimetext)
        subj = mess.email['Subject']
        assert subj == u'testing email', subj

        assert enq.owner.email == Fixtures.user_email

