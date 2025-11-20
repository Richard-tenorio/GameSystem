import requests
from io import BytesIO

session = requests.Session()

# Login as admin
login_data = {
    'username': 'admin',
    'password': 'admin123'
}
response = session.post('http://localhost:5000/login', data=login_data)

print("Login status:", response.status_code)

# Prepare game data
game_data = {
    'title': 'Sample Game',
    'platform': 'PlayStation 5 (PS5 / Digital Edition)',
    'quantity': '10',
    'genre': 'Action',
    'price': '29.99'
}

# Create a dummy image
image_data = BytesIO(b'dummy image data')
image_data.name = 'sample.png'

files = {
    'image': ('sample.png', image_data, 'image/png')
}

# Add game
add_response = session.post('http://localhost:5000/add_game', data=game_data, files=files)

print("Add game status:", add_response.status_code)
print("Add game response URL:", add_response.url)

if 'admin' in add_response.url:
    print("Game added successfully")
else:
    print("Failed to add game")
