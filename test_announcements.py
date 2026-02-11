
import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/HP/cipherpeak-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from django.contrib.auth import get_user_model
from emplyees.models import Announcement
from django.test import Client
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()

def test_announcements():
    # 1. Create or get admin and employee users
    admin_user, _ = User.objects.get_or_create(
        username='testadmin',
        defaults={'email': 'admin@test.com', 'role': 'admin', 'is_active': True}
    )
    admin_user.set_password('password123')
    admin_user.save()

    employee_user, _ = User.objects.get_or_create(
        username='testemployee',
        defaults={'email': 'emp@test.com', 'role': 'employee', 'is_active': True}
    )
    employee_user.set_password('password123')
    employee_user.save()

    # 2. Get tokens
    admin_refresh = RefreshToken.for_user(admin_user)
    admin_token = str(admin_refresh.access_token)

    emp_refresh = RefreshToken.for_user(employee_user)
    emp_token = str(emp_refresh.access_token)

    client = Client()

    print("\n--- Testing Announcement Creation (Admin) ---")
    data = {
        'title': 'System Maintenance',
        'description': 'The system will be down for maintenance on Saturday.'
    }
    response = client.post(
        '/auth/announcements/',
        data=json.dumps(data),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {admin_token}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")

    print("\n--- Testing Announcement Creation (Employee - Should Fail) ---")
    response = client.post(
        '/auth/announcements/',
        data=json.dumps(data),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {emp_token}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")

    print("\n--- Testing Announcement Listing (Employee) ---")
    response = client.get(
        '/auth/announcements/',
        HTTP_AUTHORIZATION=f'Bearer {emp_token}'
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.content.decode()}")

if __name__ == "__main__":
    test_announcements()
