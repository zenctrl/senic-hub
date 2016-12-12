from colander import null
from pyramid.security import Allow
from pyramid.security import Everyone
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension


metadata = MetaData()
db_session = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


class Base(object):
    """ the base class that all security aware content should subclass.
    """

    __acl__ = [
        (Allow, Everyone, ['view']),
    ]

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @property
    def columns(self):
        """ Return names of all known database columns. """
        return self.__mapper__.columns.keys()

    def __iter__(self):
        """ Iterate over all columns and return existing values. """
        values = vars(self)
        for attr in self.columns:
            if attr in values:
                yield attr, values[attr]

    def __json__(self, request=None):
        return dict(self)

    @property
    def data(self):
        return self.__json__()

    def add(self, **data):
        self.update(**data)
        db_session.add(self)
        db_session.flush()

    def update(self, **data):
        """ Iterate over all columns and set values from data. """
        for attr in self.columns:
            if attr in data and data[attr] is not null:
                setattr(self, attr, data[attr])

    def __repr__(self):     # pragma: no cover
        return '<%s %s>' % (self.__class__.__name__, self.id)


Base = declarative_base(cls=Base)
Base.metadata = metadata
Base.query = db_session.query_property()


class Root(object):
    """ Root object with default permissions. """

    __acl__ = [
        (Allow, Everyone, ['view']),
    ]
