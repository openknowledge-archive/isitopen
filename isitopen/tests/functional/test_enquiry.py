from isitopen.tests import *

class TestHomeController(TestController):
    @classmethod
    def setup_class(self):
        self.enq_id, self.msg_id = Fixtures.create()
        self.message = model.Message.query.get(self.msg_id)

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

    def test_view(self):
        offset = url_for(controller='enquiry', action='view',
                id=self.enq_id)
        res = self.app.get(offset)
        print str(res)
        assert 'Is It Open Data?' in res
        assert 'Status:' in res

    def test_list(self):
        offset = url_for(controller='enquiry', action='list')
        res = self.app.get(offset)
        assert self.enq_id  in res

    def test_create(self):
        offset = url_for(controller='enquiry', action='create')
        res = self.app.get(offset)
        assert 'Create' in res
        to = 'xyz@journal.org'
        sender = 'enquirer@okfn.org'
        form = res.forms[0]
        form['to'] = to
        form['sender'] = sender
        res = form.submit('preview')
        assert 'Preview' in res
        res = form.submit('send')
        # 302 redirect
        res = res.follow()
        assert 'Sent' in res
        model.Session.remove()
        assert model.Enquiry.query.count() == 2
        assert model.Message.query.count() == 3

        # TODO: test bad entry (e.g. no to address)

