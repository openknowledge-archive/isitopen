from isitopen.tests import *

class TestController(TestController):

    enquiry_data = {
        'to': u'data-handler@appropriatesoftware.net',
        'body': u'afdjdakfdakjfad\xfc',
        'subject': u'any old thing\xfc',
    }
    admin_credentials = {'login': 'mark.smith@appropriatesoftware.net', 'password': u'mark\xfc'}
    other_credentials = {'login': 'bob.smith@appropriatesoftware.net', 'password': u'bob\xfc'}

    @classmethod
    def setup_class(self):
        Fixtures.create()

    @classmethod
    def teardown_class(self):
        Fixtures.remove()

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
            if type(value) == unicode:
                value = value.encode('utf8')
            form[name] = value
        headers = self.write_cookie_headers()
        res = form.submit(button_name, headers=headers)
        self.read_cookie_headers(res)
        res = self.try_to_follow(res)
        return res

    def click(self, button_text, res):
        try:
            res.click(button_text)
        except Exception, inst:
            msg = "Couldn't click button text '%s' in page: \n\n%s\n\n" % (
                button_text, res)
            raise Exception, msg
        else:
            return self.try_to_follow(res)

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

    def assert_form_for_register_account_details(self, res):
        self.assert_checkpoint('form-for-register-account-details', res)

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

    def assert_indicator_for_email_confirmation_sent(self, res):
        self.assert_checkpoint('indicator-for-email-confirmation-sent', res)

    def assert_indicator_for_confirmed_enquiry(self, res):
        self.assert_checkpoint('indicator-for-confirmed-enquiry', res)

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

    def _find_last_pending_action_id(self):
        # Pretend email has been sent, and link is being followed.
        allPendingActions = model.PendingAction.query.all()
        #msg = "\n".join([repr(a) for a in allPendingActions])
        #raise Exception, "All pending actions:\n%s" % msg
        if not allPendingActions:
            raise Exception, "Can't see any pending actions whatsoever."
        pending_action = allPendingActions[0]
        return pending_action.id


