from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from django.db.models import Q
from clientapp.models import Client, ClientPayment
from .models import ContentVerification
from .serializers import ContentVerificationSerializer, VerificationDashboardSerializer

class VerificationDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        # If month/year not provided, use current month/year
        today = timezone.now()
        month = int(month) if month else today.month
        year = int(year) if year else today.year
        
        clients = Client.objects.filter(is_deleted=False, status='active')
        serializer = VerificationDashboardSerializer(
            clients, 
            many=True, 
            context={'month': month, 'year': year}
        )
        
        # Get verifications for summary
        verifications = ContentVerification.objects.filter(month=month, year=year)
        
        # Count by status
        completed_count = verifications.filter(verification_status='completed').count()
        pending_payment_count = verifications.filter(verification_status='pending_payment').count()
        in_progress_count = verifications.filter(verification_status='in_progress').count()
        pending_count = verifications.filter(verification_status='pending').count()
        
        # Get payment summary
        payments = ClientPayment.objects.filter(month=month, year=year)
        paid_count = payments.filter(status__in=['paid', 'early_paid']).count()
        
        return Response({
            'summary': {
                'month': month,
                'year': year,
                'total_clients': clients.count(),
                'completed': completed_count,
                'pending_payment': pending_payment_count,
                'in_progress': in_progress_count,
                'pending': pending_count,
                'paid_clients': paid_count
            },
            'clients': serializer.data
        })

class ContentVerificationSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        client_id = request.data.get('client')
        month = request.data.get('month')
        year = request.data.get('year')
        
        if not client_id:
            return Response({'error': 'Client ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use current month/year if not provided
        today = timezone.now()
        month = int(month) if month else today.month
        year = int(year) if year else today.year
            
        try:
            client = Client.objects.get(id=client_id, is_deleted=False, status='active')
        except Client.DoesNotExist:
            return Response({'error': 'Client not found or inactive'}, status=status.HTTP_404_NOT_FOUND)

        # Check if client has content targets set
        if client.videos_per_month == 0 and client.posters_per_month == 0 and \
           client.reels_per_month == 0 and client.stories_per_month == 0:
            return Response({
                'error': 'Client does not have content targets set. Please set targets in client profile.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate input counts
        errors = {}
        
        # Get submitted counts (default to 0 if not provided)
        submitted_video = int(request.data.get('video', 0))
        submitted_poster = int(request.data.get('poster', 0))
        submitted_reels = int(request.data.get('reels', 0))
        submitted_story = int(request.data.get('story', 0))
        
        # Check if counts exceed targets
        if submitted_video > client.videos_per_month:
            errors['video'] = f'Cannot exceed monthly target of {client.videos_per_month} videos'
        
        if submitted_poster > client.posters_per_month:
            errors['poster'] = f'Cannot exceed monthly target of {client.posters_per_month} posters'
        
        if submitted_reels > client.reels_per_month:
            errors['reels'] = f'Cannot exceed monthly target of {client.reels_per_month} reels'
        
        if submitted_story > client.stories_per_month:
            errors['story'] = f'Cannot exceed monthly target of {client.stories_per_month} stories'
        
        if errors:
            return Response({
                'error': 'Content counts exceed monthly targets',
                'details': errors,
                'targets': {
                    'videos_per_month': client.videos_per_month,
                    'posters_per_month': client.posters_per_month,
                    'reels_per_month': client.reels_per_month,
                    'stories_per_month': client.stories_per_month
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create verification
        verification, created = ContentVerification.objects.get_or_create(
            client=client,
            month=month,
            year=year
        )
        
        # Update content counts
        verification.video = submitted_video
        verification.poster = submitted_poster
        verification.reels = submitted_reels
        verification.story = submitted_story
        verification.verified_by = request.user
        
        verification.save()  # This will auto-calculate status
        
        # Check payment status
        try:
            payment = ClientPayment.objects.get(
                client=client,
                month=month,
                year=year
            )
            payment_status = payment.status
            is_paid = payment_status in ['paid', 'early_paid']
        except ClientPayment.DoesNotExist:
            payment_status = 'no_payment'
            is_paid = False
        
        serializer = ContentVerificationSerializer(verification)
        return Response({
            'message': 'Verification updated successfully',
            'data': serializer.data,
            'payment_info': {
                'status': payment_status,
                'is_paid': is_paid  # True/False value
            },
            'summary': {
                'total_submitted': verification.video + verification.poster + verification.reels + verification.story,
                'total_target': client.videos_per_month + client.posters_per_month + client.reels_per_month + client.stories_per_month,
                'completion_percentage': verification.progress_percentage
            }
        }, status=status.HTTP_200_OK)
       
class PendingVerificationsView(APIView):
    """View to get all pending verifications across months"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        # If month/year provided, get specific month's pending
        if month and year:
            verifications = ContentVerification.objects.filter(
                month=int(month),
                year=int(year),
                verification_status__in=['pending', 'in_progress', 'pending_payment']
            )
        else:
            # Get all pending verifications grouped by month
            verifications = ContentVerification.objects.filter(
                verification_status__in=['pending', 'in_progress', 'pending_payment']
            ).order_by('-year', '-month')
        
        # Group by month and status
        grouped_data = {}
        for verification in verifications:
            key = f"{verification.year}-{verification.month:02d}"
            if key not in grouped_data:
                grouped_data[key] = {
                    'month': verification.month,
                    'year': verification.year,
                    'pending': [],
                    'in_progress': [],
                    'pending_payment': []
                }
            
            serializer = ContentVerificationSerializer(verification)
            verification_data = serializer.data
            
            if verification.verification_status == 'pending_payment':
                grouped_data[key]['pending_payment'].append(verification_data)
            elif verification.verification_status == 'in_progress':
                grouped_data[key]['in_progress'].append(verification_data)
            else:
                grouped_data[key]['pending'].append(verification_data)
        
        # Create summary
        total_pending = sum(len(group['pending']) for group in grouped_data.values())
        total_in_progress = sum(len(group['in_progress']) for group in grouped_data.values())
        total_pending_payment = sum(len(group['pending_payment']) for group in grouped_data.values())
        
        return Response({
            'summary': {
                'total_pending': total_pending,
                'total_in_progress': total_in_progress,
                'total_pending_payment': total_pending_payment,
                'total_all': total_pending + total_in_progress + total_pending_payment
            },
            'pending_verifications': list(grouped_data.values())
        })

class ClientContentTargetsView(APIView):
    """Get content targets for a client"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            client = Client.objects.get(pk=pk, is_deleted=False)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'client_id': client.id,
            'client_name': client.client_name,
            'content_targets': {
                'videos_per_month': client.videos_per_month,
                'posters_per_month': client.posters_per_month,
                'reels_per_month': client.reels_per_month,
                'stories_per_month': client.stories_per_month
            },
            'total_content_per_month': client.total_content_per_month
        })

class PaymentStatusCheckView(APIView):
    """Check payment status for verifications"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        today = timezone.now()
        month = int(month) if month else today.month
        year = int(year) if year else today.year
        
        # Get all verifications
        verifications = ContentVerification.objects.filter(
            month=month,
            year=year
        ).select_related('client')
        
        result = []
        for verification in verifications:
            result.append({
                'client_id': verification.client.id,
                'client_name': verification.client.client_name,
                'verification_status': verification.verification_status,
                'payment_status': verification.payment_status,
                'is_paid': verification.is_paid,  # True/False
                'content_met': verification.verification_status in ['pending_payment', 'completed'],
                'needs_payment': verification.verification_status == 'pending_payment'
            })
        
        # Counts
        total = len(result)
        paid_count = sum(1 for r in result if r['is_paid'])
        needs_payment_count = sum(1 for r in result if r['needs_payment'])
        
        return Response({
            'month': month,
            'year': year,
            'summary': {
                'total': total,
                'paid': paid_count,
                'needs_payment': needs_payment_count,
                'pending_verification': total - paid_count - needs_payment_count
            },
            'details': result
        })