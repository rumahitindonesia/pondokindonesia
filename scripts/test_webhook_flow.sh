#!/bin/bash
# Script untuk test webhook flow di VPS

echo "========================================="
echo "  WEBHOOK FLOW TEST"
echo "========================================="

# 1. Check if Django is running
echo -e "\n[1/4] Checking Django service..."
if systemctl is-active --quiet gunicorn; then
    echo "✅ Gunicorn is running"
else
    echo "❌ Gunicorn is NOT running"
    echo "   Run: sudo systemctl start gunicorn"
fi

# 2. Check recent logs
echo -e "\n[2/4] Checking recent webhook logs..."
echo "Last 10 webhook-related log entries:"
tail -100 /home/triyono/pondok-django/logs/django.log 2>/dev/null | grep -E '\[FORM|\[LEAD|\[AI|\[GREETING|\[CS NOTIF|webhook_whatsapp' | tail -10 || echo "No logs found"

# 3. Run diagnostic script
echo -e "\n[3/4] Running diagnostic checks..."
cd /home/triyono/pondok-django
.venv/bin/python scripts/debug_webhook.py

# 4. Show webhook URL
echo -e "\n[4/4] Webhook URL Configuration:"
echo "Make sure StarSender webhook is set to:"
echo "  https://pondokindonesia.com/webhook/whatsapp/"
echo "  or"
echo "  https://pondokindonesia.com/webhook/whatsapp/<tenant_slug>/"

echo -e "\n========================================="
echo "  TEST COMPLETE"
echo "========================================="
