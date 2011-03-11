"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
import re

import genshi
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *
from webhelpers import date
from webhelpers.html.tools import js_obfuscate
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
    body = re.sub('<isitopen.okfn.org\s*>', '&lt;isitopen.okfn.org&gt;', body)
    # body = body.replace('<isitopen.okfn.org>', '&lt;isitopen.okfn.org&gt;')
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

def obfuscate_email(email_address):
    '''Obfuscate an email address for web display (hex encode and delete last 6
    chars).

    Borrowed and simplified from webhelpers.html.tools.mail_to
    '''
    if not email_address:
        return ''
    # replace last 5 characters
    email_address_obfuscated = email_address[:-6] + '....'
    email_address_obfuscated = HTML.literal(''.join(
        ['&#%d;' % ord(x) for x in email_address_obfuscated]))

    return email_address_obfuscated

def icon(name, alt=None):
    if alt is None:
        alt = name
    return literal('<img src="%s" class="icon" alt="%s" title="%s" /> ' %
            (icon_url(name), alt, alt))

def icon_url(name):
    return url_for('/images/icons/%s.png' % name)

def enquiry_status_icon(enq):
    if enq.status == enq.RESOLVED_OPEN:
        return icon('tick', alt='Enquiry Resolved - Data is Open')
    elif enq.status == enq.RESOLVED_CLOSED:
        return icon('cancel', alt='Enquiry Resolved - Data is Closed')
    elif enq.status == enq.RESOLVED_NOT_KNOWN:
        return icon('exclamation', alt='Enquiry Resolved - Data Status Unknown')
    else:
        return icon('clock', alt='Enquiry in Progress')

def user_link(user):
    out = icon('user') + ' '
    if user and (user.firstname or user.lastname):
        out = out + literal(user.firstname + ' ' + user.lastname)
    else:
        out += literal('Anonymous')
    return out

def snippet(text, numchars=190):
    if not text:
        return ''
    elif len(text) < numchars:
        return text
    else:
        return text[:numchars] + '...'

