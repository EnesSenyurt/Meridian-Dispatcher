import pytest
import os
import importlib
from unittest.mock import patch


class TestRoutingTableDefaults:

    def test_auth_prefix_resolves_to_default_url(self):
        from app.config import resolve_upstream
        url = resolve_upstream("/auth/login")
        assert url == "http://localhost:8001/auth/login"

    def test_delivery_prefix_resolves_to_default_url(self):
        from app.config import resolve_upstream
        url = resolve_upstream("/delivery/orders")
        assert url == "http://localhost:8002/delivery/orders"

    def test_tracking_prefix_resolves_to_default_url(self):
        from app.config import resolve_upstream
        url = resolve_upstream("/tracking/shipments")
        assert url == "http://localhost:8003/tracking/shipments"

    def test_unknown_prefix_returns_none(self):
        from app.config import resolve_upstream
        result = resolve_upstream("/payments/invoice")
        assert result is None

    def test_root_path_returns_none(self):
        from app.config import resolve_upstream
        result = resolve_upstream("/")
        assert result is None


class TestRoutingTableEnvOverride:

    def test_auth_url_overridden_by_env(self):
        with patch.dict(os.environ, {"AUTH_SERVICE_URL": "http://auth-service:8000"}):
            import app.config as cfg
            importlib.reload(cfg)
            url = cfg.resolve_upstream("/auth/login")
        assert url == "http://auth-service:8000/auth/login"

    def test_delivery_url_overridden_by_env(self):
        with patch.dict(os.environ, {"DELIVERY_SERVICE_URL": "http://delivery-service:8000"}):
            import app.config as cfg
            importlib.reload(cfg)
            url = cfg.resolve_upstream("/delivery/shipments")
        assert url == "http://delivery-service:8000/delivery/shipments"

    def test_tracking_url_overridden_by_env(self):
        with patch.dict(os.environ, {"TRACKING_SERVICE_URL": "http://tracking-service:8000"}):
            import app.config as cfg
            importlib.reload(cfg)
            url = cfg.resolve_upstream("/tracking/live")
        assert url == "http://tracking-service:8000/tracking/live"

    def test_deep_path_is_preserved(self):
        with patch.dict(os.environ, {"AUTH_SERVICE_URL": "http://auth-service:8000"}):
            import app.config as cfg
            importlib.reload(cfg)
            url = cfg.resolve_upstream("/auth/v2/users/42/profile")
        assert url == "http://auth-service:8000/auth/v2/users/42/profile"
