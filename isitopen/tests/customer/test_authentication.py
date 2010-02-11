from isitopen.tests.customer.base import *

class TestLoginToApplicationService(TestController):
    """
    Login to application service.
    """

    def test_178(self):
        """
        The system shall present to unauthenticated users a login form for submitting account credentials.
        """
        self.logout()
        res = self.get(controller='account', action='login')
        self.assert_not_logged_in(res)
        self.assert_form_for_login(res)

    def test_175(self):
        """
        The system shall accept login form submission from an unauthenticated user offering good credentials by signing in the user and resuming any referenced pending action.
        """
        self.logout()
        res = self.submit_form_for_start_enquiry() # Start example action.
        self.assert_form_for_login(res)
        self.assert_not_logged_in(res)
        res = self.submit(form_data=self.admin_credentials, res=res, controller="account", action="login")
        self.assert_is_logged_in(res)
        self.assert_form_for_confirm_enquiry(res) # Resume action above.

    def test_181(self):
        """
        The system shall resume an enquiry regarding data openness by redirecting the user to the enquiry confirmation page (as if the enquiry had just been made).
        """
        self.logout()
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_login(res)
        self.assert_not_logged_in(res)
        res = self.submit(form_data=self.admin_credentials, res=res, controller="account", action="login")
        self.assert_is_logged_in(res)
        self.assert_form_for_confirm_enquiry(res)
        # Check we've got our enquiry back.
        for value in self.enquiry_data.values():
            assert value in res, "Value '%s' not in response: %s" % (
                value, res
            )

    def test_169(self):
        """
        The system shall present near any login form options both to register new user account details and to recover old user account details, passing on any reference to a pending action.
        """
        self.logout()
        res = self.get(controller='account', action='login')
        self.assert_not_logged_in(res)
        self.assert_checkpoint('option-to-register-account-details', res)
        # Todo: Test the link works.
        self.assert_checkpoint('option-to-recover-account-details', res)
        # Todo: Test the link works.

    def test_173(self):
        """
        The system shall set on any login form hidden form values for any passed reference to a pending action.
        """
        self.logout()
        res = self.get(controller='account', action='login', code='1')
        self.assert_reference_to_pending_action(res)
