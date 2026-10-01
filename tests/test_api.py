from app.main import app


def test_root_endpoint():
    route = next(route for route in app.routes if getattr(route, "path", None) == "/")
    assert route.endpoint()["status"] == "running"


def test_health_endpoint():
    route = next(route for route in app.routes if getattr(route, "path", None) == "/health")
    assert route.endpoint()["status"] == "healthy"
