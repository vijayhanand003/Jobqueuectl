# queuectl/utils.py
def calculate_backoff(attempts, base=2):
    return base ** attempts