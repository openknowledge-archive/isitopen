# take from http://ginstrom.com/scribbles/2007/11/19/parsing-multilingual-email-with-python/
from email.Iterators import typed_subpart_iterator

def get_charset(message, default='ascii'):
    '''Get the message charset'''
    if message.get_content_charset():
        return message.get_content_charset()
    if message.get_charset():
        return message.get_charset()
    return default

def get_body(message):
    '''Get the body of the email message'''
    if message.is_multipart():
        #get the plain text version only
        text_parts = [part for part in
                typed_subpart_iterator(message, 'text', 'plain')]
        body = []
        for part in text_parts:
            charset = get_charset(part, get_charset(message))
            body.append(unicode(part.get_payload(decode=True),
                                charset,
                                'replace'))
        return u'\n'.join(body).strip()
    else: # if it is not multipart, the payload will be a string
          # representing the message body
        body = unicode(message.get_payload(decode=True),
                       get_charset(message),
                       'replace')
        return body.strip()

