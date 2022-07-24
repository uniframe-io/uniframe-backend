import os
from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

from server.settings import API_SETTING

from server.apps.user.models import User
from server.apps.dataset.models import (
    Dataset,
    DatasetShareGroup,
    DatasetShareUser,
    PublicDataset,
)
from server.apps.group.models import Group, GroupMembers
from server.apps.media.models import Media
from server.apps.nm_task.models import AbcXyzTask, AbcXyzTaskRunHistory
from server.apps.oauth.models import OAuth2User, VerificationCode
from server.apps.permission.models import LocalDeployUser

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

from server.libs.db.sqlalchemy import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# https://stackoverflow.com/questions/22178339/is-it-possible-to-store-the-alembic-connect-string-outside-of-alembic-ini


def get_url():
    if os.environ.get("API_RUN_LOCATION") == "minikube":
        url = "postgresql://postgres:postgres@postgresql/nm"
    elif os.environ.get("API_RUN_LOCATION") == "test":
        url = API_SETTING.SQLALCHEMY_DATABASE_PYTEST_URL
    else:
        url = "postgresql://%s:%s@%s/%s" % (
            os.getenv("POSTGRES_USER", "vagrant"),
            os.getenv("POSTGRES_PASSWORD", "vagrant"),
            os.getenv("POSTGRES_HOST", "db"),
            os.getenv("POSTGRES_DB", "vagrant"),
        )
    return url

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(get_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
