from isitopen.lib.base import *

class HomeController(BaseController):

    def index(self):
        return render('index.html')

    def guide(self):
        return render('guide.html')
