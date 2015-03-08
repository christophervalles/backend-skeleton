import json
import logging
import os
import threading
import datetime

import peewee
from passlib.apps import custom_app_context as pwd_context

from src import settings


class Database(object):
    def __init__(self):
        self.database_config = dict(settings.DATABASE_CONFIG)
        self.database_name = self.database_config.pop('name')
        self.database = peewee.PostgresqlDatabase(self.database_name, **self.database_config)
        self.app = None
        self.pid = os.getpid()

    def init_app(self, app):
        self.app = app
        self.register_handlers()

    def connect_db(self):
        self._check_pid()
        self.database.connect()

    def close_db(self, exc):
        self._check_pid()
        if not self.database.is_closed():
            self.database.close()

    def _check_pid(self):
        current_pid = os.getpid()
        if self.pid != current_pid:
            logging.info("New pid detected (%d!=%d); resetting database lock.", self.pid, current_pid)
            self.pid = os.getpid()
            self.database._conn_lock = threading.Lock()

    def register_handlers(self):
        self.app.before_request(self.connect_db)
        self.app.teardown_request(self.close_db)


db = Database()


class BaseModel(peewee.Model):
    class Meta:
        database = db.database

    @classmethod
    def get_by_id(cls, model_id):
        return cls.get(cls.id == model_id)

    @classmethod
    def all(cls):
        return cls.select().order_by(cls.id.desc())


class User(BaseModel):
    id = peewee.PrimaryKeyField()
    name = peewee.CharField(max_length=320)
    email = peewee.CharField(max_length=320, index=True, unique=True)
    password_hash = peewee.CharField(max_length=128, null=True)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)

    class Meta:
        db_table = 'users'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self._allowed_tables = None

    @classmethod
    def get_by_email(cls, email):
        return cls.get(cls.email == email)

    def __unicode__(self):
        return '%r, %r' % (self.name, self.email)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return self.password_hash and pwd_context.verify(password, self.password_hash)


class Event(BaseModel):
    user = peewee.ForeignKeyField(User, related_name="events")
    action = peewee.CharField()
    object_type = peewee.CharField()
    object_id = peewee.CharField(null=True)
    additional_properties = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)

    class Meta:
        db_table = 'events'

    def __unicode__(self):
        return u"%s,%s,%s,%s" % (self._data['user'], self.action, self.object_type, self.object_id)

    @classmethod
    def record(cls, event):
        user = event.pop('user_id')
        action = event.pop('action')
        object_type = event.pop('object_type')
        object_id = event.pop('object_id', None)

        created_at = datetime.datetime.utcfromtimestamp(event.pop('timestamp'))
        additional_properties = json.dumps(event)

        event = cls.create(user=user, action=action, object_type=object_type, object_id=object_id,
                           additional_properties=additional_properties, created_at=created_at)

        return event

# THIS IS AN EXAMPLE OF HOW TO ALLOW THE CONTROLLER TO RETRIEVE RELATED MODELS
# class Visualization(BaseModel):
#     id = peewee.PrimaryKeyField()
#     type = peewee.CharField(max_length=100)
#     query = peewee.ForeignKeyField(Query, related_name='visualizations')
#     name = peewee.CharField(max_length=255)
#     description = peewee.CharField(max_length=4096, null=True)
#     options = peewee.TextField()
#     created_at = peewee.DateTimeField(default=datetime.datetime.now)
#
#     class Meta:
#         db_table = 'visualizations'
#
#     def to_dict(self, with_query=True):
#         d = {
#             'id': self.id,
#             'type': self.type,
#             'name': self.name,
#             'description': self.description,
#             'options': json.loads(self.options),
#             }
#
#         # THIS IS THE IMPORTANT BIT TO ACCESS FK DATA AND RETURN IT EMBEDDED <------------------- HERE
#         if with_query:
#             d['query'] = self.query.to_dict()
#
#         return d
#
#     def __unicode__(self):
#         return u"%s %s" % (self.id, self.type)


all_models = (User, Event)


def create_db(create_tables, drop_tables):
    db.connect_db()

    for model in all_models:
        if drop_tables and model.table_exists():
            # TODO: submit PR to peewee to allow passing cascade option to drop_table.
            db.database.execute_sql('DROP TABLE %s CASCADE' % model._meta.db_table)

        if create_tables and not model.table_exists():
            model.create_table()

    db.close_db(None)