# Meridian-Dispatcher
```mermaid
graph TD
    Client((Mobil/Web İstemci)) -->|Tüm İstekler| Dispatcher

    subgraph "İç Ağ (Network Isolation)"
        Dispatcher[Dispatcher API Gateway]
        
        Auth[Auth Service]
        Delivery[Delivery Service]
        Tracking[Tracking Service]

        Dispatcher -.->|JSON| Auth
        Dispatcher -.->|JSON| Delivery
        Dispatcher -.->|JSON| Tracking
    end

    subgraph "İzole NoSQL Veri Tabanları"
        DB_Disp[(Redis - Log/Auth)]
        DB_Auth[(MongoDB - Users)]
        DB_Del[(MongoDB - Deliveries)]
        DB_Track[(Redis - Live Tracking)]
    end

    Dispatcher --> DB_Disp
    Auth --> DB_Auth
    Delivery --> DB_Del
    Tracking --> DB_Track

    subgraph "Monitoring Katmanı"
        Prometheus[Prometheus]
        Grafana[Grafana Dashboard]
        Prometheus --> Dispatcher
        Grafana --> Prometheus
    end