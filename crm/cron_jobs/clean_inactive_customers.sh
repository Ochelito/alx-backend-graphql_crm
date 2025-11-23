#!/bin/bash
# Shell script to delete inactive customers with no orders in the past year
# Logs the number of deleted customers to /tmp/customer_cleanup_log.txt

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Get number of customers to delete using count()
DELETED_COUNT=$(python3 manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer

cutoff_date = timezone.now() - timedelta(days=365)
customers_to_delete = Customer.objects.filter(order__isnull=True, created_at__lte=cutoff_date)
print(customers_to_delete.count())
customers_to_delete.delete()
")

echo \"$TIMESTAMP - Deleted $DELETED_COUNT inactive customers\" >> /tmp/customer_cleanup_log.txt
