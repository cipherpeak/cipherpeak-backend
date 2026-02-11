from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime, date
import calendar

from verification.models import ClientVerification  # Only ClientVerification from verification
from clientapp.models import Client  # Client from clientapp
from .serializers import (
    DashboardSerializer,
    PostedContentCreateSerializer,
    ClientVerificationSerializer,
    UpdateQuotaSerializer,
    VerifyClientSerializer,
    BulkUpdateVerificationSerializer
)



class VerificationDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get verification dashboard for all clients"""
        today = timezone.now().date()
        
        # Get month/year from query params
        try:
            current_month = int(request.query_params.get('month', today.month))
            current_year = int(request.query_params.get('year', today.year))
        except (ValueError, TypeError):
            current_month = today.month
            current_year = today.year
        
        # Get all active clients
        clients = Client.objects.filter(
            is_deleted=False
        ).exclude(
            status__in=['terminated', 'prospect']
        ).order_by('client_name')
        
        dashboard_data = []
        
        for client in clients:
            # Get posted counts for the selected month
            posters_posted = ClientVerification.objects.filter(
                client=client,
                content_type='poster',
                posted_date__month=current_month,
                posted_date__year=current_year,
                status__in=['posted', 'approved']
            ).count()
            
            videos_posted = ClientVerification.objects.filter(
                client=client,
                content_type='video',
                posted_date__month=current_month,
                posted_date__year=current_year,
                status__in=['posted', 'approved']
            ).count()
            
            # Check for overdue items (from previous months)
            has_overdue = ClientVerification.objects.filter(
                client=client,
                status__in=['draft', 'posted'],
                posted_date__lt=date(current_year, current_month, 1)
            ).exists()
            
            # Check if client is verified for the month
            is_verified = (
                posters_posted >= client.posters_per_month and 
                videos_posted >= client.videos_per_month
            )
            
            dashboard_data.append({
                'client_id': client.id,
                'client_name': client.client_name,
                'poster_quota': client.posters_per_month,
                'video_quota': client.videos_per_month,
                'posted_posters': posters_posted,
                'posted_videos': videos_posted,
                'is_verified': is_verified,
                'industry': client.get_industry_display() if client.industry else None,
                'has_overdue': has_overdue
            })
        
        serializer = DashboardSerializer(dashboard_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddPostedContentView(APIView):
    """Add a posted content record"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PostedContentCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client = data['client']
            content_type = data['content_type']
            month = data['month']
            year = data['year']
            
            # Create posted date (first day of the month)
            posted_date = date(year, month, 1)
            
            # Check if quota allows more posts
            current_count = ClientVerification.objects.filter(
                client=client,
                content_type=content_type,
                posted_date__month=month,
                posted_date__year=year,
                status__in=['posted', 'approved']
            ).count()
            
            quota = client.posters_per_month if content_type == 'poster' else client.videos_per_month
            
            if current_count >= quota:
                return Response({
                    'error': f'Quota reached. Maximum {quota} {content_type}s allowed per month.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the verification record
            verification = ClientVerification.objects.create(
                client=client,
                content_type=content_type,
                title=data.get('title', ''),
                description=data.get('description', ''),
                posted_date=posted_date,
                platform=data.get('platform'),
                content_url=data.get('content_url', ''),
                status='posted',
                created_by=request.user
            )
            
            # Get updated counts
            stats = client.get_posted_stats(month=month, year=year)
            
            return Response({
                'success': True,
                'message': f'{content_type.capitalize()} posted successfully',
                'verification_id': verification.id,
                'posted_posters': stats['posters_posted'],
                'posted_videos': stats['videos_posted'],
                'is_verified': stats['is_verified']
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RemovePostedContentView(APIView):
    """Remove the most recent posted content"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PostedContentCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client = data['client']
            content_type = data['content_type']
            month = data['month']
            year = data['year']
            
            # Find the most recent posted item for this client and month
            recent_item = ClientVerification.objects.filter(
                client=client,
                content_type=content_type,
                posted_date__month=month,
                posted_date__year=year,
                status__in=['posted', 'approved']
            ).order_by('-created_at').first()
            
            if recent_item:
                recent_item.delete()
                message = f'Removed {content_type} posted on {recent_item.created_at.strftime("%Y-%m-%d")}'
            else:
                message = f'No {content_type} found to remove'
            
            # Get updated stats
            stats = client.get_posted_stats(month=month, year=year)
            
            return Response({
                'success': True,
                'message': message,
                'posted_posters': stats['posters_posted'],
                'posted_videos': stats['videos_posted'],
                'is_verified': stats['is_verified']
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyClientMonthView(APIView):
    """Mark client as verified for the month"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = VerifyClientSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client_id = data['client_id']
            month = data.get('month')
            year = data.get('year')
            
            client = get_object_or_404(Client, id=client_id, is_deleted=False)
            
            today = timezone.now().date()
            month = month or today.month
            year = year or today.year
            
            # Check if client meets quotas
            stats = client.get_posted_stats(month=month, year=year)
            
            if not stats['is_verified']:
                return Response({
                    'error': 'Client does not meet quotas',
                    'details': {
                        'posters_needed': stats['posters_quota'] - stats['posters_posted'],
                        'videos_needed': stats['videos_quota'] - stats['videos_posted']
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark all posted items as approved
            posted_items = ClientVerification.objects.filter(
                client=client,
                posted_date__month=month,
                posted_date__year=year,
                status='posted'
            )
            
            updated_count = posted_items.count()
            
            for item in posted_items:
                item.approve(user=request.user)
            
            return Response({
                'success': True,
                'message': f'Client verified for {month}/{year}',
                'verified_items': updated_count,
                'is_verified': True
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetClientPostedDetailsView(APIView):
    """Get all posted content for a specific client and month"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, client_id):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        today = timezone.now().date()
        month = int(month) if month else today.month
        year = int(year) if year else today.year
        
        client = get_object_or_404(Client, id=client_id, is_deleted=False)
        
        # Get all posted content for this month
        posted_content = ClientVerification.objects.filter(
            client=client,
            posted_date__month=month,
            posted_date__year=year
        ).order_by('content_type', '-posted_date', '-created_at')
        
        # Get statistics
        stats = client.get_posted_stats(month=month, year=year)
        
        serializer = ClientVerificationSerializer(posted_content, many=True)
        
        return Response({
            'client_id': client_id,
            'client_name': client.client_name,
            'month': month,
            'year': year,
            'statistics': stats,
            'posted_content': serializer.data,
            'total_count': posted_content.count()
        }, status=status.HTTP_200_OK)


class UpdateQuotaView(APIView):
    """Update client quotas"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = UpdateQuotaSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client_id = data['client_id']
            content_type = data['content_type']
            quota = data['quota']
            
            client = get_object_or_404(Client, id=client_id, is_deleted=False)
            
            if content_type == 'posters':
                client.posters_per_month = quota
            elif content_type == 'videos':
                client.videos_per_month = quota
            
            client.save()
            
            return Response({
                'success': True,
                'message': f'{content_type.capitalize()} quota updated to {quota}',
                'quota': quota
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkUpdateVerificationStatusView(APIView):
    """Bulk update verification status for a client's monthly content"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BulkUpdateVerificationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client_id = data['client_id']
            month = data.get('month')
            year = data.get('year')
            status = data['status']
            notes = data.get('notes', '')
            
            client = get_object_or_404(Client, id=client_id, is_deleted=False)
            
            today = timezone.now().date()
            month = month or today.month
            year = year or today.year
            
            # Get items to update
            items_to_update = ClientVerification.objects.filter(
                client=client,
                posted_date__month=month,
                posted_date__year=year,
                status='posted'  # Only update items that are posted
            )
            
            updated_count = items_to_update.count()
            
            # Update items
            for item in items_to_update:
                if status == 'approved':
                    item.approve(user=request.user, notes=notes)
                else:
                    item.status = status
                    item.verification_notes = notes
                    item.save()
            
            return Response({
                'success': True,
                'message': f'Updated {updated_count} items to {status}',
                'updated_count': updated_count
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeletePostedContentView(APIView):
    """Delete a specific posted content item"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, verification_id):
        verification = get_object_or_404(ClientVerification, id=verification_id)
        
        # Store info before deletion
        client_id = verification.client.id
        content_type = verification.content_type
        month = verification.posted_date.month
        year = verification.posted_date.year
        
        verification.delete()
        
        # Get updated stats
        client = get_object_or_404(Client, id=client_id)
        stats = client.get_posted_stats(month=month, year=year)
        
        return Response({
            'success': True,
            'message': f'Deleted {content_type} posted on {verification.posted_date}',
            'posted_posters': stats['posters_posted'],
            'posted_videos': stats['videos_posted'],
            'is_verified': stats['is_verified']
        }, status=status.HTTP_200_OK)