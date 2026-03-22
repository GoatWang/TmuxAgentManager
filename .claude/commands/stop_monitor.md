# Stop Monitor

Stop the recurring worker agent monitor loop.

## Procedure

1. List all active cron jobs using `CronList`
2. Find the job related to monitoring the worker agent session
3. Delete it using `CronDelete` with the job ID
4. Confirm the loop has been stopped
