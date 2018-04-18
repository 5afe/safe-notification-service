#!/bin/sh

set -euo pipefail

export CELERY_BROKER_URL="${REDIS_URL}"
celery -A gnosis_safe_push_service.taskapp worker -l INFO
