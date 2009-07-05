from isitopen.tests import *

class TestMessageController(TestController):
    @classmethod
    def setup_class(self):
        self.enq_id, self.msg_id = Fixtures.create()
        self.message = model.Message.query.get(self.msg_id)

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_index(self):
        res = self.app.get(url_for(controller='message', action='index'))
        assert 'Message - Index' in res

    def test_create(self):
        # this is tested in test_enquiry.py
        pass

