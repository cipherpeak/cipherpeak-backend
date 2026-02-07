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