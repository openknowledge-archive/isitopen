from isitopen.tests import *

class TestHomeController(TestController):
    @classmethod
    def setup_class(self):
        Fixtures.create()
        self.enquiry = model.Message.query.filter_by(to=Fixtures.to).first()

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_view(self):
        offset = url_for(controller='enquiry', action='view',
                id=self.enquiry.id)
        res = self.app.get(offset)
        print str(res)
        assert 'Is It Open Data?' in res
        assert 'Status:' in res

