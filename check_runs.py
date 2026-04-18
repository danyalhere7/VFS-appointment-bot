import urllib.request
import json
import sys

url = "https://api.github.com/repos/danyalhere7/VFS-appointment-bot/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
except Exception as e:
    print(f"Error fetching runs: {e}")
    sys.exit(1)

print(f"Total runs: {data.get('total_count')}")
for run in data.get('workflow_runs', [])[:10]:
    msg = run.get('head_commit', {}).get('message', '').split('\n')[0]
    event = run.get('event')
    status = run.get('status')
    conclusion = run.get('conclusion')
    created_at = run.get('created_at')
    print(f"Time: {created_at} | Event: {event:<10} | Status: {status:<10} | Conclusion: {conclusion:<10} | Msg: {msg}")
