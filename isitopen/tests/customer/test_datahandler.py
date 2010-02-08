from isitopen.tests.customer.base import *

class TestDispatchDataOpennessEnquiry(TestController):
    """
    Send enquiry regarding data openness to data handler.
    """

    def test_165(self):
        """
        The system shall regularly send pending data openness enquiry messages through a secure email account.
        """ 
        res = self.login()
        self.assert_account_is_activated(res)
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_confirm_enquiry(res)
        res = self.submit_form_for_confirm_enquiry(res)
        self.assert_indicator_for_confirmed_enquiry(res)
        self.get(controller="enquiry", action="flush")
        # Todo: Check the email is received.


