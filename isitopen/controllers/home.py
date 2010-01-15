from isitopen.lib.base import *

class HomeController(BaseController):

    def index(self, environ, start_response):
        self._receive(environ)
        return render('index.html')

    def guide(self, environ, start_response):
        self._receive(environ)
        return render('guide.html')

    def about(self, environ, start_response):
        self._receive(environ)
        return render('guide.html')

