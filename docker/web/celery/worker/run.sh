#!/bin/sh

set -euo pipefail

celery -A gnosis_safe_push_service.taskapp worker -l INFO
