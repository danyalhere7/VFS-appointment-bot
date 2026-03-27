import urllib.request
import json
import sys

# 1. Get latest runs
url = "https://api.github.com/repos/danyalhere7/VFS-appointment-bot/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
except Exception as e:
    print(f"Error fetching runs: {e}")
    sys.exit(1)

# Find the most recent run (should be the "Fix GitHub Actions..." one)
runs = data.get('workflow_runs', [])
if not runs:
    print("No runs found.")
    sys.exit(1)

latest_run = runs[0]
print(f"Latest Run ID: {latest_run['id']} | Status: {latest_run['status']} | Conclusion: {latest_run['conclusion']}")

# 2. Get jobs for this run
jobs_url = latest_run['jobs_url']
req = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        jobs_data = json.loads(resp.read().decode())
except Exception as e:
    print(f"Error fetching jobs: {e}")
    sys.exit(1)

jobs = jobs_data.get('jobs', [])
if not jobs:
    print("No jobs found for this run.")
    sys.exit(1)

job_id = jobs[0]['id']
print(f"Job ID: {job_id}")

# 3. Get log for this job
log_url = f"https://api.github.com/repos/danyalhere7/VFS-appointment-bot/actions/jobs/{job_id}/logs"
req = urllib.request.Request(log_url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        logs = resp.read().decode()
    
    # We only care about the end of the logs (where Python crashes)
    lines = logs.split('\n')
    print("\n--- LAST 50 LINES OF LOG ---")
    print('\n'.join(lines[-50:]))
except Exception as e:
    print(f"Error fetching logs: {e}")
