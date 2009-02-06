from ckan.lib.base import *

class EnquiryController(Controller):

    def index(self):
        return render('index.html')
