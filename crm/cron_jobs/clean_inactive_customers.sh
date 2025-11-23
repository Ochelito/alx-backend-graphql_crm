#!/bin/bash
# Shell script to delete inactive customers with no orders in the past year
# Logs the number of deleted customers to /tmp/customer_cleanup_log.txt

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Delete inactive customers using Django ORM and get the number of deleted objects
DELETED_COUNT=$(python3 manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer

cutoff_date = timezone.now() - timedelta(days=365)
deleted, _ = Customer.objects.filter(order__isnull=True, created_at__lte=cutoff_date).delete()
print(deleted)
")

echo \"$TIMESTAMP - Deleted $DELETED_COUNT inactive customers\" >> /tmp/customer_cleanup_log.txt
