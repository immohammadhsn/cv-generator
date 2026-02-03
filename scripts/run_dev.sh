#!/usr/bin/env bash
set -euo pipefail

uvicorn cv_generator.api_prod:app --reload --host 0.0.0.0 --port 8000
