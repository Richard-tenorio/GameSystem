import requests
import json

base_url = 'http://localhost:5000'

def test_health():
    print("Testing /health endpoint...")
    response = requests.get(f'{base_url}/health')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'healthy' and data.get('database') == 'connected':
            print("Health check passed")
        else:
            print("Health check failed:", data)
    else:
        print("Health check failed")

def test_admin_login():
    print("\nTesting admin login...")
    session = requests.Session()
    login_data = {'username': 'admin', 'password': 'admin123'}
    response = session.post(f'{base_url}/login', data=login_data)
    print(f"Login status: {response.status_code}")
    if 'admin' in response.url:
        print("Admin login successful")
        return session
    else:
        print("Admin login failed")
        return None

def test_admin_dashboard(session):
    print("Testing admin dashboard...")
    response = session.get(f'{base_url}/admin')
    print(f"Dashboard status: {response.status_code}")
    if "Error loading dashboard" in response.text:
        print("Dashboard error found")
        start = response.text.find("Error loading dashboard")
        end = response.text.find("</div>", start) + 6
        print("Error:", response.text[start:end])
    elif "Dashboard" in response.text:
        print("Dashboard loaded successfully")
    else:
        print("Dashboard section not found")

def test_customer_registration():
    print("\nTesting customer registration...")
    reg_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Testpass123',
        'confirm_password': 'Testpass123',
        'full_name': 'Test User',
        'age': '25'
    }
    response = requests.post(f'{base_url}/register', data=reg_data)
    print(f"Registration status: {response.status_code}")
    if response.status_code == 200 and "success" in response.text.lower():
        print("Registration successful")
    else:
        print("Registration failed or user exists")

def test_customer_login():
    print("Testing customer login...")
    session = requests.Session()
    login_data = {'username': 'testuser', 'password': 'Testpass123'}
    response = session.post(f'{base_url}/login', data=login_data)
    print(f"Login status: {response.status_code}")
    if 'customer' in response.url or 'index' in response.url:
        print("Customer login successful")
        return session
    else:
        print("Customer login failed")
        return None

def test_marketplace(session):
    print("Testing marketplace page...")
    response = session.get(f'{base_url}/marketplace')
    print(f"Marketplace status: {response.status_code}")
    if "marketplace" in response.text.lower():
        print("Marketplace loaded")
    else:
        print("Marketplace failed to load")

def test_api_cart_add(session):
    print("Testing API cart add...")
    data = {'game_id': 1}
    response = session.post(f'{base_url}/api/cart/add', json=data)
    print(f"Cart add status: {response.status_code}")
    data = response.json()
    if data.get('success'):
        print("Cart add successful")
    else:
        print("Cart add failed:", data.get('message'))

def test_api_cart_count(session):
    print("Testing API cart count...")
    response = session.get(f'{base_url}/api/cart/count')
    print(f"Cart count status: {response.status_code}")
    data = response.json()
    print(f"Cart count: {data.get('count')}")

def test_api_ratings():
    print("Testing API ratings...")
    response = requests.get(f'{base_url}/api/ratings/1')
    print(f"Ratings status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("Ratings API successful")
        else:
            print("Ratings API failed")
    else:
        print("Ratings API failed")

def test_other_pages(session):
    pages = ['/library', '/profile', '/settings', '/topup', '/suggest_game', '/sell_game']
    for page in pages:
        print(f"Testing {page}...")
        response = session.get(f'{base_url}{page}')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"{page} loaded")
        else:
            print(f"{page} failed")

def test_admin_pages(session):
    pages = ['/admin_games', '/user_management', '/manage_suggestions', '/admin_settings', '/manage_topup_requests']
    for page in pages:
        print(f"Testing {page}...")
        response = session.get(f'{base_url}{page}')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"{page} loaded")
        else:
            print(f"{page} failed")

def test_logout(session):
    print("Testing logout...")
    response = session.get(f'{base_url}/logout')
    print(f"Logout status: {response.status_code}")
    if response.status_code == 302:  # redirect to login
        print("Logout successful")
    else:
        print("Logout failed")

# Run all tests
if __name__ == '__main__':
    test_health()
    admin_session = test_admin_login()
    if admin_session:
        test_admin_dashboard(admin_session)
        test_admin_pages(admin_session)
        test_logout(admin_session)

    test_customer_registration()
    customer_session = test_customer_login()
    if customer_session:
        test_marketplace(customer_session)
        test_api_cart_add(customer_session)
        test_api_cart_count(customer_session)
        test_other_pages(customer_session)
        test_logout(customer_session)

    test_api_ratings()

    print("\nAll tests completed.")
