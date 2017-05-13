from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
import config


logger = logging.getLogger("turkic.database")

Base = declarative_base()

try:
    import config
except ImportError:
    session = None
    Session = None
else:
    engine = create_engine(config.database, pool_recycle = 3600)

    Session = sessionmaker(bind=engine)
    session = scoped_session(Session)

    # def renew_session():
    #     global session
    #     session = scoped_session(Session)
    #     return session

    def connect():
        """
        Generates a database connection.
        """
        return Session()

    def install():
        """
        Installs the database, but does not drop existing tables.
        """
        from vatic.models import *
        from tpod_models import *

        Base.metadata.create_all(engine)

    def reinstall():
        """
        Reinstalls the database by dropping all existing tables. Actual data is
        not migrated!
        """
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)