import datetime

from meta import *

import uuid
def make_uuid():
    return str(uuid.uuid4())

class EnquiryStatus(object):
    not_yet_sent = u'Not Yet Sent'
    sent = u'Sent (Awaiting Response)'
    response = u'Response'
    awaiting_response = u'Awaiting Response'
    closed_ok = u'Closed (OK)'
    closed_not_ok = u'Closed (Not OK)'

enquiry_table = Table('enquiry', metadata,
        Column('id', types.String(36), default=make_uuid, primary_key=True),
        Column('to', types.UnicodeText),
        Column('subject', types.UnicodeText),
        Column('sender', types.UnicodeText),
        Column('body', types.UnicodeText),
        Column('status', types.UnicodeText, default=EnquiryStatus.not_yet_sent),
        Column('timestamp', types.DateTime, default=datetime.datetime.now),
        Column('last_updated', types.DateTime, default=datetime.datetime.now),
        )

class Enquiry(object):
    pass

mapper(Enquiry, enquiry_table,
    order_by=enquiry_table.c.id)


