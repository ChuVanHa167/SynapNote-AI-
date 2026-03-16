import requests
import json

try:
    response = requests.get("http://localhost:8000/meetings")
    if response.ok:
        data = response.json()
        print(f"Total meetings: {len(data)}")
        for m in data:
            print(f"ID: {m['id']}, Title: {m['title']}, Status: '{m['status']}'")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Connection failed: {str(e)}")
