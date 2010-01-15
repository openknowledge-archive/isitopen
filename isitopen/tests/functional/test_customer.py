from isitopen.tests import *

class TestController(TestController):

    enquiry_data = {
        'to': 'data-handler@appropriatesoftware.net',
        'body': 'afdjdakfdakjfad',
        'subject': 'any old thing',
    }
    admin_credentials = {'login': 'mark.smith@appropriatesoftware.net', 'password': 'mark'}
    other_credentials = {'login': 'bob.smith@appropriatesoftware.net', 'password': 'bob'}

    def get(self, *args, **kwds):
        offset = url_for(*args, **kwds)
        headers = self.write_cookie_headers()
        res = self.app.get(offset, headers=headers)
        self.read_cookie_headers(res)
        res = self.try_to_follow(res)
        return res

    def submit(self, form_data={}, form=None, res=None, forms_index=0, button_name='send', *args, **kwds):
        if not form:
            if not res:
                res = self.get(*args, **kwds)
            form = res.forms[forms_index]
        for (name, value) in form_data.items():
            form[name] = value
        headers = self.write_cookie_headers()
        res = form.submit(button_name, headers=headers)
        self.read_cookie_headers(res)
        res = self.try_to_follow(res)
        return res

    def try_to_follow(self, res, count=0):
        if count > 10:
            raise Exception, "Terminating after 10 continuous redirects!"
        if res.status == 302:
            count += 1
            res = res.follow()
            self.read_cookie_headers(res)
            res = self.try_to_follow(res, count)
        return res

    def write_cookie_headers(self, headers={}):
        if hasattr(self, 'cookies'):
            for (name, value) in self.cookies.items():
                print "Writing cookie in request headers: %s=\"%s\"" % (name, value)
                headers['Cookie'] = '%s="%s"' % (name, value)
        return headers

    def read_cookie_headers(self, res):
        import re
        if not hasattr(self, 'cookies'):
            self.cookies = {}
        lines = str(res).split('\n')
        for line in lines:
            match = re.match('Set-Cookie: (\w+)=\"(\w+)\"', line)
            if match:
                (name, value) = match.groups()
                print "Reading cookie from response headers: %s=\"%s\"" % (name, value)
                self.cookies[name] = value

    def login(self, res=None, credentials=None):
        if credentials == None:
            credentials = self.admin_credentials
        res = self.submit(form_data=credentials, res=res, controller="account", action="login")
        self.assert_is_logged_in(res)
        return res

    def logout(self):
        res = self.get(controller="account", action="logout")
        self.assert_not_logged_in(res)
        return res

    def get_form_for_start_enquiry(self):
        return self.get(controller='enquiry', action='start')

    def submit_form_for_start_enquiry(self, res=None):
        if not res:
            res = self.get_form_for_start_enquiry()
            self.assert_form_for_start_enquiry(res)
        return self.submit(form_data=self.enquiry_data, button_name='start', res=res)

    def submit_form_for_confirm_enquiry(self, res):
        return self.submit(form_data=self.enquiry_data, button_name='confirm', res=res)

    def assert_account_not_activated(self, res):
        self.assert_checkpoint('account-not-activated', res)

    def assert_account_is_activated(self, res):
        self.assert_checkpoint('account-is-activated', res)

    def assert_not_logged_in(self, res):
        self.assert_checkpoint('not-logged-in', res)

    def assert_is_logged_in(self, res):
        self.assert_checkpoint('is-logged-in', res)

    def assert_form_for_login(self, res):
        self.assert_checkpoint('form-for-login', res)

    def assert_form_for_start_enquiry(self, res):
        self.assert_checkpoint('form-for-start-enquiry', res)

    def assert_form_for_confirm_enquiry(self, res):
        self.assert_checkpoint('form-for-confirm-enquiry', res)

    def assert_form_for_confirm_email(self, res):
        self.assert_checkpoint('form-for-confirm-email', res)

    def assert_reference_to_pending_action(self, res):
        self.assert_checkpoint('reference-to-pending-action', res)

    def assert_checkpoint(self, checkvalue, res):
        checkpoint = '<!--checkpoint:%s-->' % checkvalue
        if checkpoint not in res:
            raise Exception('Checkpoint %s not found in response:\n\n%s.\n\n' % (checkpoint, res))

    def fail_if_checkpoint(self, check, res):
        try:
            self.assert_checkpoint(check, res)
        except:
            pass
        else:
            raise Exception('Checkpoint %s was found in response:\n\n%s.\n\n' % (checkpoint, res))


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
        # Todo: Currently just blocks.
        res = self.login(credentials=self.other_credentials)
        self.assert_account_not_activated(res)
        res = self.get_form_for_start_enquiry()
        #self.assert_form_for_confirm_email(res)

    def test_182(self):
        """
        The system shall accept from authenticated owners of activated accounts confirmation of the summary of enquiry regarding data openness by sending the enquiry to a data handler and indicating to the user that this has happened.
        """
        res = self.login()
        self.assert_account_is_activated(res)
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_confirm_enquiry(res)
        res = self.submit_form_for_confirm_enquiry(res)
        self.assert_checkpoint('indicator_for_confirmed_enquiry', res)
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


class TestDispatchDataOpennessEnquiry(TestController):
    """
    Send enquiry regarding data openness to data handler.
    """

    def test_165(self):
        """
        The system shall action submissions of the form for starting data openness enquiries by sending an email to the given data controller and storing the enquiry.
        """
        pass


class TestRegisterNewUserAccount(TestController):
    """
    Register new user account.
    """

    def _confirm_account(self, email):
        user = model.User.query.filter_by(email=login).first()
        user.is_confirmed = True
        model.Session.commit()

    def test_170(self):
        """
        The system shall present to unauthenticated users a registration form, for registering new user accounts.
        """
        self.logout()
        res = self.get(controller='account', action='register')
        self.assert_checkpoint('form-for-register-account-details', res)

    def test_174(self):
        """
        The system shall set on the registration form a hidden value for any passed reference to a pending action.
        """
        self.logout()
        res = self.get(controller='account', action='register', code='1')
        self.assert_reference_to_pending_action(res)

    def test_171(self):
        """
        The system shall accept submissions from unauthenticated users of the registration form by signing in the user to an unactivated account, by generating an email address confirmation request, and by resuming any referenced pending action.
        """
        self.logout()
        registration_data = {
            'login': 'admin@appropriatesoftware.net',
            'password': 'admin',
            'firstname': 'Adam',
            'lastname': 'Smith',
        }
        res = self.submit(form_data=registration_data, controller='account', action='register')
        self.assert_is_logged_in(res)
        self.assert_account_not_activated(res)

    def test_61(self):
        """
        The system shall generate email address confirmation request, by creating a pending email confirmation action with any referenced pending action, and sending an email message to the unconfirmed address, passing a reference to the pending email confirmation action with the message.
        """
        self.logout()
        registration_data = {
            'login': 'sid.smith@appropriatesoftware.net',
            'password': 'sid',
            'firstname': 'Sid',
            'lastname': 'Smith',
        }
        count_before = len(model.PendingAction.query.all())
        res = self.submit(form_data=registration_data, controller='account', action='register')
        count_after = len(model.PendingAction.query.all())
        assert count_before + 1 == count_after
        # Todo: Assert email is actually sent.

    def test_181(self):
        """
        The system shall resume an enquiry regarding data openness by redirecting the user to the enquiry confirmation page (as if the enquiry had just been made).
        """
        pass


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
        res = self.submit_form_for_start_enquiry()
        self.assert_form_for_login(res)
        self.assert_not_logged_in(res)
        #res = self.get(controller='account', action='login')
        res = self.submit(form_data=self.admin_credentials, res=res, controller="account", action="login")
        self.assert_is_logged_in(res)
        self.assert_form_for_confirm_enquiry(res)

    def test_169(self):
        """
        The system shall present near any login form options both to register new user account details and to recover old user account details, passing on any reference to a pending action.
        """
        self.logout()
        res = self.get(controller='account', action='login')
        self.assert_not_logged_in(res)
        self.assert_checkpoint('option-to-register-account-details', res)
        self.assert_checkpoint('option-to-recover-account-details', res)

    def test_173(self):
        """
        The system shall set on any login form hidden form values for any passed reference to a pending action.
        """
        self.logout()
        res = self.get(controller='account', action='login', code='1')
        self.assert_checkpoint('reference-to-pending-action', res)


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
            'login': 'jim.smith@appropriatesoftware.net',
            'password': 'jim',
            'firstname': 'Jim',
            'lastname': 'Smith',
        }
        res = self.submit(form_data=registration_data, controller='account', action='register')
        self.assert_is_logged_in(res)
        self.assert_account_not_activated(res)
        # Pretend email has been sent, and link is being followed.
        pending_action = model.PendingAction.query.all()[-1]
        code = pending_action.id
        res = self.get(controller='account', action='confirm', code=code)
        self.assert_account_is_activated(res)

    def test_179(self):
        """
        The system shall accept email confirmation submissions from unauthenticated users by redirecting to the login page, passing on the submitted reference to a pending email confirmation action.
        """
        self.logout()
        registration_data = {
            'login': 'sue.smith@appropriatesoftware.net',
            'password': 'sue',
            'firstname': 'Sue',
            'lastname': 'Smith',
        }
        res = self.submit(form_data=registration_data, controller='account', action='register')
        self.assert_is_logged_in(res)
        self.assert_account_not_activated(res)
        self.logout()
        # Pretend email has been sent, and link is being followed.
        pending_action = model.PendingAction.query.all()[-1]
        code = pending_action.id
        res = self.get(controller='account', action='confirm', code=code)
        self.assert_form_for_login(res)

