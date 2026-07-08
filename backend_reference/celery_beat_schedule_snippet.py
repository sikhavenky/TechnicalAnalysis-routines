"""
Add these entries to CELERY_BEAT_SCHEDULE in your Django settings.py.
Times are illustrative - keep fetch comfortably before, and save-output
comfortably after, the routine's actual scheduled time
(currently 09:00 GMT+5:30 / Asia/Kolkata).
"""

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "fetch-technicals-input-daily": {
        "task": "yourapp.tasks.fetch_and_push_technicals_input",
        "schedule": crontab(hour=8, minute=30),  # Asia/Kolkata, ~30 min before the routine
    },
    "save-technicals-output-daily": {
        "task": "yourapp.tasks.save_technicals_output_to_db",
        "schedule": crontab(hour=9, minute=45),  # Asia/Kolkata, ~45 min after the routine starts
    },
}
