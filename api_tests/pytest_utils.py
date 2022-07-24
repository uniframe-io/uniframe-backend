import json

from requests.models import Response

from server.core.exception import NmBaseException


def assert_endpoint_response(response: Response, err: NmBaseException) -> None:
    """Assert EXCEPTION_LIB error

    :param response: TestClient post/get/... return value
    :type response: Response
    :param err: EXCEPTION_LIB member
    :type err: NmBaseException
    """
    assert response.status_code == 418

    response_body = json.loads(response.content)
    assert response_body["error_domain"] == err.error_domain
