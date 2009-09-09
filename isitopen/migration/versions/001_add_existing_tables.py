import uuid
import datetime

from sqlalchemy import *
from migrate import *

metadata = MetaData(migrate_engine)

from isitopen.model.types import JsonType

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
    response = u'Response'


user_table = Table('user', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('email', UnicodeText),
    Column('username', UnicodeText),
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
    Column('sender', UnicodeText()),
    # would prefer UnicodeText but it seems simple str is needed for emails
    Column('mimetext', Text()),
    Column('status', UnicodeText),
    Column('timestamp', DateTime, default=datetime.datetime.now),
    )

def upgrade():
    metadata.create_all()

def downgrade():
    metadata.drop_all()

