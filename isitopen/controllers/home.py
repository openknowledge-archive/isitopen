from isitopen.lib.base import *

class HomeController(BaseController):

    def index(self):
        self._receive()
        return render('index.html')

    def guide(self):
        self._receive()
        return render('guide.html')

    def about(self):
        self._receive()
        return render('guide.html')

