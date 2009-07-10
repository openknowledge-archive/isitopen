"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
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
    body = body.replace('\r\n', '\n')
    # fix issue where quoted text immediately after quoted text at start of
    # quoting
    body = body.replace(':\n>', ':\n\n>')
    # in quoted sections seem to get line continuations with =
    body = body.replace('=\n', '')
    return markdown(body)

