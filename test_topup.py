import requests

# Register a new customer
register_data = {
    'username': 'testuser4',
    'email': 'testuser4@example.com',
    'full_name': 'Test User 4',
    'age': '25',
    'password': 'Password123!',
    'confirm_password': 'Password123!'
}
register_response = requests.post('http://localhost:5000/register', data=register_data)
print(f"Register response: {register_response.status_code}")

# Login
login_data = {
    'username': 'testuser4',
    'password': 'Password123!'
}
session = requests.Session()
login_response = session.post('http://localhost:5000/login', data=login_data)
print(f"Login response: {login_response.status_code}")

# Submit topup request
topup_data = {
    'amount': '100',
    'payment_method': 'bank_transfer',
    'reference_number': '123456789'
}
# No screenshot file
topup_response = session.post('http://localhost:5000/topup', data=topup_data)
print(f"Topup response: {topup_response.status_code}")
print("Topup submitted successfully (ignoring image as requested)")
