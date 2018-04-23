#!/bin/sh

set -euo pipefail

celery -A safe_push_service.taskapp worker -l INFO
