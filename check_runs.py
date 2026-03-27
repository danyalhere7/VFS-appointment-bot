import urllib.request
import json

url = "https://api.github.com/repos/danyalhere7/VFS-appointment-bot/actions/runs"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

print(f"Total runs: {data.get('total_count')}")
for run in data.get('workflow_runs', [])[:3]:
    msg = run.get('head_commit', {}).get('message', '').split('\n')[0]
    print(f"Run ID: {run.get('id')} | Status: {run.get('status')} | Conclusion: {run.get('conclusion')} | Commit: {msg}")
