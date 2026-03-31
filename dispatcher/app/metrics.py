import time
from prometheus_client import Counter, Histogram, Gauge

# Traffic Counter: Servislere giden toplam istek sayısı ve statüsü
REQUEST_COUNT = Counter(
    "dispatcher_requests_total", 
    "Total proxy requests via Dispatcher", 
    ["method", "service", "status"]
)

# Latency Histogram: İsteklerin saniye cinsinden süresi
REQUEST_LATENCY = Histogram(
    "dispatcher_request_duration_seconds", 
    "Request duration in seconds",
    ["method", "service", "status"]
)

# Active Connections Gauge (Opsiyonel ama iyi durur)
ACTIVE_REQUESTS = Gauge(
    "dispatcher_active_requests", 
    "Number of requests currently being processed"
)

# Anti-pattern "Log Table" Gauge (Grafana'daki Detaylı Log Tablosu algoritması için spoof)
# Value will always be 1, but labels contain the log details
LOG_ENTRY = Gauge(
    "dispatcher_log_entry",
    "Pseudo log entry for Grafana Table",
    ["timestamp", "method", "path", "status", "duration_ms"]
)
