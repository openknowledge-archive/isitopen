import datetime
import email as E
import uuid

from types import JsonType
from meta import *
from types import json

from isitopen.lib.misc import get_body

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

    # Status strings.
    NOT_SENT = u'Not Yet Sent'
    JUST_SENT = u'Sent But Not Synced'
    SENT_REREAD = u'Sent'
    JUST_RESPONSE = u'Response But No Notification'
    RESPONSE_NOTIFIED = u'Response'

    _exclude_from___str__ = [ 'mimetext' ]

    def _get_email(self):
        '''
        @return email.Message object
        '''
        if not hasattr(self, '_email'):
            if self.mimetext:
                if type(self.mimetext) == unicode:
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
        body = get_body(self.email)
        body = body.replace('\r\n', '\n')
        return body

    email = property(_get_email)
    to = property(lambda self: self.email['To'] if self.email['To'] else '')
    subject = property(lambda self: self.email['Subject'].decode('utf8') if
            self.email['Subject'] else '')
    body = property(_body)

class Enquiry(DomainObject):

    # Status strings.
    STARTED = u'Unresolved'
    RESOLVED_OPEN = u'Resolved (Open)'
    RESOLVED_CLOSED = u'Resolved (Closed)'
    RESOLVED_NOT_KNOWN = u'Resolved (Not Known)'

    @classmethod
    def start_new(self, owner, summary, email_message):
        enquiry = self(
            owner=owner,
            summary=summary,
        )
        message = Message(
            mimetext=email_message.as_string().decode('utf8'),
            status=Message.NOT_SENT,
            sender=owner.email,
            enquiry=enquiry,
        )
        Session.commit()
        return enquiry

    def _get_to(self):
        if self.messages:
            return self.messages[0].to
        else:
            return None
    to = property(_get_to)

    def _get_body(self):
        if self.messages:
            return self.messages[0].body
        else:
            return None
    body = property(_get_body)


class PendingAction(DomainObject):

    # Actions type strings.
    CONFIRM_ACCOUNT = 'confirm-account'
    START_ENQUIRY = 'start-enquiry'

    def store(self, **kwds):
        self.data = json.dumps(kwds)

    def retrieve(self):
        return json.loads(self.data)


def make_uuid():
    return str(uuid.uuid4())

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
    Column('status', UnicodeText, default=Enquiry.STARTED),
    Column('timestamp', DateTime, default=datetime.datetime.now),
    Column('last_updated', DateTime, default=datetime.datetime.now),
    Column('owner_id', String(36), ForeignKey('user.id')),
    Column('extras', JsonType),
    )

message_table = Table('message', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('enquiry_id', String(36), ForeignKey('enquiry.id')),
    Column('sender', Text),
    Column('mimetext', UnicodeText),
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

