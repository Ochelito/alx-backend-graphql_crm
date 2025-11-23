# CRM Weekly Report Setup

## 1. Install Redis and dependencies
pip install -r requirements.txt
sudo apt install redis-server

## 2. Run Django migrations
python manage.py migrate

## 3. Start Celery worker
celery -A crm worker -l info

## 4. Start Celery Beat
celery -A crm beat -l info

## 5. Verify Logs
Check /tmp/crm_report_log.txt for weekly report entries.
