from rest_framework import serializers
from .models import ContentVerification
from clientapp.models import Client
from django.utils import timezone
from django.db.models import Q

class ContentVerificationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    status = serializers.ReadOnlyField(source='verification_status')
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    # Target counts from client
    videos_target = serializers.IntegerField(source='client.videos_per_month', read_only=True)
    posters_target = serializers.IntegerField(source='client.posters_per_month', read_only=True)
    reels_target = serializers.IntegerField(source='client.reels_per_month', read_only=True)
    stories_target = serializers.IntegerField(source='client.stories_per_month', read_only=True)
    
    # Payment information
    payment_status = serializers.SerializerMethodField()
    is_paid = serializers.SerializerMethodField()
    
    # Progress percentages
    video_progress = serializers.SerializerMethodField()
    poster_progress = serializers.SerializerMethodField()
    reels_progress = serializers.SerializerMethodField()
    story_progress = serializers.SerializerMethodField()
    overall_progress = serializers.SerializerMethodField()

    class Meta:
        model = ContentVerification
        fields = [
            'id', 'client', 'client_name', 'month', 'year',
            'video', 'poster', 'reels', 'story',
            'videos_target', 'posters_target', 'reels_target', 'stories_target',
            'video_progress', 'poster_progress', 'reels_progress', 'story_progress',
            'overall_progress', 'status', 'verification_status',
            'payment_status', 'is_paid',
            'verified_at', 'verified_by', 'verified_by_name',
            'payment', 'created_at'
        ]
        read_only_fields = ['status', 'verification_status', 'verified_at', 'verified_by', 'payment']

    def get_payment_status(self, obj):
        return obj.payment_status
    
    def get_is_paid(self, obj):
        return obj.is_paid  # This returns True/False

    def get_video_progress(self, obj):
        target = obj.client.videos_per_month
        if target > 0:
            return min(100, int((obj.video / target) * 100))
        return 0

    def get_poster_progress(self, obj):
        target = obj.client.posters_per_month
        if target > 0:
            return min(100, int((obj.poster / target) * 100))
        return 0

    def get_reels_progress(self, obj):
        target = obj.client.reels_per_month
        if target > 0:
            return min(100, int((obj.reels / target) * 100))
        return 0

    def get_story_progress(self, obj):
        target = obj.client.stories_per_month
        if target > 0:
            return min(100, int((obj.story / target) * 100))
        return 0

    def get_overall_progress(self, obj):
        total_targets = sum([
            obj.client.videos_per_month,
            obj.client.posters_per_month,
            obj.client.reels_per_month,
            obj.client.stories_per_month
        ])
        
        if total_targets > 0:
            total_submitted = sum([obj.video, obj.poster, obj.reels, obj.story])
            return min(100, int((total_submitted / total_targets) * 100))
        return 0

class VerificationDashboardSerializer(serializers.ModelSerializer):
    current_verification = serializers.SerializerMethodField()
    previous_pending = serializers.SerializerMethodField()
    
    # Payment status
    payment_status = serializers.SerializerMethodField()
    is_paid = serializers.SerializerMethodField()
    
    # Client targets
    videos_target = serializers.IntegerField(source='videos_per_month', read_only=True)
    posters_target = serializers.IntegerField(source='posters_per_month', read_only=True)
    reels_target = serializers.IntegerField(source='reels_per_month', read_only=True)
    stories_target = serializers.IntegerField(source='stories_per_month', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'client_name', 
            'videos_target', 'posters_target', 'reels_target', 'stories_target',
            'current_verification', 'previous_pending', 'payment_status', 'is_paid'
        ]

    def get_current_verification(self, obj):
        from django.utils import timezone
        today = timezone.now()
        month = self.context.get('month', today.month)
        year = self.context.get('year', today.year)
        
        verification = ContentVerification.objects.filter(
            client=obj, month=month, year=year
        ).first()
        
        if verification:
            return ContentVerificationSerializer(verification).data
        
        # Create empty verification if doesn't exist
        return {
            'id': None,
            'month': month,
            'year': year,
            'video': 0,
            'poster': 0,
            'reels': 0,
            'story': 0,
            'videos_target': obj.videos_per_month,
            'posters_target': obj.posters_per_month,
            'reels_target': obj.reels_per_month,
            'stories_target': obj.stories_per_month,
            'status': 'pending',
            'verification_status': 'pending',
            'payment_status': self.get_payment_status(obj),
            'is_paid': self.get_is_paid(obj)
        }

    def get_payment_status(self, obj):
        month = self.context.get('month', timezone.now().month)
        year = self.context.get('year', timezone.now().year)
        
        try:
            payment = ClientPayment.objects.get(
                client=obj,
                month=month,
                year=year
            )
            return payment.status
        except ClientPayment.DoesNotExist:
            return 'no_payment'

    def get_is_paid(self, obj):
        payment_status = self.get_payment_status(obj)
        return payment_status in ['paid', 'early_paid']  # Returns True/False

    def get_previous_pending(self, obj):
        """Check if there are any pending verifications from previous months."""
        from django.utils import timezone
        today = timezone.now()
        current_month = self.context.get('month', today.month)
        current_year = self.context.get('year', today.year)
        
        # Get all pending verifications from previous months
        pending_verifications = ContentVerification.objects.filter(
            client=obj,
            verification_status__in=['pending', 'in_progress', 'pending_payment']
        ).exclude(
            Q(year=current_year, month=current_month)
        ).order_by('-year', '-month')
        
        if pending_verifications.exists():
            pending_data = []
            for verification in pending_verifications[:3]:  # Last 3 months
                pending_data.append({
                    'month': verification.month,
                    'year': verification.year,
                    'video': verification.video,
                    'poster': verification.poster,
                    'reels': verification.reels,
                    'story': verification.story,
                    'status': verification.verification_status,
                    'payment_status': verification.payment_status,
                    'is_paid': verification.is_paid
                })
            return pending_data
        return None