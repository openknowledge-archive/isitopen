from isitopen.tests.customer.base import *

class TestRegisterNewUserAccount(TestController):
    """
    Register new user account.
    """

    def test_170(self):
        """
        The system shall present to unauthenticated users a registration form, for registering new user accounts.
        """
        self.logout()
        res = self.get(controller='account', action='register')
        self.assert_form_for_register_account_details(res)

    def test_174(self):
        """
        The system shall set on the registration form a hidden value for any passed reference to a pending action.
        """
        self.logout()
        res = self.get(controller='account', action='register', code='1')
        self.assert_reference_to_pending_action(res)

    def test_171(self):
        """
        The system shall accept submissions from unauthenticated users of the registration form by signing in the user to an unactivated account, by generating an email address confirmation request, and by indicating to the user that this has happened.
        """
        self.logout()
        registration_data = {
            'login': 'admin@appropriatesoftware.net',
            'password': u'admin',
            'firstname': u'Adam',
            'lastname': u'Smith',
        }
        res = self.submit(form_data=registration_data, controller='account', action='register')
        self.assert_is_logged_in(res)
        self.assert_account_not_activated(res)
        self.assert_indicator_for_email_confirmation_sent(res)

    def test_61(self):
        """
        The system shall generate email address confirmation request, by creating a pending email confirmation action with any referenced pending action, and sending an email message to the unconfirmed address, passing a reference to the pending email confirmation action with the message.
        """
        self.logout()
        registration_data = {
            'login': u'sid.smith@appropriatesoftware.net',
            'password': u'sid',
            'firstname': u'Sid\xfc3'.encode('utf8'),
            'lastname': u'Smith',
        }
        count_before = len(model.PendingAction.query.all())
        res = self.submit(form_data=registration_data, controller='account', action='register')
        count_after = len(model.PendingAction.query.all())
        assert count_before + 1 == count_after
        # Todo: Assert email has actually been sent.

    def test_181(self):
        """
        The system shall resume an enquiry regarding data openness by redirecting the user to the enquiry confirmation page (as if the enquiry had just been made).
        """
        self.logout()
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_login(res)
        sign_up_link_text = 'or Sign Up for a new account \xc2\xbb'
        res = self.click(sign_up_link_text, res)
        res = res.click(sign_up_link_text)
        self.assert_form_for_register_account_details(res)
        self.assert_reference_to_pending_action(res)
        registration_data = {
            'login': u'sally.smith@appropriatesoftware.net',
            'password': u'sally',
            'firstname': u'Sally',
            'lastname': u'Smith',
        }
        res = self.submit(form_data=registration_data, res=res)
        self.assert_is_logged_in(res)
        self.assert_indicator_for_email_confirmation_sent(res)
        code = self._find_last_pending_action_id()
        #raise Exception, msg
        #print msg
        try:
            res = self.get(controller='account', action='confirm', code=code)
        except Exception, inst:
            # Has been irregularly failing because the code was wrong.
            allPendingActions = model.PendingAction.query.all()
            msg = "All pending actions: " + "\n".join([repr(a) for a in allPendingActions])
            raise Exception, "%s: %s" % (msg, inst)
        self.assert_form_for_confirm_enquiry(res)
        # Check we've got our enquiry back.
        for value in self.enquiry_data.values():
            assert value in res, "Value '%s' not in response: %s" % (
                value, res
            )

class TestConfirmUserEmailAddress(TestController):
    """
    Confirm user email address.
    """

    def test_177(self):
        """
        The system shall accept email confirmation submissions from authenticated users by activating an unactivated account and resuming any pending data openness enquiries.
        """
        self.logout()
        registration_data = {
            'login': u'jim.smith@appropriatesoftware.net',
            'password': u'jim',
            'firstname': u'Jim',
            'lastname': u'Smith',
        }
        res = self.submit(form_data=registration_data, controller='account', action='register')
        self.assert_is_logged_in(res)
        self.assert_account_not_activated(res)
        code = self._find_last_pending_action_id()
        res = self.get(controller='account', action='confirm', code=code)
        self.assert_account_is_activated(res)

    def test_179(self):
        """
        The system shall accept email confirmation submissions from unauthenticated users by redirecting to the login page, passing on the submitted reference to a pending email confirmation action.
        """
        self.logout()
        registration_data = {
            'login': u'sue.smith@appropriatesoftware.net',
            'password': u'sue',
            'firstname': u'Sue',
            'lastname': u'Smith',
        }
        res = self.submit(form_data=registration_data, controller='account', action='register')
        self.assert_is_logged_in(res)
        self.assert_account_not_activated(res)
        self.logout()
        code = self._find_last_pending_action_id()
        res = self.get(controller='account', action='confirm', code=code)
        self.assert_form_for_login(res)


