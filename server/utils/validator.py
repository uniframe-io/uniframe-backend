import re

RESOURCE_NAME_PATTERN = re.compile(r"^[a-zA-Z]+[a-zA-Z0-9_\-\s]*$")

DEMO_ACCOUNT_ALLOWED_ROUTE_PATTERN = re.compile(
    r"^/api/v1/(tasks/nm/[0-9]*/match$|logout$|test-token$)"
)


def validate_resource_name(name: str) -> bool:
    if not re.match(RESOURCE_NAME_PATTERN, name):
        return False
    else:
        return True


def validate_demo_account_route(patch: str) -> bool:
    if not re.match(DEMO_ACCOUNT_ALLOWED_ROUTE_PATTERN, patch):
        return False
    else:
        return True
