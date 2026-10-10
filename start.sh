#!/usr/bin/env bash
# Railway: bot (polling) va Mini App API bitta konteynerda.
# Ikkalasidan biri to'xtasa konteyner chiqadi va Railway uni qayta ishga tushiradi.
set -u

python main.py &
uvicorn web_api:app --host 0.0.0.0 --port "${PORT:-8000}" &

wait -n
exit $?
