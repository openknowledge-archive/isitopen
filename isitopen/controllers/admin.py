import logging
from isitopen.lib.base import BaseController, render
from isitopen import model
from isitopen import forms
from isitopen.model import meta
from formalchemy.ext.pylons.admin import FormAlchemyAdminController

log = logging.getLogger(__name__)

class AdminController(BaseController):
    model = model # where your SQLAlchemy mappers are
    forms = forms # module containing FormAlchemy fieldsets definitions
    def Session(self): # Session factory
        return meta.Session

AdminController = FormAlchemyAdminController(AdminController)

