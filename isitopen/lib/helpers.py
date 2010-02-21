"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import genshi
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *

from webhelpers.markdown import markdown as old_markdown
from routes import url_for
from routes import redirect_to

# redo markdown to deal with None values
def new_markdown(text, **kwargs):
    if not text:
        return ''
    else:
        return old_markdown(text, **kwargs)
markdown = new_markdown

def email_body(body):
    #body = str(body)
    #if type(body) == str:
    #    body = body.decode('utf8')
    body = body.replace('\r\n', '\n')
    # fix issue where quoted text immediately after quoted text at start of
    # quoting
    body = body.replace(':\n>', ':\n\n>')
    # in quoted sections seem to get line continuations with =
    body = body.replace('=\n', '')
    # incredibly ugly hack to deal with <isitopen@okfn.org> in message body
    # (does not get handled by markdown for some reason ...)
    import re
    body = re.sub('<isitopen.okfn.org\s*>', '&lt;isitopen.ofkn.org&gt;', body)
    # body = body.replace('<isitopen.okfn.org>', '&lt;isitopen.ofkn.org&gt;')
    #return ""
    #return markdown(repr(type(body)).replace("<", "&lt;") + body[:10])
    # Todo: Fix this, it screws up when unicode is in the enquiry body.
    try:
        out = genshi.HTML(markdown(body))
    except:
        out = '<p><strong>We had problems prettifying the email you are trying to display -- probably due to broken HTML in it!</strong></p>\n\n'
        try:
            out += unicode(genshi.escape(body))
        except:
            pass
        out = genshi.HTML(out)
    return out

