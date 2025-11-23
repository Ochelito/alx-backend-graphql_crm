#!/bin/bash
# Shell script to delete inactive customers with no orders in the past year
# Logs the number of deleted customers to /tmp/customer_cleanup_log.txt

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

DELETED_COUNT=$(python3 manage.py shell -c "
from datetime import datetime, timedelta
from crm.models import Customer
from django.utils import timezone
cutoff_date = timezone.now() - timedelta(days=365)
deleted, _ = Customer.objects.filter(order__isnull=True, created_at__lte=cutoff_date).delete()
print(deleted)
")

echo \"$TIMESTAMP - Deleted $DELETED_COUNT inactive customers\" >> /tmp/customer_cleanup_log.txt
