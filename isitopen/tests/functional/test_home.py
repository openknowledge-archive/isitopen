from isitopen.tests import *

class TestHomeController(TestController):

    def test_home_page(self):
        offset = url_for('home')
        res = self.app.get(offset)
        print str(res)
        assert 'Is It Open Data?' in res

    def test_404(self):
        offset = '/some_nonexistent_url/'
        res = self.app.get(offset, status=404)

