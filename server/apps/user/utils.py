from server.apps.user.schemas import UserDO


def is_free_user(user: UserDO) -> bool:
    # TODO: how to define a free user and a premium user?
    return not user.is_superuser


def get_user_premium_type(user: UserDO) -> str:
    # TODO: change the return value to a enum type
    if is_free_user(user):
        return "free-user"
    else:
        return "super-user"
