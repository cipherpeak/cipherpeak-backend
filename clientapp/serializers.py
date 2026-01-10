# client/serializers.py
from rest_framework import serializers
from .models import Client, ClientDocument, ClientPaymentHistory, ClientAdminNote
from django.utils import timezone
from datetime import date
import calendar


#client serializer
class ClientSerializer(serializers.ModelSerializer):
    is_active_client = serializers.ReadOnlyField()
    contract_duration = serializers.ReadOnlyField()
    class Meta:
        model = Client
        fields = [
            'id',
            'client_name',
            'client_type',
            'industry',
            'owner_name',
            'contact_person_name',
            'contact_email',
            'contact_phone',
            'instagram_id',
            'facebook_id',
            'youtube_channel',
            'google_my_business',
            'linkedin_url',
            'twitter_handle',
            'videos_per_month',
            'posters_per_month',
            'reels_per_month',
            'stories_per_month',
            'status',
            'onboarding_date',
            'contract_start_date',
            'contract_end_date',
            # New payment timing fields
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'website',
            'business_registration_number',
            'tax_id',
            'description',
            'created_at',
            'updated_at',
            # Read-only properties
            'is_active_client',
            'contract_duration',
            
        ]
        read_only_fields = [
            'created_at', 
            'updated_at', 
            'is_active_client',
        ]
    
    def validate_client_name(self, value):
        """Ensure client name is unique"""
        queryset = Client.objects.filter(client_name=value)
        
        # If updating, exclude current instance
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
            
        if queryset.exists():
            raise serializers.ValidationError("A client with this name already exists.")
        return value
    

#client document serializer
class ClientDocumentSerializer(serializers.ModelSerializer):
    
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    
    class Meta:
        model = ClientDocument
        fields = [
            'id', 'document_type', 'file', 'client_name', 
        ]
        

class ClientPaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for client payment history"""
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ClientPaymentHistory
        fields = [
            'id',
            'client',
            'client_name',
            'payment_date',
            'amount',
            'payment_type',
            'payment_method',
            'transaction_id',
            'reference_number',
            'notes',
            'is_early_payment',
            'early_days',
            'processed_by',
            'processed_by_name',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['processed_by', 'created_at', 'updated_at']


class ClientAdminNoteSerializer(serializers.ModelSerializer):
    """Serializer for client admin notes"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_role = serializers.CharField(source='created_by.role', read_only=True)
    
    class Meta:
        model = ClientAdminNote
        fields = [
            'id',
            'client',
            'note',
            'created_by',
            'created_by_name',
            'created_by_role',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ClientAdminNoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating client admin notes"""
    class Meta:
        model = ClientAdminNote
        fields = ['client', 'note']



#client detail serializer
class ClientDetailSerializer(serializers.ModelSerializer):
    """Full serializer for client details including all fields and properties"""
    is_active_client = serializers.ReadOnlyField()
    contract_duration = serializers.ReadOnlyField()
    documents = ClientDocumentSerializer(many=True, read_only=True)
    payment_history = ClientPaymentHistorySerializer(many=True, read_only=True)
    admin_notes = ClientAdminNoteSerializer(many=True, read_only=True)
    
    
    
    payment_status = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Client
        fields = [
            'id', 'client_name', 'client_type', 'industry',
            'owner_name', 'contact_person_name', 'contact_email',
            'contact_phone', 'instagram_id', 'facebook_id',
            'youtube_channel', 'google_my_business', 'linkedin_url',
            'twitter_handle', 'videos_per_month', 'posters_per_month',
            'reels_per_month', 'stories_per_month', 'status',
            'monthly_retainer', 'address', 'city', 'state',
            'country', 'postal_code', 'website',
            'business_registration_number', 'tax_id', 'description',
            'is_active_client', 'contract_duration', 'documents', 
            'payment_history', 'admin_notes', 'payment_status',
            # Add these fields if they exist in your Client model:
            'contract_start_date', 'contract_end_date', 'admin_notes',
        ]
    
        
    def get_payment_status(self, obj):
        today = timezone.now().date()
        
        # Check if payment history exists for current month and year
        has_paid = obj.payment_history.filter(
            payment_date__year=today.year, 
            payment_date__month=today.month
        ).exists()
        
        if has_paid:
            return "Paid"
            
        if not obj.payment_date:
            return "Unknown"
            
        # Get the current year and month
        current_year = today.year
        current_month = today.month
        
        # Get the last day of current month
        _, last_day_current_month = calendar.monthrange(current_year, current_month)
        
        # Adjust payment date if it exceeds the last day of the month
        adjusted_payment_date = min(obj.payment_date, last_day_current_month)
        
        # Create payment date for current month
        payment_due_date = date(current_year, current_month, adjusted_payment_date)
            
        days_diff = (payment_due_date - today).days
        
        if days_diff <= 0:
            return "Payment Due" # Date passed for this month or is today
        elif days_diff <= 5:
            return "Payment date reaching soon"
        else:
            return "Pending"

#client update serializer
class ClientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating client details"""
    class Meta:
        model = Client
        fields = [
            'client_name',
            'client_type',
            'industry',
            'owner_name',
            'contact_person_name',
            'contact_email',
            'contact_phone',
            'instagram_id',
            'facebook_id',
            'youtube_channel',
            'google_my_business',
            'linkedin_url',
            'twitter_handle',
            'videos_per_month',
            'posters_per_month',
            'reels_per_month',
            'stories_per_month',
            'status',
            'contract_start_date',
            'contract_end_date',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'website',
            'business_registration_number',
            'tax_id',
            'description',
        ]

    def validate_client_name(self, value):
        """Ensure client name is unique"""
        queryset = Client.objects.filter(client_name=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("A client with this name already exists.")
        return value

   
#client list serializer
class ClientListSerializer(serializers.ModelSerializer):
    """Simplified serializer for client lists"""
    is_active_client = serializers.ReadOnlyField()
   
    class Meta:
        model = Client
        fields = [
            'id',
            'client_name',
            'client_type',
            'industry',
            'contact_person_name',
            'contact_email',
            'contact_phone',
            'status',
            'is_active_client',
            'created_at',
        ]



class ClientMarkPaymentSerializer(serializers.ModelSerializer):
    """Simplified serializer for marking payments"""
    payment_date = serializers.DateField(required=True)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        min_value=0
    )
    payment_method = serializers.ChoiceField(
        choices=ClientPaymentHistory.PAYMENT_METHOD_CHOICES,
        default='bank_transfer'
    )
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    reference_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_payment_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Payment date cannot be in the future.")
        return value

    """Serializer for client payment timeline information"""
    payment_status_display = serializers.ReadOnlyField()
    days_until_next_payment = serializers.ReadOnlyField()
    is_payment_overdue = serializers.ReadOnlyField()
    is_early_payment = serializers.ReadOnlyField()
    early_payment_days = serializers.ReadOnlyField()
    payment_timing_display = serializers.CharField(source='get_payment_timing_display', read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id',
            'client_name',
            'payment_cycle',
            'payment_date',
            'next_payment_date',
            'current_month_payment_status',
            'payment_timing',
            'payment_timing_display',
            'last_payment_date',
            'early_payment_date',
            'early_payment_amount',
            'monthly_retainer',
            'payment_status_display',
            'days_until_next_payment',
            'is_payment_overdue',
            'is_early_payment',
            'early_payment_days',
        ]
        read_only_fields = fields