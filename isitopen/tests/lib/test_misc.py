import pkgutil
import email

import isitopen.lib.misc


def test_get_body_01():
    text = pkgutil.get_data('isitopen', 'tests/testdata/charset_message.txt')
    msg = email.message_from_string(text)
    out = isitopen.lib.misc.get_body(msg)
    assert 'isitopen' in out

