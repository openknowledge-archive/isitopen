
import email as E

from isitopen.tests import *

import isitopen.model as model
import isitopen.lib.finder

class TestFinder:
    finder = isitopen.lib.finder.Finder()

    @classmethod
    def setup_class(self):
        self.enq_id, msgid= Fixtures.create()
        msg = model.Message.query.get(msgid)
        self.response = E.message_from_string(u'a body')
        self.response2 = E.message_from_string(u'a body')
        self.response['In-Reply-To'] = msg.email['Message-Id']
        self.response2['References'] = msg.email['Message-Id']

    @classmethod
    def teardown_class(self):
        Fixtures.remove()
    
    def test_extract_id_from_subject(self):
        subject = '[iio-1] fajdaf'
        out = self.finder.extract_id_from_subject(subject)
        assert out == 1, out

        subject = 'afdfdaf [iio-3318] fajdaf'
        out = self.finder.extract_id_from_subject(subject)
        assert out == 3318, out
    
    def test_enquiry_for_message(self):
        out = self.finder.enquiry_for_message(self.response)
        assert out.id == self.enq_id

    def test_enquiry_for_message_references(self):
        out = self.finder.enquiry_for_message(self.response2)
        assert out.id == self.enq_id

