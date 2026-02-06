#!/usr/bin/env python3
"""
Simple API health check for CI.

Checks key endpoints under BASE_URL (defaults to http://localhost:8000)
and exits non-zero on failures. Designed to be lightweight and dependency-free.
"""
import json
import os
import sys
import urllib.request
import urllib.error


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


def fetch_json(path: str):
    url = f"{BASE_URL.rstrip('/')}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        body = resp.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response from {url}")


def check_portfolio():
    data = fetch_json("/api/v1/portfolio/")
    # Expect summary and stocks keys
    if not isinstance(data, dict) or "summary" not in data or "stocks" not in data:
        raise RuntimeError("portfolio response missing keys: summary/stocks")


def check_history():
    data = fetch_json("/api/v1/portfolio/history/?period=all")
    # Expect arrays
    required = ["periods", "totalProfits", "totalValues", "totalCosts"]
    if not isinstance(data, dict) or any(k not in data for k in required):
        raise RuntimeError("history response missing required arrays")


def check_records():
    data = fetch_json("/api/v1/data/records/?start_month=2023-01&end_month=2023-12")
    if not isinstance(data, dict) or "data" not in data:
        raise RuntimeError("data/records response missing 'data'")


def main():
    checks = [
        ("portfolio", check_portfolio),
        ("history", check_history),
        ("records", check_records),
    ]
    failed = []
    for name, fn in checks:
        try:
            fn()
            print(f"✅ {name} OK")
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            failed.append(name)
    if failed:
        print(f"One or more checks failed: {', '.join(failed)}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()

