import uuid
import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

metadata = MetaData(migrate_engine)

def make_uuid():
    return str(uuid.uuid4())

pending_action_table = Table('pending_action', metadata,
    Column('id', String(36), default=make_uuid, primary_key=True),
    Column('type', Text),
    Column('data', Text),
    Column('timestamp', DateTime, default=datetime.datetime.now),
    )

user_table = Table('user', metadata, autoload=True)
user_columns = [
    Column('firstname', UnicodeText),
    Column('lastname', UnicodeText),
    Column('is_confirmed', Boolean, default=False),
    ]

def upgrade():
    pending_action_table.create()
    for col in user_columns:
        col.create(user_table)

def downgrade():
    raise NotImplementedError()

