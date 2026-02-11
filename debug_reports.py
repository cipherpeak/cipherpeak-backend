import os
import django
import sys

# Add project root to path if needed (though running from root usually works)
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from reports.utils import get_monthly_client_data
from django.utils import timezone

now = timezone.now()
print(f"Starting debug for {now.month}/{now.year}...")
try:
    data = get_monthly_client_data(now.month, now.year)
    print("Function returned data keys:", data.keys())
    print("Client Details Count:", len(data['details']))
    print("Summary:", data['summary'])
    if len(data['details']) > 0:
        print("First client:", data['details'][0]['client_name'], data['details'][0]['status'])
except Exception as e:
    print("CRASH during execution:", e)
    import traceback
    traceback.print_exc()
