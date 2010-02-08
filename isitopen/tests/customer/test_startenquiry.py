from isitopen.tests.customer.base import *

class TestBrowseDataOpennessEnquiries(TestController):
    """
    Check enquiry has not been made
    """
    def test_196(self):
        """
        The system shall present to all users a list of existing data openness enquiries.
        """
        res = self.get(controller="enquiry", action="list")
        self.assert_checkpoint('indicator-for-enquiry-list', res)
        assert self.enq_id in res


class TestStartDataOpennessEnquiry(TestController):
    """
    Start data openness enquiry
    """
    def test_162(self):
        """
        The system shall present to all users a form for starting data openness enquiries.
        """
        self.logout()
        res = self.get_form_for_start_enquiry()
        self.assert_form_for_start_enquiry(res)
        self.login()
        res = self.get_form_for_start_enquiry()
        self.assert_form_for_start_enquiry(res)

    def test_163(self):
        """
        The system shall accept submissions from authenticated owners of activated accounts using the data openness enquiry form by presenting the enquiry summary and prompting for confirmation.
        """
        res = self.login()
        self.assert_account_is_activated(res)
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_confirm_enquiry(res)

    def test_164(self):
        """
        The system shall accept submissions from unauthenticated users of the data openness enquiry form by creating an anonymous pending enquiry action, and by redirecting the user to login form, passing a reference to the pending action.
        """
        self.logout()
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_login(res)
        self.assert_reference_to_pending_action(res)

    def test_176(self):
        """
        The system shall accept (and action pending account activation) submissions from authenticated owners of unactivated accounts using the form for starting data openness enquiries by directing the user to activate their account.
        """
        res = self.login(credentials=self.other_credentials)
        self.assert_account_not_activated(res)
        res = self.get_form_for_start_enquiry()
        self.assert_form_for_confirm_email(res)

    def test_182(self):
        """
        The system shall accept from authenticated owners of activated accounts confirmation of the summary of enquiry regarding data openness by creating a pending message to a data handler with the enquiry and indicating to the user that this has happened.
        """
        res = self.login()
        self.assert_account_is_activated(res)
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_confirm_enquiry(res)
        res = self.submit_form_for_confirm_enquiry(res)
        # Assert confirmation has been received.
        self.assert_indicator_for_confirmed_enquiry(res)
        # Assert message created properly.
        login = self.admin_credentials['login']
        message = model.Message.query.filter_by(sender=login).first()
        assert message, str(model.Message.query.all())
        print message.mimetext
        assert self.enquiry_data['to'] == message.to
        assert self.enquiry_data['subject'] == message.subject
        assert self.enquiry_data['body'] in message.mimetext
        assert 'Sent by' in message.mimetext
        assert self.enquiry_data['subject'] == message.enquiry.summary
        assert login == message.enquiry.owner.email

