import urllib.request
import json

url = 'https://api.github.com/orgs/Mods-Center/repos?per_page=30'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        repos = json.loads(resp.read().decode())
        for repo in repos:
            print(f"- {repo['name']}: {repo.get('description', '')}")
except Exception as error:
    print('Failed:', error)

