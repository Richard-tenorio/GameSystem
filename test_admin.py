import requests

session = requests.Session()

# Login as admin
login_data = {
    'username': 'admin',
    'password': 'admin123'
}
response = session.post('http://localhost:5000/login', data=login_data)

print("Login status:", response.status_code)
print("Login response URL:", response.url)

if 'admin' in response.url:
    print("Login successful, redirected to admin")
else:
    print("Login failed")

# Now get admin page
admin_response = session.get('http://localhost:5000/admin')
print("Admin page status:", admin_response.status_code)
print("Admin page content length:", len(admin_response.text))

# Check for error message
if "Error loading dashboard" in admin_response.text:
    print("Error: Dashboard loading failed")
    # Print the error part
    start = admin_response.text.find("Error loading dashboard")
    end = admin_response.text.find("</div>", start) + 6
    print("Error message:", admin_response.text[start:end])
elif "Dashboard" in admin_response.text:
    print("Dashboard loaded successfully")
else:
    print("Admin page loaded, but dashboard section not found")
