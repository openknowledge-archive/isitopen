import logging
import email as E

from pylons import config
from isitopen.lib.base import *

log = logging.getLogger(__name__)

class PendingController(BaseController):

    def index(self, environ, start_response):
        formvars = self._receive(environ)
        code = formvars.get('code')
        if not code:
            abort(404)
        if not self._is_logged_in():
            self._redirect_to_login(code=code)
        else:
            self._do_pending_action(code)

    def _do_pending_action(self, code):
        pending_action = model.PendingAction.query.get(code)
        if not pending_action:
            abort(404)
        data = pending_action.retrieve()
        if pending_action.type == model.PendingAction.START_ENQUIRY:
            self._redirect_to_start_enquiry(code=code)
        else:
            raise Exception, "Action type not supported: %s" % action_name

