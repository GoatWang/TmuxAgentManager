# Stop Monitor

Stop any legacy recurring worker monitor loop that may still exist from older behavior.
New monitoring should be manual sleep-and-wait supervision, not cron.

## Procedure

1. List all active cron jobs using `CronList`
2. Find any job related to monitoring the worker agent session
3. Delete it using `CronDelete` with the job ID
4. Confirm the legacy loop has been stopped
5. Report that worker monitoring should now use manual sleep-and-wait checks instead of cron
