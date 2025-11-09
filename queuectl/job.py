# queuectl/job.py
import subprocess
from .db import update_job, move_to_dlq, get_config
from .utils import calculate_backoff
from datetime import datetime, timedelta

class Job:
    def __init__(self, data):
        self.data = data

    def execute(self):
        try:
            result = subprocess.run(
                self.data['command'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # Prevent hanging
            )
            if result.returncode == 0:
                self.complete()
            else:
                print(f"Job {self.data['id']} failed: {result.stderr}")
                self.fail()
        except subprocess.TimeoutExpired:
            print(f"Job {self.data['id']} timed out")
            self.fail()
        except Exception as e:
            print(f"Job {self.data['id']} exception: {e}")
            self.fail()

    def complete(self):
        update_job(self.data['id'], {'state': 'completed', 'locked_by': None})

    def fail(self):
        attempts = self.data['attempts'] + 1
        max_retries = int(get_config('max_retries') or 3)
        if attempts > max_retries:
            move_to_dlq(self.data)
        else:
            base = int(get_config('backoff_base') or 2)
            delay = calculate_backoff(attempts, base)
            next_time = (datetime.utcnow() + timedelta(seconds=delay)).strftime("%Y-%m-%dT%H:%M:%SZ")
            update_job(self.data['id'], {
                'state': 'pending',
                'attempts': attempts,
                'next_attempt_at': next_time,
                'locked_by': None
            })