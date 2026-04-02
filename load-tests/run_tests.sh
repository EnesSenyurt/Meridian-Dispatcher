#!/usr/bin/env bash
set -euo pipefail

HOST="${LOCUST_HOST:-http://dispatcher:8000}"
LOCUSTFILE="${LOCUSTFILE:-/locust/locustfile.py}"
RESULTS_DIR="${RESULTS_DIR:-/locust/results}"
RUN_TIME="${RUN_TIME:-60s}"
COOLDOWN="${COOLDOWN:-10}"

mkdir -p "$RESULTS_DIR"

USER_COUNTS=(50 100 200 500)

# ------------------------------------------------------------------ #
# Yardımcı: CSV'den özet satırı oku ve terminale bas
# ------------------------------------------------------------------ #
print_summary_row() {
    local users=$1
    local stats_csv="$RESULTS_DIR/locust_${users}_stats.csv"

    if [[ ! -f "$stats_csv" ]]; then
        printf "| %-5s | %-8s | %-11s | %-8s | %-8s | %-6s | %-7s |\n" \
            "$users" "N/A" "N/A" "N/A" "N/A" "N/A" "N/A"
        return
    fi

    # Aggregated satırı bul (son satır genellikle "Aggregated"dır)
    local agg
    agg=$(grep -i "aggregated" "$stats_csv" | tail -1 || true)

    if [[ -z "$agg" ]]; then
        # Aggregated yoksa tüm satırların ortalamasını alma yerine uyarı ver
        printf "| %-5s | %-8s | %-11s | %-8s | %-8s | %-6s | %-7s |\n" \
            "$users" "N/A" "N/A" "N/A" "N/A" "N/A" "N/A"
        return
    fi

    # Locust stats CSV sütun sırası (v2.x):
    # Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,
    # Min Response Time,Max Response Time,Average Content Size,Requests/s,
    # Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%
    local req_count failure_count avg med p95 p99 rps fail_s

    IFS=',' read -ra cols <<< "$agg"

    req_count="${cols[2]:-0}"
    failure_count="${cols[3]:-0}"
    med="${cols[4]:-0}"
    avg="${cols[5]:-0}"
    rps="${cols[9]:-0}"
    fail_s="${cols[10]:-0}"
    p95="${cols[16]:-0}"
    p99="${cols[18]:-0}"

    # Hata yüzdesi
    local err_pct="0.00"
    if [[ "$req_count" -gt 0 ]] 2>/dev/null; then
        err_pct=$(awk "BEGIN {printf \"%.2f\", ($failure_count/$req_count)*100}")
    fi

    printf "| %-5s | %-8s | %-11s | %-8s | %-8s | %-6s | %-7s |\n" \
        "$users" \
        "$(printf "%.0f" "$avg" 2>/dev/null || echo "$avg")" \
        "$(printf "%.0f" "$med" 2>/dev/null || echo "$med")" \
        "$(printf "%.0f" "$p95" 2>/dev/null || echo "$p95")" \
        "$(printf "%.0f" "$p99" 2>/dev/null || echo "$p99")" \
        "$(printf "%.1f" "$rps" 2>/dev/null || echo "$rps")" \
        "${err_pct}%"
}

# ------------------------------------------------------------------ #
# Başlık
# ------------------------------------------------------------------ #
echo ""
echo "========================================================"
echo "  Meridian Dispatcher - Yük Testi"
echo "  Host: $HOST"
echo "  Süre: $RUN_TIME / test"
echo "========================================================"
echo ""

# ------------------------------------------------------------------ #
# Testleri sırayla çalıştır
# ------------------------------------------------------------------ #
for users in "${USER_COUNTS[@]}"; do
    spawn_rate=$(( users / 10 ))
    [[ "$spawn_rate" -lt 1 ]] && spawn_rate=1

    csv_prefix="$RESULTS_DIR/locust_${users}"

    echo ">>> Test başlıyor: $users kullanıcı | spawn rate: ${spawn_rate}/s | süre: $RUN_TIME"

    locust \
        --headless \
        --host "$HOST" \
        --locustfile "$LOCUSTFILE" \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$RUN_TIME" \
        --csv "$csv_prefix" \
        --csv-full-history \
        --exit-code-on-error 0 \
        2>&1 | tail -5

    echo "    Sonuçlar kaydedildi: ${csv_prefix}_stats.csv"
    echo ""

    if [[ "$users" != "${USER_COUNTS[-1]}" ]]; then
        echo "    Servisler toparlanıyor... $COOLDOWN saniye bekleniyor."
        sleep "$COOLDOWN"
        echo ""
    fi
done

# ------------------------------------------------------------------ #
# Özet tablo
# ------------------------------------------------------------------ #
echo ""
echo "========================================================"
echo "  TEST SONUÇLARI ÖZETİ"
echo "========================================================"
printf "| %-5s | %-8s | %-11s | %-8s | %-8s | %-6s | %-7s |\n" \
    "Users" "Avg (ms)" "Median (ms)" "P95 (ms)" "P99 (ms)" "RPS" "Error %"
printf "|%s|%s|%s|%s|%s|%s|%s|\n" \
    "-------" "----------" "-------------" "----------" "----------" "--------" "---------"

for users in "${USER_COUNTS[@]}"; do
    print_summary_row "$users"
done

echo ""
echo "Detaylı CSV sonuçları: $RESULTS_DIR/"
echo ""

# Python özet scripti varsa çalıştır
if command -v python3 &>/dev/null && [[ -f "/locust/summarize_results.py" ]]; then
    python3 /locust/summarize_results.py
fi
