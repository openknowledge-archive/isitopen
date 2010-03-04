"""The base Controller API

Provides the BaseController class for subclassing, and other objects
utilized by Controllers.
"""
from pylons import c, cache, config, g, request, response, session
from pylons.controllers import WSGIController
from pylons.controllers.util import abort, etag_cache, redirect_to
from pylons.decorators import jsonify, validate
from pylons.i18n import _, ungettext, N_
from pylons.templating import render
import isitopen.lib.helpers as h
import isitopen.model as model
from isitopen.lib.mailer import Mailer
import email
import logging
log = logging.getLogger(__name__)

class BaseController(WSGIController):

    def __call__(self, environ, start_response):
        """Invoke the WSGI controller."""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()

    def _receive(self):
        """Read the WSGI environ."""
        self._receive_remote_user()
        if self._is_logged_in():
            self._read_account_status()
        self._read_server_name()
        self._receive_formvars()

    def _receive_remote_user(self):
        c.remote_user = request.environ.get('REMOTE_USER')
        c.user = self._find_user(c.remote_user)

    def _find_user(self, login):
        return model.User.query.filter_by(email=login).first()

    def _is_logged_in(self):
        return bool(c.user)

    def _is_admin_logged_in(self):
        # Todo: Get admin_emails from config?
        admin_emails = [
            'john.bywater@appropriatesoftware.net',
            'mark.smith@appropriatesoftware.net',
        ]
        if not self._is_logged_in():
            return False
        if c.user.email in admin_emails:
            return True
        return False

    def _read_account_status(self):
        if c.user and c.user.is_confirmed:
            c.is_account_activated = True
        else:
            c.is_account_activated = False

    def _is_account_activated(self):
        return bool(c.is_account_activated)

    def _read_server_name(self):
        server_name = request.environ['SERVER_NAME']
        if server_name in ['localhost', '0.0.0.0']:
            # Needed for development and testing...
            server_name = '127.0.0.1:5000'
        c.site_url = 'http://%s' % server_name

    def _receive_formvars(self):
        c.pending_action_code = request.params.get('code', None)

    def _redirect_to(self, *args, **kwds):
        h.redirect_to(*args, **kwds)

    def _redirect_to_home(self):
        if self._is_logged_in():
            self._redirect_to(controller='account', action='index')
        else:
            self._redirect_to(controller='home', action='index')
 
    def _redirect_to_login(self, **kwds):
        self._redirect_to(controller='account', action='login', **kwds)

    def _redirect_to_login_handler(self, **kwds):
        self._redirect_to('login-handler', **kwds)

    def _redirect_to_confirm_account(self, **kwds):
        self._redirect_to('confirm-account', **kwds)

    def _redirect_to_enquiry_list(self, **kwds):
        self._redirect_to(controller='enquiry', action='list', **kwds)

    def _redirect_to_enquiry(self, **kwds):
        self._redirect_to(controller='enquiry', action='view', **kwds)

    def _redirect_to_start_enquiry(self, **kwds):
        self._redirect_to(controller='enquiry', action='start', **kwds)

    def _redirect_to_follow_up_enquiry(self, **kwds):
        self._redirect_to(controller='enquiry', action='followup', **kwds)

    def _validate_email_address(self, email_address):
        import formalchemy.validators
        try:
            formalchemy.validators.email(email_address)
        except formalchemy.validators.ValidationError, inst:
            c.error = u'Invalid email address: %s' % inst

    def _mailer(self):
        return Mailer(site_url=c.site_url)

#    def logout(self):
#        raise Exception, "No logout action on '%s' controller." % self.__class__

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
