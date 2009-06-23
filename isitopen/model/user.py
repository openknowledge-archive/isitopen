import datetime

from meta import *

import uuid
def make_uuid():
    return str(uuid.uuid4())

user_table = Table('user', metadata,
        Column('id', types.String(36), default=make_uuid, primary_key=True),
        Column('email', types.UnicodeText),
        Column('username', types.UnicodeText),
        )

class User(object):
    pass

mapper(User, user_table,
    order_by=user_table.c.id)

