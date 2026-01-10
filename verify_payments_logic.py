import os
import django
from datetime import date, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cipher.settings')
django.setup()

from clientapp.models import Client, ClientPaymentHistory
from emplyees.models import CustomUser, SalaryHistory
from clientapp.serializers import ClientDetailSerializer
from emplyees.serializers import EmployeeDetailSerializer

def test_client_logic():
    print("\n--- Testing Client Payment Logic ---")
    today = timezone.now().date()
    
    scenarios = [
        ("Payment Due Today", today),
        ("Payment Overdue (1 day past)", today - timedelta(days=1)),
        ("Payment Reaching Soon (2 days remaining)", today + timedelta(days=2)),
        ("Payment Reaching Soon (5 days remaining)", today + timedelta(days=5)),
        ("Payment Pending (6 days remaining)", today + timedelta(days=6)),
    ]
    
    for label, due_date in scenarios:
        # Create a mock client
        client = Client(
            client_name=f"Test Client {label}",
            payment_date=due_date.day,
            # We bypass save() but call the logic manually to isolate test
        )
        # Manually set next_payment_date to simulate the scenario
        client.next_payment_date = due_date
        client.update_payment_status()
        
        # Check serializer status
        serializer = ClientDetailSerializer(client)
        status = serializer.get_payment_status(client)
        
        print(f"Scenario: {label:40} | Model Status: {client.current_month_payment_status:10} | Serializer status: {status}")

def test_employee_logic():
    print("\n--- Testing Employee Salary Logic ---")
    today = timezone.now().date()
    
    scenarios = [
        ("Salary Due Today", today),
        ("Salary Overdue (1 day past)", today - timedelta(days=1)),
        ("Salary Reaching Soon (2 days remaining)", today + timedelta(days=2)),
        ("Salary Reaching Soon (5 days remaining)", today + timedelta(days=5)),
        ("Salary Pending (6 days remaining)", today + timedelta(days=6)),
    ]
    
    for label, due_date in scenarios:
        # Create a mock employee
        employee = CustomUser(
            username=f"test_user_{due_date.day}",
            joining_date=due_date
        )
        
        # Check serializer status
        serializer = EmployeeDetailSerializer(employee)
        status = serializer.get_payment_status(employee)
        
        print(f"Scenario: {label:40} | Serializer status: {status}")

if __name__ == "__main__":
    try:
        test_client_logic()
        test_employee_logic()
    except Exception as e:
        print(f"Error during verification: {e}")
