#!/bin/bash

set -euo pipefail

exec celery -A safe_notification_service.taskapp worker -l INFO
