from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import ClientVerification
from .serializers import (
    ClientVerificationSerializer, 
    PendingClientSerializer,
    ClientContentDetailSerializer,
    ContentItemSerializer,
    MarkContentVerifiedSerializer
)
from clientapp.models import Client
from datetime import datetime
from django.utils import timezone




# API 1: Get list of clients with pending verifications
class PendingClientsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Returns two arrays of clients with pending verifications:
        - current_month: Clients with pending work from current month
        - previous_months: Clients with pending work from previous months (overdue)
        """
        from django.utils import timezone
        
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        # Get all verifications that are not verified (verified_by is null)
        pending_verifications = ClientVerification.objects.filter(
            verified_by__isnull=True
        ).select_related('client')
        
        # Separate into current month and previous months
        current_month_data = {}
        previous_months_data = {}
        
        for verification in pending_verifications:
            client_id = verification.client.id
            created_date = verification.created_at.date()
            
            # Determine if this is current month or previous month
            is_current_month = (created_date.month == current_month and 
                              created_date.year == current_year)
            
            # Choose the appropriate dictionary
            target_dict = current_month_data if is_current_month else previous_months_data
            
            if client_id not in target_dict:
                target_dict[client_id] = {
                    'client_id': client_id,
                    'client_name': verification.client.client_name,
                    'completion_date': verification.completion_date or created_date,
                    'status': 'Pending',
                    'pending_count': 0
                }
            target_dict[client_id]['pending_count'] += 1
            
            # Update to the latest date
            current_date = verification.completion_date or created_date
            if current_date > target_dict[client_id]['completion_date']:
                target_dict[client_id]['completion_date'] = current_date
        
        # Convert to lists
        current_month_list = list(current_month_data.values())
        previous_months_list = list(previous_months_data.values())
        
        # Sort by completion_date (most recent first)
        current_month_list.sort(key=lambda x: x['completion_date'], reverse=True)
        previous_months_list.sort(key=lambda x: x['completion_date'], reverse=True)
        
        # Serialize both arrays
        current_month_serialized = PendingClientSerializer(current_month_list, many=True).data
        previous_months_serialized = PendingClientSerializer(previous_months_list, many=True).data
        
        return Response({
            'current_month': current_month_serialized,
            'previous_months': previous_months_serialized
        }, status=status.HTTP_200_OK)




# API 2: Get details of a specific client's content (videos and posters)
class ClientContentDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, client_id):
        """
        Returns detailed information about videos and posters for a specific client.
        Includes verification status for each content item.
        """
        # Check if client exists
        client = get_object_or_404(Client, id=client_id, is_deleted=False)
        
        # Get only videos and posters for this client
        videos = ClientVerification.objects.filter(
            client=client,
            content_type='video'
        ).order_by('-completion_date')
        
        posters = ClientVerification.objects.filter(
            client=client,
            content_type='poster'
        ).order_by('-completion_date')
        
        # Calculate totals (only for videos and posters)
        all_content = ClientVerification.objects.filter(
            client=client,
            content_type__in=['video', 'poster']
        )
        total_pending = all_content.filter(verified_by__isnull=True).count()
        total_verified = all_content.filter(verified_by__isnull=False).count()
        
        # Prepare response data
        data = {
            'client_id': client.id,
            'client_name': client.client_name,
            'videos': ContentItemSerializer(videos, many=True).data,
            'posters': ContentItemSerializer(posters, many=True).data,
            'total_pending': total_pending,
            'total_verified': total_verified,
        }
        
        return Response(data, status=status.HTTP_200_OK)


# API 3: Mark a content item as verified
class MarkContentVerifiedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Mark a specific content verification as done.
        Saves the current date and the current user as verified_by.
        
        Request body: { "verification_id": <id> }
        """
        serializer = MarkContentVerifiedSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        verification_id = serializer.validated_data['verification_id']
        
        # Get the verification object
        verification = get_object_or_404(ClientVerification, id=verification_id)
        
        # Check if already verified
        if verification.verified_by is not None:
            return Response(
                {'error': 'This content has already been verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as verified
        verification.verified_by = request.user
        verification.completion_date = timezone.now().date()
        verification.save()
        
        # Return updated verification data
        response_serializer = ContentItemSerializer(verification)
        return Response({
            'message': 'Content marked as verified successfully.',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)


# API 4: Get list of all completed/verified work
class CompletedWorkListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Returns list of all completed/verified work.
        Each item contains client info, content details, and verification info.
        """
        # Get all verified work (verified_by is not null)
        completed_verifications = ClientVerification.objects.filter(
            verified_by__isnull=False,
            content_type__in=['video', 'poster']
        ).select_related('client', 'verified_by').order_by('-completion_date')
        
        # Serialize the data
        serializer = ContentItemSerializer(completed_verifications, many=True)
        
        # Add client name to each item
        result = []
        for verification in completed_verifications:
            item_data = ContentItemSerializer(verification).data
            item_data['client_id'] = verification.client.id
            item_data['client_name'] = verification.client.client_name
            result.append(item_data)
        
        return Response({
            'completed_work': result,
            'total_count': len(result)
        }, status=status.HTTP_200_OK)

