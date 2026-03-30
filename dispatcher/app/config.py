import os

# Yönlendirme tablosu: URL'e göre
ROUTES = {
    "/auth":     ("AUTH_SERVICE_URL",     "http://localhost:8001"),
    "/delivery": ("DELIVERY_SERVICE_URL", "http://localhost:8002"),
    "/tracking": ("TRACKING_SERVICE_URL", "http://localhost:8003"),
}


def resolve_upstream(path: str) -> str | None:
    """Gelen isteğe karşılık gelen upstream URL'yi döner.
    Eşleşen rota yoksa None döner."""

    for prefix, (env_var, default) in ROUTES.items():
        if path.startswith(prefix):
            base_url = os.getenv(env_var, default)
            return base_url + path
    return None
