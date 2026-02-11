import os
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from emplyees.models import CustomUser
from clientapp.models import Client
from task.models import Task
from reports.views import MonthlyFullReportView, MonthlyClientReportView, MonthlyEmployeeReportView

def verify_tasks_in_reports():
    factory = APIRequestFactory()
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found for testing")
        return

    # 1. Create a sample client if not exists
    client, _ = Client.objects.get_or_create(
        client_name="Test Client Alpha",
        defaults={'contact_email': 'alpha@example.com'}
    )

    # 2. Create sample tasks for this month
    now = timezone.now()
    Task.objects.get_or_create(
        title="Report Integration Task 1",
        assignee=user,
        client=client,
        due_date=now,
        task_type='content',
        created_by=user
    )
    Task.objects.get_or_create(
        title="Report Integration Task 2",
        assignee=user,
        due_date=now + timedelta(days=1),
        task_type='seo',
        created_by=user
    )

    print("\n--- Testing Tasks in Full Report ---")
    request = factory.get('/api/reports/monthly/full/', {'month': now.month, 'year': now.year})
    force_authenticate(request, user=user)
    view = MonthlyFullReportView.as_view()
    response = view(request)
    if response.status_code == 200:
        tasks = response.data.get('tasks', [])
        print(f"Total Tasks in Full Report: {len(tasks)}")
        for t in tasks:
            print(f"- {t['title']} (Assignee: {t['assignee']}, Client: {t['client']})")
    else:
        print(f"Error: {response.status_code}")

    print("\n--- Testing Tasks in Client Report ---")
    request = factory.get('/api/reports/monthly/clients/', {'month': now.month, 'year': now.year})
    force_authenticate(request, user=user)
    view = MonthlyClientReportView.as_view()
    response = view(request)
    if response.status_code == 200:
        tasks = response.data.get('tasks', [])
        print(f"Tasks in Client Report: {len(tasks)}")
    else:
        print(f"Error: {response.status_code}")

    print("\n--- Testing Tasks in Employee Report ---")
    request = factory.get('/api/reports/monthly/employees/', {'month': now.month, 'year': now.year})
    force_authenticate(request, user=user)
    view = MonthlyEmployeeReportView.as_view()
    response = view(request)
    if response.status_code == 200:
        tasks = response.data.get('tasks', [])
        print(f"Tasks in Employee Report: {len(tasks)}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    verify_tasks_in_reports()
