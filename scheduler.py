from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.agent import run_cycle
from app.config import SCHEDULE_HOURS, TIMEZONE


def start_scheduler() -> None:
    scheduler = BlockingScheduler(timezone=TIMEZONE)
    for hour in SCHEDULE_HOURS:
        scheduler.add_job(run_cycle, CronTrigger(hour=hour, minute=0))
    print(f"Scheduler active for {SCHEDULE_HOURS} at timezone {TIMEZONE}")
    run_cycle()
    scheduler.start()


if __name__ == "__main__":
    start_scheduler()
