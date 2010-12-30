from isitopen.tests import *
import isitopen.forms as forms
import isitopen.model as model

class TestForms:
    @classmethod
    def setup_class(self):
        self.enq_id, self.msg_id = Fixtures.create()

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_message(self):
        # only standard fields
        msg = model.Message.query.get(self.msg_id)
        ourf = forms.Message.bind(msg)
        out = ourf.render()
        assert out, out

    def test_enquiry(self):
        # JsonType in fields extras ...
        enq = model.Enquiry.query.get(self.enq_id)
        fenq = forms.Enquiry.bind(enq)
        out = fenq.render()
        assert out, out

