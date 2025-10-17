import requests

url = 'http://localhost:8000/api/v1/projects/ee783fe1-d67a-4e94-87d3-94be3e6047ce/files'
response = requests.get(url)

print(f'Status Code: {response.status_code}')
print(f'File Count: {len(response.json())}')
print('\nFiles:')
for i, file in enumerate(response.json(), 1):
    print(f'{i}. {file["filename"]} (ID: {file["id"][:8]}...)')
