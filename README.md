# QueueCTL

**Production‑grade background job queue system (Windows-ready)**

A lightweight, CLI-driven job queue with retries, exponential backoff, Dead Letter Queue (DLQ), and full persistence — implemented in Python 3.11+ and built to work cleanly on Windows.

---

## Features

| Feature                                                  | Status |
| -------------------------------------------------------- | ------ |
| Enqueue jobs via CLI                                     | ✅ Done |
| Multiple parallel workers                                | ✅ Done |
| Exponential backoff (`backoff_base ** attempts` seconds) | ✅ Done |
| Dead Letter Queue (DLQ)                                  | ✅ Done |
| Retry jobs from DLQ                                      | ✅ Done |
| Full persistence across restarts                         | ✅ Done |
| Configurable via CLI (`max_retries`, `backoff_base`)     | ✅ Done |
| Clean, user-friendly CLI with help                       | ✅ Done |
| Comprehensive test suite                                 | ✅ Done |
| 100% Windows compatible                                  | ✅ Done |

---

## Tech Stack

* **Language:** Python 3.11+
* **CLI:** [Click](https://click.palletsprojects.com/)
* **Persistence:** SQLite (`queuectl.db`)
* **Concurrency:** `multiprocessing` (Windows-safe)
* **Dependencies:** `click`, `psutil`

---

## Project Structure

```plaintext
queuectl/
├── queuectl/               # Core package
│   ├── cli.py              # CLI commands
│   ├── db.py               # SQLite persistence
│   ├── job.py              # Job execution logic
│   ├── worker.py           # Worker processes
│   └── utils.py            # Helpers
├── tests/
│   └── test_queuectl.py    # Full test suite
├── queuectl.py             # CLI entrypoint
├── requirements.txt
└── queuectl.db             # Auto-generated
```

---

## Setup (Windows)

```powershell
# 1. Clone repo
git clone https://github.com/vijayhanand003/Jobqueuectl.git
cd Jobqueuectl

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

> Use PowerShell’s `Activate.ps1` on Windows. If using CMD, run `venv\Scripts\activate.bat`.

---

## Run Tests

```powershell
# Clean state
Remove-Item queuectl.db -ErrorAction SilentlyContinue

# Run full test suite
python -m tests.test_queuectl
```

**Expected Output:** `ALL TESTS PASSED!`

---

## CLI Usage

### Enqueue a Job

```powershell
python queuectl.py enqueue "{\"id\":\"job1\",\"command\":\"cmd /c echo Hello World\"}"
```

### Start Workers

```powershell
python queuectl.py worker start --count 3
```

### Check Status

```powershell
python queuectl.py status
```

### List Jobs

```powershell
python queuectl.py list --state pending
python queuectl.py list --state completed
```

### Dead Letter Queue (DLQ)

```powershell
python queuectl.py dlq list
python queuectl.py dlq retry job1
```

### Configuration

```powershell
python queuectl.py config set max-retries 5
python queuectl.py config set backoff_base 3
python queuectl.py config get max-retries
```

### Stop Workers

```powershell
python queuectl.py worker stop
```

---

## Architecture Overview

```plaintext
[CLI] → enqueue() → SQLite (jobs table)
                    ↓
             [Worker Pool] → poll → execute → update state
                    ↓
     Success → completed
     Fail → retry with backoff → DLQ after max_retries
```

---

## Backoff & Retry Logic

* Backoff delay = `backoff_base ** attempts`
* Example: `backoff_base = 2` → delays = 2s, 4s, 8s, 16s...
* Job moves to **DLQ** after exceeding `max_retries`

---

## Test Scenarios (All Passing)

| Test | Description                               |
| ---- | ----------------------------------------- |
| ✅ 1  | Enqueued job runs and completes           |
| ✅ 2  | Failed job retries 3 times → moves to DLQ |
| ✅ 3  | DLQ job is retried → succeeds             |
| ✅ 4  | Jobs persist after process restart        |

---

## Troubleshooting

| Issue                 | Fix                                         |
| --------------------- | ------------------------------------------- |
| JSON parsing errors   | Escape quotes or use JSON file path         |
| Workers not executing | Ensure `worker start` is running            |
| Multiprocessing error | Confirm Python 3.11+ and Windows spawn mode |

---

## Demo Video

 **Watch the project demo video here:**
[QueueCTL Demo Video - Google Drive](https://drive.google.com/drive/folders/1F3bo-2kbh78STcBWdbojGx8ROFsn1d99?usp=sharing)

---

## Author

**Vijay H Anand**
[GitHub](https://github.com/vijayhanand003) | [LinkedIn](https://www.linkedin.com/in/vijay-h-anand-4a925625a/)

---
