from isitopen.lib.base import *

class AccountController(BaseController):

    def login(self, environ, start_response):
        # Todo: Change to always set came_from value - otherwise
        # authentication middleware will redirect here indefinitely,
        # because by default it returns to HTTP_REFERER.
        # Todo: Try again to set login handler path to /account/login/.
        formvars = self._receive(environ)
        if c.pending_action_code:
            c.came_from = h.url_for(controller='enquiry', action='start', code=c.pending_action_code)
        else:
            c.came_from = formvars.get('came_from')
        if self._is_logged_in():
            self._redirect_to_home()
        return render('account/login.html')

    def index(self, environ, start_response):
        formvars = self._receive(environ)
        if self._is_logged_in():
            return render('account/index.html')
        else:
            self._redirect_to_login()
            return 'Server response, you will be redirected.'

    def recover(self, environ, start_response):
        self._receive(environ)
        if self._is_logged_in():
            self._redirect_to_home()
            return 'Server response, you will be redirected.'
        else:
            return render('account/recover.html')

    def register(self, environ, start_response):
        formvars = self._receive(environ)
        c.firstname = formvars.get('firstname', '').decode('utf8')
        c.lastname = formvars.get('lastname', '').decode('utf8')
        c.login = formvars.get('login', '')
        c.password = formvars.get('password', '').decode('utf8')
        if formvars.get('send'):
            self._validate_registration_submission()
            came_from = h.url_for(controller='account', action='index', code=c.pending_action_code)
            if not c.error:
                self._create_user(c.firstname, c.lastname, c.login, c.password)
                self._request_confirmation(c.login, code=c.pending_action_code)
                self._redirect_to_login_handler(
                    login=c.login, password=c.password,
                    came_from=came_from
                )
        return render('account/register.html')

    def confirm(self, environ, start_response):
        formvars = self._receive(environ)
        confirmation_code = formvars.get('code')
        if confirmation_code:
            login = ''
            enquiry_code = ''
            pending_action = model.PendingAction.query.get(confirmation_code)
            if pending_action:
                if pending_action.type == model.PendingAction.CONFIRM_ACCOUNT:
                    confirmation_data = pending_action.retrieve()
                    login = confirmation_data['login']
                    enquiry_code = confirmation_data['code']
                else:
                    raise Exception, "Wrong action code: %s" % repr(pending_action)
            if login:
                self._confirm_account(login)
                if self._is_logged_in():
                    if enquiry_code:
                        self._redirect_to_start_enquiry(code=enquiry_code)
                        return
                    else:
                        self._redirect_to_home()
                        return
                else:
                    if enquiry_code:
                        self._redirect_to_login(code=enquiry_code)
                        return
                    else:
                        self._redirect_to_login()
                        return
            else:
                self._redirect_to_home()
                return
        elif self._is_logged_in():
            if self._is_account_activated():
                self._redirect_to_home()
                return
            elif formvars.get('send'):
                self._request_confirmation(c.user.email)
                c.just_sent_new_request = True
        else:
            self._redirect_to_home()
            return
        return render('account/confirm.html')

    def _validate_registration_submission(self):
        # Todo: Check password looks okay.
        if not (c.firstname and c.lastname and c.login and c.password):
            c.error = 'All fields are required.'
        elif self._find_user(c.login):
            c.error = 'That email address is already being used.'
        else:
            self._validate_email_address(c.login)

    def _create_user(self, firstname, lastname, login, password):
        user = model.User(firstname=firstname, lastname=lastname,
            email=login, password=password, is_confirmed=False)
        model.Session.commit()
        return user

    def _request_confirmation(self, login, code=''):
        type = model.PendingAction.CONFIRM_ACCOUNT
        pending_action = model.PendingAction(type=type)
        pending_action.store(login=login, code=code)
        model.Session.commit()
        user = self._find_user(login)
        confirmation_code = pending_action.id
        self._mailer().send_email_confirmation_request(user, confirmation_code)

    def _confirm_account(self, login):
        user = self._find_user(login)
        if user and not user.is_confirmed:
            user.is_confirmed = True
            model.Session.commit()


