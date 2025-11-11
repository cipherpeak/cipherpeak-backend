# client/serializers.py
from rest_framework import serializers
from .models import Client, ClientDocument

class ClientSerializer(serializers.ModelSerializer):
    total_content_per_month = serializers.ReadOnlyField()
    is_active_client = serializers.ReadOnlyField()
    contract_duration = serializers.ReadOnlyField()
    is_payment_overdue = serializers.ReadOnlyField()
    days_until_next_payment = serializers.ReadOnlyField()
    payment_status_display = serializers.ReadOnlyField()
    is_early_payment = serializers.ReadOnlyField()
    early_payment_days = serializers.ReadOnlyField()
    
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
            'payment_cycle',
            'payment_date',
            'next_payment_date',
            'current_month_payment_status',
            'last_payment_date',
            'monthly_retainer',
            # New payment timing fields
            'payment_timing',
            'early_payment_date',
            'early_payment_amount',
            'early_payment_notes',
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
            'total_content_per_month',
            'is_active_client',
            'contract_duration',
            'is_payment_overdue',
            'days_until_next_payment',
            'payment_status_display',
            'is_early_payment',
            'early_payment_days',
        ]
        read_only_fields = [
            'created_at', 
            'updated_at', 
            'next_payment_date',
            'total_content_per_month',
            'is_active_client',
            'contract_duration',
            'is_payment_overdue',
            'days_until_next_payment',
            'payment_status_display',
            'is_early_payment',
            'early_payment_days',
            'payment_timing',
            'early_payment_date',
            'early_payment_amount',
            'early_payment_notes',
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
    
    def validate(self, data):
        """Validate contract dates and payment data"""
        contract_start_date = data.get('contract_start_date')
        contract_end_date = data.get('contract_end_date')
        payment_date = data.get('payment_date')
        
        # Validate contract dates
        if contract_start_date and contract_end_date:
            if contract_end_date <= contract_start_date:
                raise serializers.ValidationError({
                    "contract_end_date": "Contract end date must be after start date."
                })
        
        # Validate payment date
        if payment_date is not None:
            if payment_date < 1 or payment_date > 31:
                raise serializers.ValidationError({
                    "payment_date": "Payment date must be between 1 and 31."
                })
        
        # Validate monthly retainer
        monthly_retainer = data.get('monthly_retainer')
        if monthly_retainer is not None and monthly_retainer < 0:
            raise serializers.ValidationError({
                "monthly_retainer": "Monthly retainer cannot be negative."
            })
        
        # Validate early payment amount
        early_payment_amount = data.get('early_payment_amount')
        if early_payment_amount is not None and early_payment_amount < 0:
            raise serializers.ValidationError({
                "early_payment_amount": "Early payment amount cannot be negative."
            })
        
        return data
    
    def create(self, validated_data):
        """Override create to handle automatic next_payment_date calculation"""
        instance = super().create(validated_data)
        # Next payment date will be automatically calculated in the model's save method
        return instance
    
    def update(self, instance, validated_data):
        """Override update to handle automatic next_payment_date calculation"""
        # Store original payment date to check if it changed
        original_payment_date = instance.payment_date
        original_payment_cycle = instance.payment_cycle
        
        instance = super().update(instance, validated_data)
        
        # If payment date or cycle changed, recalculate next payment date
        if (validated_data.get('payment_date') != original_payment_date or 
            validated_data.get('payment_cycle') != original_payment_cycle):
            instance.calculate_next_payment_date()
            instance.save()
        
        return instance

class ClientPaymentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating payment status"""
    payment_status = serializers.ChoiceField(
        choices=Client.PAYMENT_STATUS_CHOICES,
        required=False
    )
    mark_as_paid = serializers.BooleanField(default=False)
    mark_as_early_paid = serializers.BooleanField(default=False)
    payment_date = serializers.DateField(required=False)
    amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False,
        min_value=0
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate payment update data"""
        mark_as_paid = data.get('mark_as_paid')
        mark_as_early_paid = data.get('mark_as_early_paid')
        payment_status = data.get('payment_status')
        
        # Cannot mark as paid and set payment status simultaneously
        if mark_as_paid and payment_status:
            raise serializers.ValidationError({
                "mark_as_paid": "Cannot set both mark_as_paid and payment_status. Use mark_as_paid to automatically set status to paid."
            })
        
        # Validate early payment requirements
        if mark_as_early_paid:
            if not data.get('payment_date'):
                raise serializers.ValidationError({
                    "payment_date": "Payment date is required for early payments."
                })
        
        return data
    
    def update(self, instance, validated_data):
        payment_status = validated_data.get('payment_status')
        mark_as_paid = validated_data.get('mark_as_paid')
        mark_as_early_paid = validated_data.get('mark_as_early_paid')
        payment_date = validated_data.get('payment_date')
        amount = validated_data.get('amount')
        notes = validated_data.get('notes')
        
        if mark_as_early_paid:
            # Mark as early payment
            instance.mark_early_payment(
                payment_date=payment_date,
                amount=amount,
                notes=notes
            )
        elif mark_as_paid:
            # Mark as regular paid payment
            instance.mark_payment_as_paid(
                payment_date=payment_date,
                amount=amount,
                notes=notes
            )
        elif payment_status:
            # Manually set payment status
            instance.current_month_payment_status = payment_status
            instance.save()
        
        return instance

class ClientEarlyPaymentSerializer(serializers.Serializer):
    """Serializer specifically for early payments"""
    payment_date = serializers.DateField(required=True)
    amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False,
        min_value=0
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        """Mark payment as early paid"""
        instance.mark_early_payment(
            payment_date=validated_data['payment_date'],
            amount=validated_data.get('amount'),
            notes=validated_data.get('notes', '')
        )
        return instance

class ClientDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    
    class Meta:
        model = ClientDocument
        fields = '__all__'
        read_only_fields = ['uploaded_at', 'uploaded_by']

class ClientListSerializer(serializers.ModelSerializer):
    """Simplified serializer for client lists"""
    total_content_per_month = serializers.ReadOnlyField()
    is_active_client = serializers.ReadOnlyField()
    payment_status_display = serializers.ReadOnlyField()
    is_payment_overdue = serializers.ReadOnlyField()
    is_early_payment = serializers.ReadOnlyField()
    payment_timing_display = serializers.CharField(source='get_payment_timing_display', read_only=True)
    
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
            'monthly_retainer',
            'payment_cycle',
            'next_payment_date',
            'current_month_payment_status',
            'payment_timing',
            'payment_timing_display',
            'early_payment_date',
            'total_content_per_month',
            'is_active_client',
            'payment_status_display',
            'is_payment_overdue',
            'is_early_payment',
            'created_at',
        ]

class ClientStatsSerializer(serializers.Serializer):
    """Serializer for client statistics"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    overdue_payments = serializers.IntegerField()
    early_payments = serializers.IntegerField()
    total_monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    clients_by_industry = serializers.DictField()
    clients_by_status = serializers.DictField()
    clients_by_payment_status = serializers.DictField()
    clients_by_payment_timing = serializers.DictField()

class ClientPaymentTimelineSerializer(serializers.ModelSerializer):
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