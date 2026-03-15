import requests

s = requests.Session()
res = s.post("http://localhost:8000/api/auth/login", json={"username": "admin", "password": "change-this-password"})
print("Login:", res.status_code, res.text)

res = s.post("http://localhost:8000/api/ai/generate", json={"idea": "hello internet", "target_subreddits": ["test"]})
print("Generate:", res.status_code, res.text)
