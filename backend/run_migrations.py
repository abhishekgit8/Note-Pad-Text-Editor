import os
import sys
from alembic import command
from alembic.config import Config

# ensure backend path
here = os.path.dirname(__file__)
config = Config(os.path.join(here, 'alembic.ini'))
# make sure alembic picks up DATABASE_URL from environment
print('Running Alembic migrations...')
command.upgrade(config, 'head')
print('Migrations complete.')
