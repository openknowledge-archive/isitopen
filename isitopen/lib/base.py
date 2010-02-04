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
from paste.request import parse_formvars
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

    def _receive(self, environ):
        """Read the WSGI environ."""
        self._receive_remote_user(environ)
        if self._is_logged_in():
            self._read_account_status()
        return self._receive_formvars(environ)

    def _receive_remote_user(self, environ):
        c.remote_user = environ.get('REMOTE_USER')
        c.user = self._find_user(c.remote_user)

    def _find_user(self, login):
        return model.User.query.filter_by(email=login).first()

    def _is_logged_in(self):
        return bool(c.remote_user)

    def _read_account_status(self):
        if c.user and c.user.is_confirmed:
            c.is_account_activated = True
        else:
            c.is_account_activated = False

    def _is_account_activated(self):
        return bool(c.is_account_activated)

    def _receive_formvars(self, environ):
        formvars = parse_formvars(environ)
        c.pending_action_code = formvars.get('code', None)
        return formvars

    def _redirect_to_home(self):
        if self._is_logged_in():
            h.redirect_to(controller='account', action='index')
        else:
            h.redirect_to(controller='home', action='index')
 
    def _redirect_to_login(self, **kwds):
        h.redirect_to(controller='account', action='login', **kwds)

    def _redirect_to_login_handler(self, **kwds):
        h.redirect_to('login-handler', **kwds)

    def _redirect_to_confirm_account(self, **kwds):
        h.redirect_to('confirm-account', **kwds)

    def _redirect_to_enquiry(self, **kwds):
        h.redirect_to(controller='enquiry', action='view', **kwds)

    def _redirect_to_start_enquiry(self, **kwds):
        h.redirect_to(controller='enquiry', action='start', **kwds)

    def _redirect_to_wait_enquiry(self, **kwds):
        h.redirect_to(controller='enquiry', action='wait', **kwds)

    def _validate_email_address(self, email_address):
        import formalchemy.validators
        try:
            formalchemy.validators.email(email_address)
        except formalchemy.validators.ValidationError, inst:
            c.error = u'Invalid email address: %s' % inst

    def _make_email_message(self, email_body, **headers):
        if type(email_body) == unicode:
            email_body = email_body.encode('utf8')
        headers['Content-Type'] = 'text/plain; charset="utf-8"'
        email_message = email.message_from_string(email_body)
        for name, value in headers.items():
            if type(value) == unicode:
                value = value.encode('utf8')
            email_message[name.capitalize()] = value
        return email_message
 
    def _send_email_message(self, email_message):
        mailer = Mailer.default()
        mailer.send(email_message)

# Include the '_' function in the public names
__all__ = [__name for __name in locals().keys() if not __name.startswith('_') \
           or __name == '_']
