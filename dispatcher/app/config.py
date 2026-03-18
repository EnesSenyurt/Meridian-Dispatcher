import os

# Yönlendirme tablosu: URL öneki -> (env değişkeni adı, yerel geliştirme varsayılanı)
ROUTES = {
    "/auth":     ("AUTH_SERVICE_URL",     "http://localhost:8001"),
    "/delivery": ("DELIVERY_SERVICE_URL", "http://localhost:8002"),
    "/tracking": ("TRACKING_SERVICE_URL", "http://localhost:8003"),
}


def resolve_upstream(path: str) -> str | None:
    """
    Gelen istek yoluna karşılık gelen upstream URL'yi döner.
    Eşleşen rota yoksa None döner.
    os.getenv fonksiyon içinde çağrılır; bu sayede env değişkeni değişiklikleri anında yansır.
    """
    for prefix, (env_var, default) in ROUTES.items():
        if path.startswith(prefix):
            base_url = os.getenv(env_var, default)
            return base_url + path
    return None
