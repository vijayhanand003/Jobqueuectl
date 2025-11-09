# queuectl/cli.py
import click
import json
from .db import init_db, enqueue_job, list_jobs, list_dlq, retry_dlq_job, get_config, set_config
from .worker import start_workers, stop_workers, WORKER_PROCESSES

@click.group()
def main():
    init_db()

@main.command()
@click.argument('job_json')
def enqueue(job_json):
    """Enqueue a new job"""
    try:
        job_data = json.loads(job_json)
        required = ['id', 'command']
        if not all(k in job_data for k in required):
            raise ValueError(f"Missing keys: {required}")
        enqueue_job(job_data)
        click.echo(f"Enqueued job: {job_data['id']}")
    except json.JSONDecodeError:
        click.echo("Invalid JSON")
    except Exception as e:
        click.echo(f"Error: {e}")

@main.group()
def worker():
    """Manage worker processes"""
    pass

@worker.command('start')
@click.option('--count', default=1, type=int, help='Number of workers')
def worker_start(count):
    """Start background workers"""
    start_workers(count)

@worker.command('stop')
def worker_stop():
    """Stop all workers"""
    stop_workers()

@main.command()
def status():
    """Show queue status"""
    counts = {
        'pending': len(list_jobs('pending')),
        'processing': len(list_jobs('processing')),
        'completed': len(list_jobs('completed')),
        'failed': len(list_jobs('failed')),
        'dead': len(list_dlq())
    }
    active = len([p for p in WORKER_PROCESSES if p.is_alive()])
    click.echo(f"Jobs: {counts}")
    click.echo(f"Active Workers: {active}")

@main.command()
@click.option('--state', type=str, help='Filter by state')
def list(state):
    """List jobs"""
    jobs = list_jobs(state)
    click.echo(json.dumps(jobs, indent=2))

@main.group()
def dlq():
    """Dead Letter Queue commands"""
    pass

@dlq.command('list')
def dlq_list():
    jobs = list_dlq()
    click.echo(json.dumps(jobs, indent=2))

@dlq.command('retry')
@click.argument('job_id')
def dlq_retry(job_id):
    job = retry_dlq_job(job_id)
    if job:
        click.echo(f"Retried job {job_id} from DLQ")
    else:
        click.echo(f"Job {job_id} not in DLQ")

@main.group()
def config():
    """Manage configuration"""
    pass

@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    set_config(key, value)
    click.echo(f"Config: {key} = {value}")

@config.command('get')
@click.argument('key')
def config_get(key):
    value = get_config(key)
    click.echo(f"{key} = {value or 'Not set'}")

if __name__ == '__main__':
    main()