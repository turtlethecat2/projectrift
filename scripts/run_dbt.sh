#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/dbt_project"
export DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-.}"

dbt debug
dbt run
