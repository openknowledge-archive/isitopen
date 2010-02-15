from repoze.who.middleware import PluggableAuthenticationMiddleware
from repoze.who.interfaces import IIdentifier
from repoze.who.interfaces import IChallenger
from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.plugins.cookie import InsecureCookiePlugin
from repoze.who.plugins.form import RedirectingFormPlugin
from repoze.who.plugins.htpasswd import HTPasswdPlugin
from StringIO import StringIO
import logging

class ModelPasswordPlugin(object):

    def __init__(self, model):
        self.model = model

    # IAuthenticatorPlugin
    def authenticate(self, environ, identity):
        try:
            login = identity['login']
            password = identity['password']
        except KeyError:
            return None
        user = self._find_user(login)
        if not user:
            return None
        if user.password.encode('utf8') == password:
            return login
        return None

    def _find_user(self, login): 
        return self.model.User.query.filter_by(email=login).first()

def AuthenticationMiddleware(app):
    import isitopen.model as model
    import isitopen.lib.helpers as h
    modelpassword = ModelPasswordPlugin(model)
    basicauth = BasicAuthPlugin('repoze.who')
    auth_tkt = AuthTktCookiePlugin('secret', 'auth_tkt')
    form = RedirectingFormPlugin(
        login_form_url=h.url_for(controller='account', action='login'),
        login_handler_path=h.url_for('login-handler'),
        logout_handler_path=h.url_for('logout-handler'),
        rememberer_name='auth_tkt',
    )

    form.classifications = { IIdentifier:['browser'],
                             IChallenger:['browser'] } # only for browser
    identifiers = [('form', form),('auth_tkt',auth_tkt),('basicauth',basicauth)]
    authenticators = [('modelpassword', modelpassword)]
    challengers = [('form',form), ('basicauth',basicauth)]
    mdproviders = []

    from repoze.who.classifiers import default_request_classifier
    from repoze.who.classifiers import default_challenge_decider
    log_stream = None
    import os
    if os.environ.get('WHO_LOG'):
        log_stream = sys.stdout

    return PluggableAuthenticationMiddleware(
        app,
        identifiers,
        authenticators,
        challengers,
        mdproviders,
        default_request_classifier,
        default_challenge_decider,
        log_stream = log_stream,
        log_level = logging.DEBUG
    )

