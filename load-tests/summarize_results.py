#!/usr/bin/env python3
"""
Locust CSV çıktılarını okuyarak özet tablo oluşturur.
Hem terminale basar hem load-tests/results/summary.md olarak kaydeder.
"""

import csv
import os
import sys

RESULTS_DIR = os.environ.get("RESULTS_DIR", os.path.join(os.path.dirname(__file__), "results"))
USER_COUNTS = [50, 100, 200, 500]


def parse_stats_csv(filepath: str) -> dict | None:
    """Locust stats CSV'den Aggregated satırını parse eder."""
    if not os.path.isfile(filepath):
        return None

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "").strip().lower()
            if name == "aggregated":
                return row
    return None


def safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def build_row(users: int) -> dict:
    csv_path = os.path.join(RESULTS_DIR, f"locust_{users}_stats.csv")
    row = parse_stats_csv(csv_path)

    if row is None:
        return {
            "users": users,
            "avg": "N/A",
            "median": "N/A",
            "p95": "N/A",
            "p99": "N/A",
            "rps": "N/A",
            "error_pct": "N/A",
        }

    req_count = safe_int(row.get("Request Count", 0))
    failure_count = safe_int(row.get("Failure Count", 0))
    avg = safe_float(row.get("Average Response Time", 0))
    median = safe_float(row.get("Median Response Time", 0))
    rps = safe_float(row.get("Requests/s", 0))

    # Percentile sütun adları Locust sürümüne göre değişebilir
    p95 = safe_float(
        row.get("95%") or row.get("95th Percentile Response Time") or 0
    )
    p99 = safe_float(
        row.get("99%") or row.get("99th Percentile Response Time") or 0
    )

    error_pct = (failure_count / req_count * 100) if req_count > 0 else 0.0

    return {
        "users": users,
        "avg": f"{avg:.0f}",
        "median": f"{median:.0f}",
        "p95": f"{p95:.0f}",
        "p99": f"{p99:.0f}",
        "rps": f"{rps:.1f}",
        "error_pct": f"{error_pct:.2f}%",
    }


def format_table(rows: list[dict]) -> str:
    header = (
        "| Users | Avg (ms) | Median (ms) | P95 (ms) | P99 (ms) | RPS  | Error % |\n"
        "|-------|----------|-------------|----------|----------|------|---------|\n"
    )
    lines = [header]
    for r in rows:
        line = (
            f"| {r['users']:<5} "
            f"| {r['avg']:<8} "
            f"| {r['median']:<11} "
            f"| {r['p95']:<8} "
            f"| {r['p99']:<8} "
            f"| {r['rps']:<4} "
            f"| {r['error_pct']:<7} |\n"
        )
        lines.append(line)
    return "".join(lines)


def main():
    rows = [build_row(u) for u in USER_COUNTS]
    table = format_table(rows)

    # Terminale bas
    print("\n========================================")
    print("  Meridian Dispatcher - Yük Testi Özeti")
    print("========================================\n")
    print(table)

    # Markdown olarak kaydet
    os.makedirs(RESULTS_DIR, exist_ok=True)
    summary_path = os.path.join(RESULTS_DIR, "summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Meridian Dispatcher - Yük Testi Sonuçları\n\n")
        f.write(table)
        f.write("\n> Otomatik olarak `summarize_results.py` tarafından oluşturuldu.\n")

    print(f"Özet kaydedildi: {summary_path}\n")


if __name__ == "__main__":
    main()
