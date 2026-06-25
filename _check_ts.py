from datetime import datetime, timezone
ts = datetime.fromisoformat('2026-06-05T05:32:30.981245+00:00')
now = datetime.now(timezone.utc)
print('elapsed=%.0f' % (now - ts).total_seconds())
