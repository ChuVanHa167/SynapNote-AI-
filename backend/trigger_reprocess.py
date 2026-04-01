import requests

meeting_id = "5e9a3273-eebd-4551-951e-777c5337b95d"
url = f"http://localhost:8000/meetings/{meeting_id}/reprocess"

try:
    response = requests.post(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
