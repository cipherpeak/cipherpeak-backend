from rest_framework import serializers
from .models import ClientVerification,MonthlyVerification
from django.utils import timezone

class ClientVerificationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    client_monthly_poster  = serializers.CharField(source='client.posters_per_month', read_only=True)
    client_monthly_videos  = serializers.CharField(source='client.videos_per_month', read_only=True)
    
    posters_completed = serializers.SerializerMethodField()
    videos_completed = serializers.SerializerMethodField()
    posters_posted = serializers.SerializerMethodField()
    videos_posted = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = ClientVerification
        fields = [
            'id', 'client_name', 'is_completed', 
            'client_monthly_poster', 'client_monthly_videos',
            'posters_completed', 'videos_completed', 
            'posters_posted', 'videos_posted', 'is_verified'
        ]

    def get_monthly_stat(self, obj, field_name):
        
        now = timezone.now()
        monthly_stat = MonthlyVerification.objects.filter(
            clientverification=obj,
            month=now.month,
            year=now.year
        ).first()
        if monthly_stat:
            return getattr(monthly_stat, field_name)
        return 0

    def get_posters_completed(self, obj):
        return self.get_monthly_stat(obj, 'posters_completed')

    def get_videos_completed(self, obj):
        return self.get_monthly_stat(obj, 'videos_completed')

    def get_posters_posted(self, obj):
        return self.get_monthly_stat(obj, 'posters_posted')

    def get_videos_posted(self, obj):
        return self.get_monthly_stat(obj, 'videos_posted')

    def get_is_verified(self, obj):
        return self.get_monthly_stat(obj, 'is_verified')
