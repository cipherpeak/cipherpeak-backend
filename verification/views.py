from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from .models import ClientVerification
from .serializers import ClientVerificationSerializer
from clientapp.models import Client
from datetime import datetime

class ClientVerificationListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Auto-create verification objects for active clients
        from django.utils import timezone
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        active_clients = Client.objects.filter(status='active', is_deleted=False)
        
        for client in active_clients:
            # Check for each content type
            content_types = [
                ('video', client.videos_per_month),
                ('poster', client.posters_per_month),
                ('reel', client.reels_per_month),
                ('story', client.stories_per_month)
            ]
            
            for type_code, required_count in content_types:
                if required_count > 0:
                    current_count = ClientVerification.objects.filter(
                        client=client,
                        content_type=type_code,
                        completion_date__month=current_month,
                        completion_date__year=current_year
                    ).count()
                    
                    rows_to_create = required_count - current_count
                    if rows_to_create > 0:
                        for _ in range(rows_to_create):
                            ClientVerification.objects.create(
                                client=client,
                                content_type=type_code,
                                completion_date=today,
                                verified_by=None
                            )

        verifications = ClientVerification.objects.all()
        
        # Manual filtering to match previous functionality
        client_id = request.query_params.get('client')
        content_type = request.query_params.get('content_type')
        completion_date = request.query_params.get('completion_date')
        verified_by = request.query_params.get('verified_by')

        if client_id:
            verifications = verifications.filter(client_id=client_id)
        if content_type:
            verifications = verifications.filter(content_type=content_type)
        if completion_date:
            verifications = verifications.filter(completion_date=completion_date)
        if verified_by:
            verifications = verifications.filter(verified_by_id=verified_by)

        serializer = ClientVerificationSerializer(verifications, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ClientVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(verified_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
