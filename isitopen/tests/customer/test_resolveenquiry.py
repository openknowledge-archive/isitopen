from isitopen.tests.customer.base import *

class TestResolveEnquiry(TestController):
    """
    Resolve data openness enquiry.
    """
    
    def assert_requirement_186(self, resolution):
        """
        The system shall present to data openness enquiry owner options to resolve the enquiry with resolution of open, not open, or not known.
        """
        self.logout()
        res = self.get(controller="enquiry", action="view", id=self.enq_id)
        self.fail_if_checkpoint('form-for-resolve-enquiry', res)
        self.login()
        res = self.get(controller="enquiry", action="view", id=self.enq_id)
        self.assert_checkpoint('form-for-resolve-enquiry', res)
        assert self.enq_id in res
        # Actually resolve the enquiry (submission not specified in requirements).
        form = res.forms[0]
        resolution_data = {'resolution': resolution}
        res = self.submit(form_data=resolution_data, form=form)
        assert resolution in res, (resolution, res)
        enquiry = model.Enquiry.query.get(self.enq_id)
        assert enquiry.status == resolution, (enquiry.status, resolution)

    def test_186_open(self):
        self.assert_requirement_186(model.Enquiry.RESOLVED_OPEN)

    def test_186_closed(self):
        self.assert_requirement_186(model.Enquiry.RESOLVED_CLOSED)

    def test_186_not_known(self):
        self.assert_requirement_186(model.Enquiry.RESOLVED_NOT_KNOWN)

