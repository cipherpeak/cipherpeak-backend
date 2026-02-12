from rest_framework import serializers
from .models import Client, ClientDocument, ClientPayment
from django.utils import timezone
from datetime import date
import calendar
from . import utils


#client serializer
class ClientSerializer(serializers.ModelSerializer):
    is_active_client = serializers.SerializerMethodField()
    contract_duration = serializers.SerializerMethodField()
    payment_status_display = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='contact_email')
    phone = serializers.ReadOnlyField(source='contact_phone')
    company = serializers.ReadOnlyField(source='client_name')
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)

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
            'payment_date',
            'next_payment_date',
            'current_month_payment_status',
            'last_payment_date',
            'payment_status_display',
            'email',
            'phone',
            'company',
            'client_type_display',
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

    def get_is_active_client(self, obj):
        return obj.status == 'active'

    def get_contract_duration(self, obj):
        if obj.contract_start_date and obj.contract_end_date:
            delta = obj.contract_end_date - obj.contract_start_date
            return delta.days // 30
        return None

    def get_payment_status_display(self, obj):
        # We try to use the more robust get_payment_status logic if available
        # or at least avoid returning "Paid" if there's no record.
        # For simplicity and performance in the list view, we still use obj.current_month_payment_status
        # but the Detail view will be the most accurate.
        
        if hasattr(obj, 'next_payment_date') and obj.next_payment_date:
             days_until = (obj.next_payment_date - timezone.now().date()).days
        else:
             days_until = None

        if obj.current_month_payment_status == 'paid':
            # Verify if this is actually true for the list view too
            return "Paid"
        elif obj.current_month_payment_status == 'early_paid':
            return "Early Paid"
        elif obj.current_month_payment_status == 'overdue':
            return "Overdue"
        elif days_until == 0:
            return "Due Today"
        elif days_until and days_until <= 7:
            return f"Due in {days_until} days"
        else:
            return "Pending"

    def create(self, validated_data):
        from verification.models import ClientVerification
        
        instance = super().create(validated_data)
        
        # Calculate payment dates
        if instance.payment_date:
             utils.calculate_next_payment_date(instance)
        utils.update_payment_status(instance)
        instance.save()
        
        # Create a single verification object for the client
        ClientVerification.objects.create(
            client=instance,
            verified_by=None
        )
        
        return instance
    

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



#client detail serializer
class ClientDetailSerializer(serializers.ModelSerializer):
     
    is_active_client = serializers.SerializerMethodField()
    contract_duration = serializers.SerializerMethodField()
    payment_status_display = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='contact_email')
    phone = serializers.ReadOnlyField(source='contact_phone')
    company = serializers.ReadOnlyField(source='client_name')
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)
    documents = ClientDocumentSerializer(many=True, read_only=True)
    client_payments = ClientPaymentSerializer(many=True, read_only=True)
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
            'onboarding_date', 'monthly_retainer', 
            'payment_date', 'next_payment_date', 'current_month_payment_status',
            'last_payment_date', 'payment_status_display',
            'email', 'phone', 'company', 'client_type_display',
            'address', 'city', 'state',
            'country', 'postal_code', 'website',
            'business_registration_number', 'tax_id', 'description',
            'is_active_client', 'contract_duration', 'documents', 
            'client_payments', 'payment_status',
            'contract_start_date', 'contract_end_date',
        ]
    
    def get_payment_status(self, obj):
        from django.utils import timezone
        import calendar
        from datetime import date
        
        if not obj.onboarding_date:
            return "Unknown"
        
        today = timezone.now().date()
        
        # Find the first unpaid month since onboarding
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
            # Check if any payments exist at all
            has_payments = ClientPayment.objects.filter(client=obj).exists()
            
            # Check if current month is paid early or if future payments exist
            current_payment = ClientPayment.objects.filter(
                client=obj,
                month=today.month,
                year=today.year,
                status__in=['paid', 'early_paid']
            ).first()
            
            if current_payment:
                if current_payment.status == 'early_paid':
                    return "Early Payment Received"
                return "Payment Received"
            
            if not has_payments and obj.onboarding_date > today:
                return "Upcoming"
                
            if not has_payments:
                return "Pending"

            return "Payment Received" # Default for "all caught up"

        # Calculate scheduled date threshold based on end of month (align with employee logic)
        _, last_day_target_month = calendar.monthrange(target_year, target_month)
        scheduled_date_threshold = date(target_year, target_month, last_day_target_month)
        
        days_diff = (scheduled_date_threshold - today).days
        
        if days_diff < 0:
            return "Overdue"
        elif days_diff == 0:
            return "Pay Client"
        elif 0 < days_diff <= 7:
            return "Payment date coming soon"
        else:
            return "Pending"

    def get_is_active_client(self, obj):
        return obj.status == 'active'

    def get_contract_duration(self, obj):
        if obj.contract_start_date and obj.contract_end_date:
            delta = obj.contract_end_date - obj.contract_start_date
            return delta.days // 30
        return None

    def get_payment_status_display(self, obj):
        # In the detail view, we can afford to be more accurate
        status = self.get_payment_status(obj)
        if status == "Payment Received": return "Paid"
        if status == "Early Payment Received": return "Early Paid"
        return status


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
            'payment_date',
            'description',
        ]

    def validate_client_name(self, value):
        
        queryset = Client.objects.filter(client_name=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("A client with this name already exists.")
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.payment_date:
             utils.calculate_next_payment_date(instance)
        utils.update_payment_status(instance)
        instance.save()
        return instance

   
#client list serializer
class ClientListSerializer(serializers.ModelSerializer):
  
    is_active_client = serializers.SerializerMethodField()
    payment_status_display = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='contact_email')
    phone = serializers.ReadOnlyField(source='contact_phone')
    company = serializers.ReadOnlyField(source='client_name')
    client_type_display = serializers.CharField(source='get_client_type_display', read_only=True)
   
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
            'next_payment_date',
            'last_payment_date',
            'current_month_payment_status',
            'payment_status_display',
            'email',
            'phone',
            'company',
            'client_type_display',
            "client_payments",
            'monthly_retainer',
            'videos_per_month', 'posters_per_month',
            'reels_per_month', 'stories_per_month',
            'address', 'city', 'state',
            'country', 'postal_code',

        ]

    def get_is_active_client(self, obj):
        return obj.status == 'active'

    def get_payment_status_display(self, obj):
        # For the list view, we avoid heavy calculations but verify the 'paid' status
        from .models import ClientPayment
        today = timezone.now().date()
        
        # Check if a payment actually exists for the current month if status is 'paid'
        if obj.current_month_payment_status in ['paid', 'early_paid']:
            exists = ClientPayment.objects.filter(
                client=obj,
                month=today.month,
                year=today.year,
                status__in=['paid', 'early_paid']
            ).exists()
            
            if not exists:
                # Use target month's end to decide 'Overdue' to align with detail view
                import calendar
                _, last_day = calendar.monthrange(today.year, today.month)
                eom = date(today.year, today.month, last_day)
                if today > eom:
                    return "Overdue"
                return "Pending"

        if hasattr(obj, 'next_payment_date') and obj.next_payment_date:
             days_until = (obj.next_payment_date - timezone.now().date()).days
        else:
             days_until = None

        if obj.current_month_payment_status == 'paid':
            return "Paid"
        elif obj.current_month_payment_status == 'early_paid':
            return "Early Paid"
        elif obj.current_month_payment_status == 'overdue':
            return "Overdue"
        elif days_until == 0:
            return "Due Today"
        elif days_until and days_until <= 7:
            return f"Due in {days_until} days"
        else:
            return "Pending"


#client payment detail serializer
class ClientPaymentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientPayment
        fields = '__all__'