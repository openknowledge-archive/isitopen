from isitopen.tests import *

import isitopen.model as model

class TestModel(object):
    @classmethod
    def setup_class(self):
        Fixtures.create()

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_basics(self):
        # by using the same 'to' value ensure it is removed in teardown
        to = Fixtures.to
        subj = u'testing email'
        enq = model.Enquiry(
                to=to,
                subject=subj)
        model.Session.commit()
        id = enq.id
        model.Session.clear()
        out = model.Enquiry.query.get(id)
        assert out.subject == subj
        assert out.to == to
        assert out.status == model.EnquiryStatus.not_yet_sent

