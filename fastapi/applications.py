from collections.abc import Callable


class FastAPI:
    def __init__(self, title: str | None = None):
        self.title = title
        self._routes: dict[str, Callable[[], object]] = {}

    def get(self, path: str):
        def decorator(func: Callable[[], object]):
            self._routes[path] = func
            return func

        return decorator

    def handle_get(self, path: str):
        handler = self._routes.get(path)
        if handler is None:
            return 404, {"detail": "Not Found"}
        return 200, handler()
