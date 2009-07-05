import datetime
import email as E

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
    Column('owner_id', types.String(36), ForeignKey('user.id')),
    )

message_table = Table('message', metadata,
    Column('id', types.String(36), default=make_uuid, primary_key=True),
    Column('enquiry_id', types.String(36), ForeignKey('enquiry.id')),
    Column('mimetext', types.Text()),
    Column('status', types.UnicodeText, default=MessageStatus.not_yet_sent),
    Column('timestamp', types.DateTime, default=datetime.datetime.now),
    )

class User(object):
    pass

class Message(object):
    def _get_email(self):
        '''
        @return email.Message object
        '''
        if not hasattr(self, '_email'):
            if self.mimetext:
                # REALLY odd.
                # 1. mimetext was unicode (even though set to str type types.Text())
                # 2. This makes message_from_string fail to parse properly!!
                self._email = E.message_from_string(
                        self.mimetext.encode('utf8', 'ignore'))
            else:
                self._email = E.message_from_string('')
        return self._email

    # def _set_email(self, email_message_obj):
    #    self._email = email_message_obj
    #    self.save_email()

    email = property(_get_email)
    to = property(lambda self: self.email['To'])
    subject = property(lambda self: self.email['Subject'])
    body = property(lambda self: self.email.get_payload())


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

