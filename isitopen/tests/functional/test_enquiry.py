from isitopen.tests import *
import isitopen.controllers.message as MSG

class TestEnquiryController(TestController):
    def setup(self):
        self.enq_id, self.msg_id = Fixtures.create()
        self.message = model.Message.query.get(self.msg_id)

    def teardown(self):
        # should rebuild as create stuff
        model.repo.rebuild_db()

    def test_1_view(self):
        offset = url_for(controller='enquiry', action='view',
                id=self.enq_id)
        res = self.app.get(offset)
        assert 'Is It Open Data?' in res, str(res)
        assert 'Status:' in res, str(res)

    def test_2_list(self):
        offset = url_for(controller='enquiry', action='list')
        res = self.app.get(offset)
        assert self.enq_id  in res

    def test_4_write_response(self):
        offset = url_for(controller='enquiry', action='view',
                id=self.enq_id)
        res = self.app.get(offset)
        res = res.click('Write a response')
        assert 'Specify Your Enquiry' in res, res

        form = res.forms[0]
        newbody = 'Response to an enquiry'
        newsubject = 'Re: testing email response'
        print form['to'].value
        assert form['to'].value == Fixtures.to, form['to'].value
        assert form['subject'].value == newsubject, form['subject'].value
        form['body'] = newbody
        res = form.submit('send')

        res = res.follow()
        assert 'Enquiry - Sent' in res
        model.Session.remove()
        enqnum = model.Enquiry.query.count()
        assert enqnum == 1, enqnum
        assert model.Message.query.count() == 3
        enq = model.Enquiry.query.get(self.enq_id)
        msg = enq.messages[-1]
        print msg.mimetext
        assert msg.to == Fixtures.to
        assert newbody in msg.body
        assert MSG.enquiry_footer in msg.mimetext
        assert msg.subject == newsubject

