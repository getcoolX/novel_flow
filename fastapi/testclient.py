class Response:
    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class TestClient:
    __test__ = False
    def __init__(self, app):
        self.app = app

    def get(self, path: str) -> Response:
        status_code, payload = self.app.handle_get(path)
        return Response(status_code=status_code, payload=payload)
