# tests/test_queuectl.py
import time
import os
from queuectl.db import init_db, enqueue_job, list_jobs, list_dlq, retry_dlq_job, get_conn
from queuectl.worker import start_workers, stop_workers

def run_tests():
    print("Running QueueCTL Tests on Windows...\n")

    # --- FORCE CLEAN DB ---
    DB_PATH = "queuectl.db"
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Deleted old {DB_PATH}")

    init_db()
    print("Fresh database initialized.\n")

    # --- Test 1: Successful job ---
    print("Test 1: Job should complete successfully")
    enqueue_job({
        "id": "test-success",
        "command": "cmd /c echo Hello from QueueCTL"
    })
    print("Enqueued success job")

    start_workers(1)
    print("Started 1 worker")

    time.sleep(5)
    stop_workers()

    completed = [j for j in list_jobs('completed') if j['id'] == 'test-success']
    if completed:
        print("Test 1 PASSED")
    else:
        print("Test 1 FAILED")
        print("Jobs:", list_jobs())
        exit(1)

    # --- Test 2: Failed → Retry → DLQ ---
    print("\nTest 2: Failed job should go to DLQ")
    enqueue_job({
        "id": "test-fail",
        "command": "cmd /c exit 1"
    })
    print("Enqueued failing job")

    start_workers(1)
    print("Started worker for retry test")
    print("Waiting 18s for retries (2+4+8)...")
    time.sleep(18)
    stop_workers()

    dlq_jobs = list_dlq()
    in_dlq = any(j['id'] == 'test-fail' for j in dlq_jobs)
    if in_dlq:
        print("Test 2 PASSED")
    else:
        print("Test 2 FAILED")
        print("DLQ:", dlq_jobs)
        print("Pending:", list_jobs('pending'))
        exit(1)

    # --- Test 3: DLQ retry (MODIFY TO SUCCEED) ---
    print("\nTest 3: Retry from DLQ")
    
    # Change command in DLQ to succeed
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE dlq SET command = 'cmd /c echo Retried and succeeded' WHERE id = 'test-fail'")
    conn.commit()
    conn.close()

    retry_dlq_job("test-fail")
    print("Job retried from DLQ (now succeeds)")

    start_workers(1)
    time.sleep(5)
    stop_workers()

    completed_retry = [j for j in list_jobs('completed') if j['id'] == 'test-fail']
    if completed_retry:
        print("Test 3 PASSED")
    else:
        print("Test 3 FAILED")
        exit(1)

    # --- Test 4: Persistence ---
    print("\nTest 4: Jobs persist after restart")
    init_db()
    persistent = list_jobs('completed')
    if any(j['id'] in ['test-success', 'test-fail'] for j in persistent):
        print("Test 4 PASSED")
    else:
        print("Test 4 FAILED")
        exit(1)

    print("\nALL 4 TESTS PASSED!")
    print("QueueCTL is ready!")

# REQUIRED FOR WINDOWS
if __name__ == '__main__':
    run_tests()