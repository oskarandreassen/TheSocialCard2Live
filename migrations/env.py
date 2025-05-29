import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context
from sqlalchemy import engine_from_config, pool

# Läs in konfiguration och logginställningar från alembic.ini
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

#
# Helpers to plocka upp Flask-SQLAlchemy motorn och metadata
#
def get_engine():
    try:
        # Flask-SQLAlchemy < 3
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # Flask-SQLAlchemy >= 3
        return current_app.extensions['migrate'].db.engine

def get_engine_url():
    url = get_engine().url
    try:
        return url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError:
        return str(url).replace('%', '%%')

# Sätt sqlalchemy.url i Alembic till exakt samma URL som flask-appen
config.set_main_option('sqlalchemy.url', get_engine_url())

# Hämta metadata för autogenerering
def get_metadata():
    db = current_app.extensions['migrate'].db
    if hasattr(db, 'metadatas'):
        return db.metadatas[None]
    return db.metadata

#
# Offline migrations (ingen live-connection)
#
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

#
# Online migrations (med echo=True så vi ser all SQL)
#
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        echo=True,               # <-- logga all SQL som körs
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            compare_type=True,   # visar också typ-ändringar om det behövs
        )

        with context.begin_transaction():
            context.run_migrations()

#
# Kör rätt variant beroende på offline/online
#
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
