from rest_framework import serializers
from .models import ClientVerification
from clientapp.models import Client

class VerificationDashboardSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    client_name = serializers.CharField()
    poster_quota = serializers.IntegerField()
    video_quota = serializers.IntegerField()
    posted_posters = serializers.IntegerField()
    posted_videos = serializers.IntegerField()
    pending_videos = serializers.IntegerField()
    pending_posters = serializers.IntegerField()
    has_overdue = serializers.BooleanField()
from rest_framework import serializers
# Correct imports:
from verification.models import ClientVerification  # Only ClientVerification from verification
from clientapp.models import Client  # Client from clientapp
from datetime import date

class ClientVerificationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    content_type_display = serializers.CharField(source='get_content_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ClientVerification
        fields = [
            'id',
            'client', 'client_name',
            'content_type', 'content_type_display',
            'title', 'description',
            'posted_date', 'platform', 'platform_display', 'content_url',
            'status', 'status_display',
            'verified_by', 'verified_by_name', 'verified_date', 'verification_notes',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'verified_date']


class PostedContentCreateSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    content_type = serializers.ChoiceField(choices=['poster', 'video'])
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False, allow_null=True)
    content_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate(self, data):
        # Validate client exists
        try:
            client = Client.objects.get(id=data['client_id'], is_deleted=False)
            data['client'] = client
        except Client.DoesNotExist:
            raise serializers.ValidationError({"client_id": "Client not found or deleted"})
        
        # Set default month/year if not provided
        today = date.today()
        if 'month' not in data:
            data['month'] = today.month
        if 'year' not in data:
            data['year'] = today.year
        
        return data


class DashboardSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    client_name = serializers.CharField()
    poster_quota = serializers.IntegerField()
    video_quota = serializers.IntegerField()
    posted_posters = serializers.IntegerField()
    posted_videos = serializers.IntegerField()
    is_verified = serializers.BooleanField()
    industry = serializers.CharField(allow_null=True)
    has_overdue = serializers.BooleanField(default=False)


class UpdateQuotaSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    content_type = serializers.ChoiceField(choices=['posters', 'videos'])
    quota = serializers.IntegerField(min_value=0)


class VerifyClientSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)


class BulkUpdateVerificationSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    notes = serializers.CharField(required=False, allow_blank=True)
    is_verified = serializers.BooleanField()
    industry = serializers.CharField()

class MarkClientVerifiedSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    month = serializers.IntegerField(required=False)
    year = serializers.IntegerField(required=False)

class UpdatePostedCountSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    content_type = serializers.ChoiceField(choices=['posters', 'videos'])
    count = serializers.IntegerField()
    month = serializers.IntegerField(required=False)
    year = serializers.IntegerField(required=False)

class UpdateQuotaSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    content_type = serializers.ChoiceField(choices=['posters', 'videos', 'quota_posters', 'quota_videos'])
    quota = serializers.IntegerField()