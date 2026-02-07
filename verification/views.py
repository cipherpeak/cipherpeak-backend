from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import ClientVerification
from clientapp.models import Client
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Sum, Q
from .serializers import (
    VerificationDashboardSerializer,
    MarkClientVerifiedSerializer,
    UpdatePostedCountSerializer,
    UpdateQuotaSerializer
)


class VerificationDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Returns a summary for ALL active clients for the current month, formatted for the dashboard.
        """
        today = timezone.now().date()
        
        # Get month/year from query params, default to current month/year
        try:
            current_month = int(request.query_params.get('month', today.month))
            current_year = int(request.query_params.get('year', today.year))
        except (ValueError, TypeError):
            current_month = today.month
            current_year = today.year
            
        # Target date for logic consistency
        target_date = date(current_year, current_month, 1)
        start_of_month = timezone.make_aware(datetime(current_year, current_month, 1))
        
        # Get all active clients
        clients = Client.objects.filter(is_deleted=False).exclude(status='terminated')
        
        dashboard_data = []
        
        for client in clients:
            # Quotas (Total)
            poster_quota = client.posters_per_month
            video_quota = client.videos_per_month
            
            # Posted (Verified)
            base_verified = ClientVerification.objects.filter(
                client=client,
                verified_by__isnull=False,
                completion_date__month=current_month,
                completion_date__year=current_year
            )
            
            posted_videos = base_verified.filter(content_type='video').count()
            posted_posters = base_verified.filter(content_type='poster').count()
            
            # Pending (Unverified)
            base_pending = ClientVerification.objects.filter(
                client=client,
                verified_by__isnull=True
            )
            
            pending_videos = base_pending.filter(content_type='video').count()
            pending_posters = base_pending.filter(content_type='poster').count()
            
            # Roll-over flag
            has_overdue = base_pending.filter(
                Q(completion_date__lt=target_date) | 
                Q(created_at__lt=start_of_month)
            ).exists()
            
            is_verified = (
                posted_posters >= poster_quota and 
                posted_videos >= video_quota and 
                pending_posters == 0 and
                pending_videos == 0
            )
            
            dashboard_data.append({
                'client_id': client.id,
                'client_name': client.client_name,
                'poster_quota': poster_quota,
                'video_quota': video_quota,
                'posted_posters': posted_posters,
                'posted_videos': posted_videos,
                'pending_videos': pending_videos,
                'pending_posters': pending_posters,
                'has_overdue': has_overdue,
                'is_verified': is_verified,
                'industry': client.get_industry_display() if client.industry else 'N/A' 
            })
            
        serializer = VerificationDashboardSerializer(dashboard_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MarkClientVerifiedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MarkClientVerifiedSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        client_id = serializer.validated_data.get('client_id')
        client = get_object_or_404(Client, id=client_id)
        
        today = timezone.now().date()
        current_month = serializer.validated_data.get('month', today.month)
        current_year = serializer.validated_data.get('year', today.year)
        target_date = date(int(current_year), int(current_month), 1)
        
        pending_verifications = ClientVerification.objects.filter(
            client=client,
            verified_by__isnull=True
        )
        
        count = pending_verifications.count()
        
        if count > 0:
            pending_verifications.update(
                verified_by=request.user,
                completion_date=target_date,
                updated_at=timezone.now()
            )
        else:
            ClientVerification.objects.create(
                client=client,
                content_type='poster', 
                verified_by=request.user,
                completion_date=target_date,
                description=f"Monthly verification sign-off for {target_date.strftime('%B %Y')}",
                updated_at=timezone.now()
            )
        
        return Response({
            'message': f'Successfully verified {client.client_name}',
            'count': count
        }, status=status.HTTP_200_OK)


class UpdatePostedCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = UpdatePostedCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        client_id = serializer.validated_data.get('client_id')
        content_type = serializer.validated_data.get('content_type')
        new_count = serializer.validated_data.get('count')
            
        client = get_object_or_404(Client, id=client_id)
        
        type_map = {'posters': 'poster', 'videos': 'video'}
        db_type = type_map.get(content_type)
        
        today = timezone.now().date()
        current_month = serializer.validated_data.get('month', today.month)
        current_year = serializer.validated_data.get('year', today.year)
        target_date = date(int(current_year), int(current_month), 1)
        
        existing_items = ClientVerification.objects.filter(
            client=client,
            content_type=db_type,
            completion_date__month=current_month,
            completion_date__year=current_year
        )
        
        current_count = existing_items.count()
        
        if int(new_count) > current_count:
            to_create = int(new_count) - current_count
            placeholders = []
            for _ in range(to_create):
                placeholders.append(ClientVerification(
                    client=client,
                    content_type=db_type,
                    verified_by=None,
                    completion_date=target_date,
                    description=f"Auto-generated for {content_type} count update",
                    updated_at=timezone.now()
                ))
            ClientVerification.objects.bulk_create(placeholders)
            message = f"Added {to_create} pending {db_type} items"
        elif int(new_count) < current_count:
            to_remove = current_count - int(new_count)
            unverified_to_remove = existing_items.filter(verified_by__isnull=True).order_by('-id')[:to_remove]
            remaining = to_remove - unverified_to_remove.count()
            ids_to_remove = list(unverified_to_remove.values_list('id', flat=True))
            
            if remaining > 0:
                verified_to_remove = existing_items.filter(verified_by__isnull=False).order_by('-id')[:remaining]
                ids_to_remove.extend(list(verified_to_remove.values_list('id', flat=True)))
                
            ClientVerification.objects.filter(id__in=ids_to_remove).delete()
            message = f"Removed {to_remove} {db_type} items"
        else:
            message = "No changes needed"
            
        return Response({'message': message, 'count': new_count}, status=status.HTTP_200_OK)


class UpdateQuotaView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = UpdateQuotaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        client_id = serializer.validated_data.get('client_id')
        content_type = serializer.validated_data.get('content_type')
        new_quota = serializer.validated_data.get('quota')
            
        client = get_object_or_404(Client, id=client_id)
        
        if content_type == 'quota_posters' or content_type == 'posters':
            client.posters_per_month = int(new_quota)
        elif content_type == 'quota_videos' or content_type == 'videos':
            client.videos_per_month = int(new_quota)
        
        client.save()
        return Response({'message': 'Quota updated successfully', 'quota': new_quota}, status=status.HTTP_200_OK)
