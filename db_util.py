from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging
import config
from sqlalchemy import exc

logger = logging.getLogger("turkic.database")

Base = declarative_base()

try:
    import config
except ImportError:
    session = None
    Session = None
else:

    # set listener for disconnect, then the pool will replace it with new one
    class LookLively(object):
        """Ensures that MySQL connections checked out of the pool are alive."""

        def checkout(self, dbapi_con, con_record, con_proxy):
            try:
                try:
                    dbapi_con.ping(False)
                except TypeError:
                    dbapi_con.ping()
            except dbapi_con.OperationalError, ex:
                if ex.args[0] in (2006, 2013, 2014, 2045, 2055):
                    raise exc.DisconnectionError()
                else:
                    raise


    engine = create_engine(config.database, pool_recycle = 3600, pool_size=100, listeners=[LookLively()])

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

    def renew_session():
        global session
        session = connect()

    def close_session():
        global session
        session.close()

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