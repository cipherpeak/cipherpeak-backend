from rest_framework import serializers
from .models import Client, ClientDocument, ClientAdminNote, ClientPayment
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
            
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'website',
            'business_registration_number',
            'tax_id',
            'monthly_retainer',
            'description',
            'created_at',
            'updated_at',
            
            'is_active_client',
            'contract_duration',
            
        ]
        read_only_fields = [
            'created_at', 
            'updated_at', 
            'is_active_client',
        ]
    
    def validate_client_name(self, value):
        
        queryset = Client.objects.filter(client_name=value)
        
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
            
        if queryset.exists():
            raise serializers.ValidationError("A client with this name already exists.")
        return value
    

#client document serializer
class ClientDocumentSerializer(serializers.ModelSerializer):
    
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    uploaded_by = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    class Meta:
        model = ClientDocument
        fields = [
            'id', 'document_type', 'file', 'client_name','uploaded_by','created_at',
        ]


#client payment serializer
class ClientPaymentSerializer(serializers.ModelSerializer):
    
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ClientPayment
        fields = [
            'id', 'client', 'month', 'year',
            'amount', 'tax_amount', 'discount', 'net_amount',
            'scheduled_date', 'payment_date', 'status', 'status_display',
            'payment_method', 'transaction_id', 'processed_by',
            'processed_by_name', 'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'net_amount']


#client admin note serializer
class ClientAdminNoteSerializer(serializers.ModelSerializer):
    
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


#client detail serializer
class ClientDetailSerializer(serializers.ModelSerializer):
     
    is_active_client = serializers.ReadOnlyField()
    contract_duration = serializers.ReadOnlyField()
    documents = ClientDocumentSerializer(many=True, read_only=True)
    client_payments = ClientPaymentSerializer(many=True, read_only=True)
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
            'onboarding_date', 'monthly_retainer', 'address', 'city', 'state',
            'country', 'postal_code', 'website',
            'business_registration_number', 'tax_id', 'description',
            'is_active_client', 'contract_duration', 'documents', 
            'client_payments', 'admin_notes', 'payment_status',
            'contract_start_date', 'contract_end_date',
        ]
    
    def get_payment_status(self, obj):
      
        from django.utils import timezone
        import calendar
        from datetime import date
        
        if not obj.onboarding_date:
            return "Unknown"
        
        today = timezone.now().date()
        
        current_date_iter = date(obj.onboarding_date.year, obj.onboarding_date.month, 1)
        
        end_date = date(today.year, today.month, 1)
        
        target_month = None
        target_year = None
        
        while current_date_iter <= end_date:
            m = current_date_iter.month
            y = current_date_iter.year
            
            is_paid = ClientPayment.objects.filter(
                client=obj,
                month=m,
                year=y,
                status__in=['paid', 'early_paid']
            ).exists()
            
            if not is_paid:
                target_month = m
                target_year = y
                break
            
            if current_date_iter.month == 12:
                current_date_iter = date(current_date_iter.year + 1, 1, 1)
            else:
                current_date_iter = date(current_date_iter.year, current_date_iter.month + 1, 1)

        if not target_month:
           
            current_payment = ClientPayment.objects.filter(
                client=obj,
                month=today.month,
                year=today.year,
                status='early_paid'
            ).exists()
            
            next_month = (today.month % 12) + 1
            next_year = today.year + (1 if today.month == 12 else 0)
            next_payment_is_early = ClientPayment.objects.filter(
                client=obj,
                month=next_month,
                year=next_year,
                status='early_paid'
            ).exists()

            if current_payment or next_payment_is_early:
                return "Early Payment Received"
            return "Payment Received"

        try:
            _, last_day_target_month = calendar.monthrange(target_year, target_month)
            scheduled_date = date(target_year, target_month, last_day_target_month)
        except (AttributeError, ValueError):
            _, last_day_target_month = calendar.monthrange(target_year, target_month)
            scheduled_date = date(target_year, target_month, last_day_target_month)
        
        days_diff = (scheduled_date - today).days
        
        if days_diff < 0:
            return "Overdue"
        elif days_diff == 0:
            return "Pay Client"
        elif 0 < days_diff <= 7:
            return "Payment date coming soon"
        else:
            return None


#client update serializer
class ClientUpdateSerializer(serializers.ModelSerializer):
    
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
            'monthly_retainer',
            'description',
        ]

    def validate_client_name(self, value):
        
        queryset = Client.objects.filter(client_name=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("A client with this name already exists.")
        return value

   
#client list serializer
class ClientListSerializer(serializers.ModelSerializer):
  
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


#client payment detail serializer
class ClientPaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayment
        fields = '__all__'