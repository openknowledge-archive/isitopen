"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper
from formalchemy.ext.pylons import maps # routes generator

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    map.connect('home', '/', controller='home', action='index')
    map.connect('about', '/about/', controller='home', action='guide')
    map.connect('guide', '/guide/', controller='home', action='guide')
    map.connect('start', '/enquiry/start/', controller='enquiry', action='start')
    map.connect('browse', '/enquiry/list/', controller='enquiry', action='list')
    map.connect('register', '/account/register/', controller='account', action='register')
    map.connect('login-handler', '/account/login/handler/')
    map.connect('confirm-account', '/account/confirm/', controller='account', action='confirm')
    # Map the /admin url to FA's AdminController
    maps.admin_map(map, controller='admin', url='/admin')
    # standard controllers
    map.connect('/{controller}/', action='index')
    map.connect('/{controller}/{action}/')
    map.connect('/{controller}/{action}/{id}/')
    # standardize on trailing slash
    map.redirect('/*(url)', '/{url}/', requirements=dict(url='.*[^/]$'), _redirect_code='301 Moved Permanently')

    return map
