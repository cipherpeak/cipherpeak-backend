import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipherpeak.settings')
django.setup()

from reports.utils import get_monthly_client_data, get_monthly_employee_data

print("=" * 80)
print("Testing Monthly Client Report for February 2026")
print("=" * 80)

try:
    client_data = get_monthly_client_data(2, 2026)
    print(f"✓ Client data fetched successfully!")
    print(f"  - Found {len(client_data.get('details', []))} clients")
    print(f"  - Total revenue: {client_data.get('summary', {}).get('total_revenue', 0)}")
except Exception as e:
    print(f"✗ ERROR in get_monthly_client_data:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Testing Monthly Employee Report for February 2026")
print("=" * 80)

try:
    employee_data = get_monthly_employee_data(2, 2026)
    print(f"✓ Employee data fetched successfully!")
    print(f"  - Found {len(employee_data.get('details', []))} employees")
    print(f"  - Total salary: {employee_data.get('summary', {}).get('total_net_paid', 0)}")
except Exception as e:
    print(f"✗ ERROR in get_monthly_employee_data:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Debug test complete")
print("=" * 80)
