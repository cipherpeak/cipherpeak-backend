import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from emplyees.models import CustomUser
from reports.models import MonthlyReport
from reports.views import MonthlyFullReportView, MonthlyReportListView

def verify_persistence():
    factory = APIRequestFactory()
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found for testing")
        return

    # Clear existing reports for clean test
    MonthlyReport.objects.all().delete()
    print("Deleted existing reports.")

    # 1. Generate a report via API
    print("\n--- Generating January 2026 Report ---")
    request = factory.get('/api/reports/monthly/full/', {'month': 1, 'year': 2026})
    force_authenticate(request, user=user)
    view = MonthlyFullReportView.as_view()
    response = view(request)
    if response.status_code == 200:
        print("Report Generated Successfully")
    else:
        print(f"Error Generating Report: {response.status_code}")
        return

    # 2. Check if a model record was created
    report_count = MonthlyReport.objects.count()
    print(f"MonthlyReport records in DB: {report_count}")
    if report_count == 1:
        report = MonthlyReport.objects.first()
        print(f"Saved Report: {report} (Net Profit: {report.net_profit})")
    else:
        print("FAILED: No MonthlyReport record found!")

    # 3. Test the History List API
    print("\n--- Testing History List API ---")
    request = factory.get('/api/reports/history/')
    force_authenticate(request, user=user)
    view = MonthlyReportListView.as_view()
    response = view(request)
    if response.status_code == 200:
        print(f"History List Results: {len(response.data)}")
        for item in response.data:
            print(f"- {item['month_name']} {item['year']}: Total Income {item['total_income']}")
    else:
        print(f"History Error: {response.status_code}")

if __name__ == "__main__":
    verify_persistence()
