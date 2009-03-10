"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.html.tags import *

# TODO: remove the deprecated calls and replace with functionality from
# webhelpers.html, etc.
from webhelpers.rails.wrapped import *

from webhelpers.markdown import markdown
from routes import url_for

# redo markdown to deal with None values
old_markdown = markdown
def new_markdown(text, **kwargs):
    if not text:
        return ''
    else:
        return old_markdown(text, **kwargs)
markdown = new_markdown

