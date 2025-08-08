#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

curl_json() {
  local path="$1"
  http_code=$(curl -sS -o /tmp/resp.json -w "%{http_code}" -H 'Accept: application/json' "$BASE_URL$path")
  if [ "$http_code" != "200" ]; then
    echo "HTTP $http_code for $BASE_URL$path" >&2
    return 1
  fi
  cat /tmp/resp.json
}

ok=()
fail=()

echo "Checking $BASE_URL"

if jq . >/dev/null 2>&1 <(curl_json "/api/v1/portfolio/") && \
   jq -e '.summary and .stocks' >/dev/null < /tmp/resp.json; then
  echo "✅ portfolio OK"; ok+=(portfolio)
else
  echo "❌ portfolio FAILED"; fail+=(portfolio)
fi

if jq . >/dev/null 2>&1 <(curl_json "/api/v1/portfolio/history/?period=all") && \
   jq -e '.periods and .totalProfits and .totalValues and .totalCosts' >/dev/null < /tmp/resp.json; then
  echo "✅ history OK"; ok+=(history)
else
  echo "❌ history FAILED"; fail+=(history)
fi

if jq . >/dev/null 2>&1 <(curl_json "/api/v1/data/records/?start_month=2023-01&end_month=2023-12") && \
   jq -e '.data' >/dev/null < /tmp/resp.json; then
  echo "✅ records OK"; ok+=(records)
else
  echo "❌ records FAILED"; fail+=(records)
fi

if [ ${#fail[@]} -gt 0 ]; then
  echo "Failures: ${fail[*]}" >&2
  exit 1
fi
echo "All checks passed."

