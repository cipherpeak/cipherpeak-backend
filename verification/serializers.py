from rest_framework import serializers
from .models import ClientVerification
from django.utils import timezone
from clientapp.models import Client
from django.db.models import Count, Q

class ClientVerificationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.client_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)

    class Meta:
        model = ClientVerification
        fields = [
            'id', 'client', 'client_name', 'content_type', 
            'completion_date', 'description', 'verified_by', 
            'verified_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'verified_by']

    def validate(self, data):
        client = data.get('client')
        content_type = data.get('content_type')
        completion_date = data.get('completion_date', timezone.now().date())
        
        if not client or not content_type:
            return data

        # Get the month and year from completion_date
        month = completion_date.month
        year = completion_date.year

        # Get current count for this content type in this month
        current_count = ClientVerification.objects.filter(
            client=client,
            content_type=content_type,
            completion_date__year=year,
            completion_date__month=month
        ).count()

        # Check against limit
        limit = 0
        if content_type == 'video':
            limit = client.videos_per_month
        elif content_type == 'poster':
            limit = client.posters_per_month
        elif content_type == 'reel':
            limit = client.reels_per_month
        elif content_type == 'story':
            limit = client.stories_per_month

        # If we are creating a new record (no instance), current_count + 1 should not exceed limit
        if not self.instance:
            if current_count >= limit:
                raise serializers.ValidationError(
                    f"Monthly limit of {limit} for {content_type}s reached for {client.client_name} in {completion_date.strftime('%B %Y')}."
                )
        
        return data

