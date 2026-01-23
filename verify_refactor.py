import os
import django
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from emplyees.models import CustomUser
from reports.views import MonthlyFullReportView, MonthlyClientReportView, MonthlyEmployeeReportView

def finalize_verification():
    factory = APIRequestFactory()
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found for testing")
        return

    # Test Full Report
    print("\n--- Testing Refactored Full Report ---")
    request = factory.get('/api/reports/monthly/full/')
    force_authenticate(request, user=user)
    view = MonthlyFullReportView.as_view()
    response = view(request)
    if response.status_code == 200:
        print("Full Report OK")
        print(f"Keys: {response.data.keys()}")
    else:
        print(f"Full Report Error: {response.status_code}")
        print(response.data)

    # Test Client Report
    print("\n--- Testing Refactored Client Report ---")
    request = factory.get('/api/reports/monthly/clients/')
    force_authenticate(request, user=user)
    view = MonthlyClientReportView.as_view()
    response = view(request)
    if response.status_code == 200:
        print("Client Report OK")
    else:
        print(f"Client Report Error: {response.status_code}")

if __name__ == "__main__":
    finalize_verification()
