#!/bin/bash

set -euo pipefail

celery -A safe_notification_service.taskapp worker -l INFO
