import os
import django
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from emplyees.models import LeaveManagement
from leaves.models import LeaveApplication
from django.db import transaction

def migrate_leaves():
    legacy_leaves = LeaveManagement.objects.all()
    print(f"Found {legacy_leaves.count()} legacy leave records.")

    count = 0
    with transaction.atomic():
        for legacy in legacy_leaves:
            # Map category to leave_type
            # Handle potential date parsing if start_date/end_date are strings in legacy
            try:
                # If they are strings like 'YYYY-MM-DD', they can be converted to DateField
                # If they are already date objects, it's easier.
                # In emplyees.models.LeaveManagement, they are CharFields.
                
                # Check if it already exists in LeaveApplication to avoid duplicates if re-run
                if LeaveApplication.objects.filter(
                    employee=legacy.employee,
                    start_date=legacy.start_date,
                    end_date=legacy.end_date,
                    leave_type=legacy.category
                ).exists():
                    continue

                LeaveApplication.objects.create(
                    employee=legacy.employee,
                    leave_type=legacy.category,
                    start_date=legacy.start_date,
                    end_date=legacy.end_date,
                    total_days=legacy.total_days,
                    reason=legacy.reason,
                    status=legacy.status,
                    attachment=legacy.attachment,
                    applied_date=legacy.applied_date if hasattr(legacy, 'applied_date') else None,
                    # Note: other fields like address_during_leave will be null for legacy data
                )
                count += 1
            except Exception as e:
                print(f"Error migrating record {legacy.id}: {e}")

    print(f"Successfully migrated {count} records.")

if __name__ == "__main__":
    migrate_leaves()
