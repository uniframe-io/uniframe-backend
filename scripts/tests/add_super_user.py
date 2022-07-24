"""
Startup docker by `make docker-backend`
Run `docker-compose exec server /bin/bash -c 'python scripts/tests/add_super_user.py super@email.com 123456'`
"""

import sys

from server.api.main import app  # noqa: F401

# from server.api.main import app
from server.apps.user.crud import USER_CRUD
from server.apps.user.schemas import LOGIN_TYPE, UserCreateDO
from server.core import security
from server.libs.db.sqlalchemy import db

if __name__ == "__main__":
    superuser_email = sys.argv[1]
    superuser_password = sys.argv[2]
    print(
        f"Setup superuser email [superuser_email] and password [{superuser_password}]"
    )

    user = UserCreateDO(
        email=superuser_email,
        hashed_password=security.get_password_hash(superuser_password),
        full_name="super user",
        login_type=LOGIN_TYPE.EMAIL,
    )

    with db():
        superuser = USER_CRUD.create_user(user, is_superuser=True)
        print(superuser)
