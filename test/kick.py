import requests

url = "http://localhost:20080/v1"  # cloudflare bypass proxy
headers = {"Content-Type": "application/json"}
data = {
    "cmd": "request.get",
    "url": "https://kick.com/api/v1/channels/" + "madjoepeach",
    "maxTimeout": 60000,
}
response = requests.post(url, headers=headers, json=data)
print(response.text)
