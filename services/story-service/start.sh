#!/bin/sh
# Startup script for Story Service
# Ensures shared libraries are in Python path

export PYTHONPATH="/app/shared:${PYTHONPATH}"
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-config src/logging_config.json
