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

    # most of this is tested in test_enquiry.py
    def _test_create(self):
        # TODO: test bad entry (e.g. no to address)
        pass

    def test_bad_entry(self):
        pass

    def test__make_email(self):
        import isitopen.controllers.message as MSG
        out = MSG._make_email('xyx', to='me@me.com')
        assert out['To'] == 'me@me.com'
        assert 'xyx' in out.as_string()


