import os
import django
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from emplyees.models import CustomUser
from reports.views import MonthlyEmployeeReportView

def verify_employee_fields():
    factory = APIRequestFactory()
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found for testing")
        return

    now = timezone.now()
    print(f"\n--- Testing Employee Report Fields for {now.month}/{now.year} ---")
    request = factory.get('/api/reports/monthly/employees/', {'month': now.month, 'year': now.year})
    force_authenticate(request, user=user)
    view = MonthlyEmployeeReportView.as_view()
    response = view(request)
    
    if response.status_code == 200:
        details = response.data.get('details', [])
        print(f"Total Employees in Report: {len(details)}")
        if details:
            emp = details[0]
            print(f"Sample Employee Data:")
            print(f"- Name: {emp.get('employee_name')}")
            print(f"- Gender: {emp.get('gender')}")
            print(f"- Email: {emp.get('email')}")
            print(f"- Phone: {emp.get('phone')}")
            
            # Check if fields exist and are not None (they might be 'N/A' if empty in DB)
            if 'gender' in emp and 'email' in emp and 'phone' in emp:
                print("\nSUCCESS: New fields (gender, email, phone) are present in the response.")
            else:
                print("\nFAILURE: Missing one or more of the new fields.")
        else:
            print("No employee data found for this month in the report. Make sure there are paid salary records.")
    else:
        print(f"Error: {response.status_code}")
        print(response.data)

if __name__ == "__main__":
    verify_employee_fields()
