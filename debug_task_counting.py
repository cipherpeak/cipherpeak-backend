import os
import django
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from emplyees.models import CustomUser
from task.models import Task

def debug_tasks():
    emp_name = "krishna S Nair"
    # Find the user
    user = CustomUser.objects.filter(first_name__icontains="krishna").first()
    if not user:
        print(f"Employee {emp_name} not found.")
        return

    print(f"Checking tasks for {user.get_full_name()} (ID: {user.id})")
    
    month = 1
    year = 2026
    
    # Check all tasks for this user
    all_tasks = Task.objects.filter(assignee=user)
    print(f"Total tasks assigned: {all_tasks.count()}")
    
    for t in all_tasks:
        print(f"Task: {t.title} | Due: {t.due_date} | Status: {t.status} | Deleted: {t.is_deleted}")
    
    # Check tasks with the specific filter used in utils.py
    emp_tasks = Task.objects.filter(
        assignee=user,
        due_date__month=month,
        due_date__year=year,
        is_deleted=False
    )
    print(f"\nFiltered tasks (Month: {month}, Year: {year}): {emp_tasks.count()}")
    for t in emp_tasks:
        print(f"- {t.title} ({t.status})")

if __name__ == "__main__":
    debug_tasks()
