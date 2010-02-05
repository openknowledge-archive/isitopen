import datetime
import email as E

from types import JsonType
from meta import *
from types import json

import uuid
def make_uuid():
    return str(uuid.uuid4())

class EnquiryStatus(object):
    resolved_open = u'Resolved (Open)'
    resolved_closed = u'Resolved (Closed)'
    unresolved = u'Unresolved'

class MessageStatus(object):
    not_yet_sent = u'Not Yet Sent'
    sent_not_synced = u'Sent But Not Synced'
    sent = u'Sent'
    # a response but no notification sent to enquiry owner
    response_no_notification = u'Response But No Notification'
    # notification done
    response = u'Response'


user_table = Table('user', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('firstname', UnicodeText),
    Column('lastname', UnicodeText),
    Column('email', Text),
    Column('password', UnicodeText),
    Column('is_confirmed', Boolean, default=False),
    )

enquiry_table = Table('enquiry', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('summary', UnicodeText),
    Column('status', UnicodeText, default=EnquiryStatus.unresolved),
    Column('timestamp', DateTime, default=datetime.datetime.now),
    Column('last_updated', DateTime, default=datetime.datetime.now),
    Column('owner_id', String(36), ForeignKey('user.id')),
    Column('extras', JsonType),
    )

message_table = Table('message', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('enquiry_id', String(36), ForeignKey('enquiry.id')),
    Column('sender', Text),
    Column('mimetext', Text),
    Column('status', UnicodeText),
    Column('timestamp', DateTime, default=datetime.datetime.now),
    )

pending_action_table = Table('pending_action', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('type', Text),
    Column('data', Text),
    Column('timestamp', DateTime, default=datetime.datetime.now),
    )

# sqlalchemy migrate version table
import sqlalchemy.exceptions
try:
    version_table = Table('migrate_version', metadata, autoload=True)
except sqlalchemy.exceptions.NoSuchTableError:
    pass

class DomainObject(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    
    _exclude_from___str__ = []
    def __str__(self):
        repr = u'{{%s' % self.__class__.__name__
        table = orm.class_mapper(self.__class__).mapped_table
        for col in table.c:
            if col.name not in self._exclude_from___str__:
                repr += u' %s=%s' % (col.name, getattr(self, col.name))
        repr += u'}}'
        return repr.encode('utf8')

    def __repr__(self):
        return self.__str__()

class User(DomainObject):
    pass

class Message(DomainObject):
    _exclude_from___str__ = [ 'mimetext' ]
    def _get_email(self):
        '''
        @return email.Message object
        '''
        if not hasattr(self, '_email'):
            if self.mimetext:
                if type(self.mimetext) == unicode:
                    # REALLY odd.
                    # 1. mimetext was unicode (even though set to str type types.Text())
                    # 2. This makes message_from_string fail to parse properly!!
                    # Todo: Log warning.
                    email_message_mimetext = self.mimetext.encode('utf8')
                else:
                    email_message_mimetext = self.mimetext
            else:
                email_message_mimetext = ''
            self._email = E.message_from_string(email_message_mimetext)
        return self._email

    # def _set_email(self, email_message_obj):
    #    self._email = email_message_obj
    #    self.save_email()

    def _body(self):
        if self.email.is_multipart():
            # take first message
            # TODO: could be more sophisticated (e.g. use html if it exists)
            body = self.email.get_payload(0).get_payload(decode=True)
        else:
            body = self.email.get_payload(decode=True)
        body = body.replace('\r\n', '\n')
        return body

    email = property(_get_email)
    to = property(lambda self: self.email['To'])
    subject = property(lambda self: self.email['Subject'].decode('utf8'))
    body = property(_body)


class Enquiry(DomainObject):
    def _get_to(self):
        if self.messages:
            return self.messages[0].to
        else:
            return None
    to = property(_get_to)


class PendingAction(DomainObject):

    CONFIRM_ACCOUNT = 'confirm-account'
    START_ENQUIRY = 'start-enquiry'

    def store(self, **kwds):
        self.data = json.dumps(kwds)

    def retrieve(self):
        return json.loads(self.data)


mapper(User, user_table,
    order_by=user_table.c.id)

mapper(Enquiry, enquiry_table, properties={
    'owner': relation(User, backref='enquiries'),
    },
    order_by=enquiry_table.c.timestamp.desc()
    )

mapper(Message, message_table, properties={
    'enquiry': relation(Enquiry,
        backref=backref('messages', order_by=message_table.c.timestamp),
        ),
    },
    order_by=message_table.c.timestamp.desc()
)

mapper(PendingAction, pending_action_table,
    order_by=pending_action_table.c.timestamp.desc()
)

