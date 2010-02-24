import isitopen.lib.helpers as h

in1 = '''A response

A Publisher

2009/7/10 Is It Open Enquiry Service <okfn.isitopen.test@googlemail.com>:
> Dear **...**,
>
> I am **insert information about yourself, e.g. I am a researcher in field=
 X**.
>
'''

in2 = "I don't have much to say ...\r\n\r\nA Publisher\r\n\r\n2009/7/10 Is It Open Enquiry Service <okfn.isitopen.test@googlemail.com>:\r\n> Dear **...**,\r\n>\r\n> I am **insert information about yourself, e.g. I am a researcher in field=\r\n X**.\r\n>\r\n> I am writing on behalf of the Open Scientific Data Working Group of the O=\r\npen Knowledge Foundation [1]. We are seeking clarification of the 'openness=\r\n' of the scientific data associated with your publications such as **insert=\r\n information or link here**."

def test_email_body():
    out = unicode(h.email_body(in1))
    assert 'blockquote' in out, out

    out = unicode(h.email_body(in2))
    assert 'blockquote' in out
    assert not 'O=' in out
    assert 'Open Knowledge' in out

def test_obfuscate_email():
    inaddr = 'xyz@okfn.org'
    outaddr = u'&#120;&#121;&#122;&#64;&#111;&#107;&#46;&#46;&#46;&#46;'
    out = unicode(h.obfuscate_email(inaddr))
    assert out == outaddr, out

