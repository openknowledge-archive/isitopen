import datetime

from meta import *

import uuid
def make_uuid():
    return str(uuid.uuid4())

class EnquiryStatus(object):
    resolved_open = u'Resolved (Open)'
    resolved_closed = u'Resolved (Closed)'
    unresolved = u'Unresolved'

class MessageStatus(object):
    not_yet_sent = u'Not Yet Sent'
    sent = u'Sent'


user_table = Table('user', metadata,
        Column('id', types.String(36), default=make_uuid, primary_key=True),
        Column('email', types.UnicodeText),
        Column('username', types.UnicodeText),
        )

enquiry_table = Table('enquiry', metadata,
        Column('id', types.String(36), default=make_uuid, primary_key=True),
        Column('status', types.UnicodeText, default=EnquiryStatus.unresolved),
        Column('timestamp', types.DateTime, default=datetime.datetime.now),
        Column('last_updated', types.DateTime, default=datetime.datetime.now),
        Column('owner_id', types.String(36), ForeignKey('user.id'),
        )

message_table = Table('message', metadata,
        Column('id', types.String(36), default=make_uuid, primary_key=True),
        # Column('mimetext', types.UnicodeText),
        Column('enquiry_id', types.String(36), ForeignKey('enquiry.id')),
        Column('to', types.UnicodeText),
        Column('subject', types.UnicodeText),
        Column('sender', types.UnicodeText),
        Column('body', types.UnicodeText),
        Column('status', types.UnicodeText, default=MessageStatus.not_yet_sent),
        Column('timestamp', types.DateTime, default=datetime.datetime.now),
        )

class User(object):
    pass

class Message(object):
    pass

class Enquiry(object):
    pass

mapper(User, user_table,
    order_by=user_table.c.id)

mapper(Enquiry, enquiry_table, properties={
    'owner': relation(User, backref='enquiries'),
    },
    order_by=enquiry_table.c.id
    )

mapper(Message, message_table, properties={
    'enquiry': relation(Enquiry, backref='messages'),
    },
    order_by=message_table.c.id,
)


