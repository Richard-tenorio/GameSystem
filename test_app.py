import requests

base_url = 'http://127.0.0.1:5000'

# Test registration
register_data = {
    'username': 'testuser',
    'password': 'Testpass1!',
    'confirm_password': 'Testpass1!',
    'role': 'customer'
}

response = requests.post(f'{base_url}/register', data=register_data)
print('Registration response:', response.status_code, response.text)

# Test login
login_data = {
    'username': 'testuser',
    'password': 'Testpass1!'
}

response = requests.post(f'{base_url}/', data=login_data)
print('Login response:', response.status_code, response.text)
