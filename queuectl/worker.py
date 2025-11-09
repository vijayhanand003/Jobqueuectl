# queuectl/worker.py
import multiprocessing
import time
import os
import signal
import psutil
from .db import get_pending_job, list_jobs
from .job import Job

# Global list to track worker processes
WORKER_PROCESSES = []

def worker_loop(worker_id):
    pid = os.getpid()
    print(f"[Worker {worker_id}] Started (PID: {pid})")
    while True:
        try:
            job_data = get_pending_job(pid)
            if job_data:
                print(f"[Worker {worker_id}] Executing job {job_data['id']}: {job_data['command']}")
                job = Job(job_data)
                job.execute()
            else:
                time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Worker {worker_id}] Error: {e}")
            time.sleep(1)

def start_workers(count=1):
    global WORKER_PROCESSES
    if WORKER_PROCESSES:
        print("Workers already running!")
        return

    for i in range(count):
        p = multiprocessing.Process(target=worker_loop, args=(i,))
        p.start()
        WORKER_PROCESSES.append(p)
    print(f"Started {count} worker(s)")

def stop_workers():
    global WORKER_PROCESSES
    print("Stopping workers gracefully...")
    for p in WORKER_PROCESSES[:]:
        if p.is_alive():
            p.terminate()
            p.join(timeout=10)
            if p.is_alive():
                p.kill()
    WORKER_PROCESSES.clear()
    print("All workers stopped.")

# Handle Ctrl+C globally
def signal_handler(sig, frame):
    print("\nCtrl+C received. Shutting down...")
    stop_workers()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)