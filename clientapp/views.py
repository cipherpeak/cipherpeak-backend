from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import date
from .models import Client, ClientDocument
from .serializers import (
    ClientSerializer, 
    ClientDocumentSerializer, 
    ClientPaymentStatusUpdateSerializer,
    ClientListSerializer,
    ClientStatsSerializer,
    ClientEarlyPaymentSerializer,
    ClientPaymentTimelineSerializer,
    ClientDetailSerializer,
    ClientUpdateSerializer
)


#client create view
class ClientCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Create client with permission check"""
        # Check if user has permission to create clients
        if request.user.role not in ['director', 'managing_director'] and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied. Only Directors and Managing Directors can create clients."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Client created successfully!",
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#clent detail view   
class ClientDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        try:
            return Client.objects.get(id=id, is_deleted=False)
        except Client.DoesNotExist:
            return None

    def get(self, request, id):
        client = self.get_object(id)
        if not client:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientDetailSerializer(client)
        return Response(serializer.data)


#client active list view
class ClientListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Return only active clients with searching and ordering
        """
        queryset = Client.objects.filter(status='active', is_deleted=False)
        
        # Searching
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(client_name__icontains=search) |
                models.Q(contact_person_name__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get('ordering', 'client_name')
        queryset = queryset.order_by(ordering)

        serializer = ClientListSerializer(queryset, many=True)
        return Response(serializer.data)


#client update view
class ClientUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, id):
        try:
            return Client.objects.get(id=id, is_deleted=False)
        except Client.DoesNotExist:
            return None

    def put(self, request, id):
        client = self.get_object(id)
        if not client:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientUpdateSerializer(client, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Client updated successfully",
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        client = self.get_object(id)
        if not client:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientUpdateSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Client updated successfully",
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

#class for uploading client documents
class ClientDocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """
        Create a new document for the specified client
        """
        client = generics.get_object_or_404(Client, id=id, is_deleted=False)
        
        serializer = ClientDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            document = serializer.save(client=client, uploaded_by=request.user)
            return Response({
                "message": "Document uploaded successfully",
                "document": ClientDocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#client delete view
class ClientDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        try:
            client = Client.objects.get(id=id, is_deleted=False)

            client.is_deleted = True
            client.deleted_at = timezone.now()
            client.save()

            return Response(
                {'message': f'Client deleted successfully.'},
                status=status.HTTP_200_OK
            )

        except Client.DoesNotExist:
            return Response(
                {'error': 'Client not found or already deleted.'},
                status=status.HTTP_404_NOT_FOUND
            )






class ClientPaymentStatusUpdateView(generics.UpdateAPIView):
    """
    View for updating client payment status with support for early payments
    """
    queryset = Client.objects.filter(is_deleted=False)
    serializer_class = ClientPaymentStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        """Handle payment status update including early payments"""
        instance = serializer.save()
        
        # Log the payment update
        mark_as_paid = serializer.validated_data.get('mark_as_paid')
        mark_as_early_paid = serializer.validated_data.get('mark_as_early_paid')
        
        if mark_as_early_paid:
            # Early payment was processed
            payment_date = serializer.validated_data.get('payment_date')
            amount = serializer.validated_data.get('amount')
            notes = serializer.validated_data.get('notes', '')
            
            # Log the early payment (you might want to add logging here)
            print(f"Early payment recorded for {instance.client_name} on {payment_date}")
            
        elif mark_as_paid:
            # Regular payment was processed
            instance.mark_payment_as_paid()

class ClientMarkPaymentPaidView(generics.GenericAPIView):
    """
    View to mark client payment as paid
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Client.objects.filter(is_deleted=False)
    lookup_field = 'id'

    def post(self, request, *args, **kwargs):
        client = self.get_object()
        client.mark_payment_as_paid()
        
        return Response({
            'message': 'Payment marked as paid successfully',
            'next_payment_date': client.next_payment_date,
            'payment_status': client.current_month_payment_status,
            'payment_timing': client.payment_timing
        }, status=status.HTTP_200_OK)

class ClientMarkEarlyPaymentView(generics.GenericAPIView):
    """
    View to mark client payment as early paid
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Client.objects.filter(is_deleted=False)
    lookup_field = 'id'
    serializer_class = ClientEarlyPaymentSerializer

    def post(self, request, *args, **kwargs):
        client = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update client with early payment
        serializer.update(client, serializer.validated_data)
        
        return Response({
            'message': 'Early payment recorded successfully',
            'next_payment_date': client.next_payment_date,
            'payment_status': client.current_month_payment_status,
            'payment_timing': client.payment_timing,
            'early_payment_date': client.early_payment_date,
            'early_payment_amount': client.early_payment_amount,
            'early_payment_days': client.early_payment_days
        }, status=status.HTTP_200_OK)

class ClientPaymentTimelineView(generics.RetrieveAPIView):
    """
    View for retrieving client payment timeline information
    """
    queryset = Client.objects.filter(is_deleted=False)
    serializer_class = ClientPaymentTimelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'



#client statistics view
class ClientStatsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Use base queryset excluding deleted clients
        base_queryset = Client.objects.filter(is_deleted=False)
        
        total_clients = base_queryset.count()
        active_clients = base_queryset.filter(status='active').count()
        prospect_clients = base_queryset.filter(status='prospect').count()
        
        # Payment statistics
        overdue_payments = base_queryset.filter(current_month_payment_status='overdue').count()
        paid_payments = base_queryset.filter(current_month_payment_status='paid').count()
        early_payments = base_queryset.filter(current_month_payment_status='early_paid').count()
        pending_payments = base_queryset.filter(current_month_payment_status='pending').count()
        partial_payments = base_queryset.filter(current_month_payment_status='partial').count()
        
        # Payment timing statistics
        early_timing = base_queryset.filter(payment_timing='early').count()
        on_time_timing = base_queryset.filter(payment_timing='on_time').count()
        late_timing = base_queryset.filter(payment_timing='late').count()
        
        # Revenue statistics
        total_monthly_revenue = base_queryset.filter(status='active').aggregate(
            total_revenue=Sum('monthly_retainer')
        )['total_revenue'] or 0
        
        # Early payment revenue
        early_payment_revenue = base_queryset.filter(
            current_month_payment_status='early_paid'
        ).aggregate(
            total_early_revenue=Sum('early_payment_amount')
        )['total_early_revenue'] or 0
        
        # Clients with overdue payments
        clients_with_overdue_payments = base_queryset.filter(
            current_month_payment_status='overdue',
            status='active'
        ).count()
        
        # Clients by type
        clients_by_type = base_queryset.values('client_type').annotate(count=Count('id'))
        
        # Clients by industry
        clients_by_industry = base_queryset.values('industry').annotate(count=Count('id'))
        
        # Clients by status
        clients_by_status = base_queryset.values('status').annotate(count=Count('id'))
        
        # Clients by payment status
        clients_by_payment_status = base_queryset.values('current_month_payment_status').annotate(count=Count('id'))
        
        # Clients by payment timing
        clients_by_payment_timing = base_queryset.values('payment_timing').annotate(count=Count('id'))
        
        # Clients by payment cycle
        clients_by_payment_cycle = base_queryset.values('payment_cycle').annotate(count=Count('id'))
        
        # Upcoming payments (due in next 7 days)
        next_week = timezone.now().date() + timezone.timedelta(days=7)
        upcoming_payments = base_queryset.filter(
            next_payment_date__lte=next_week,
            next_payment_date__gte=timezone.now().date(),
            current_month_payment_status__in=['pending', 'overdue']
        ).count()
        
        # Recent early payments (last 30 days)
        thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
        recent_early_payments = base_queryset.filter(
            early_payment_date__gte=thirty_days_ago
        ).count()
        
        stats = {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'prospect_clients': prospect_clients,
            'overdue_payments': overdue_payments,
            'paid_payments': paid_payments,
            'early_payments': early_payments,
            'pending_payments': pending_payments,
            'partial_payments': partial_payments,
            'early_timing_payments': early_timing,
            'on_time_timing_payments': on_time_timing,
            'late_timing_payments': late_timing,
            'total_monthly_revenue': float(total_monthly_revenue),
            'early_payment_revenue': float(early_payment_revenue),
            'clients_with_overdue_payments': clients_with_overdue_payments,
            'upcoming_payments': upcoming_payments,
            'recent_early_payments': recent_early_payments,
            'clients_by_type': {item['client_type']: item['count'] for item in clients_by_type},
            'clients_by_industry': {item['industry']: item['count'] for item in clients_by_industry if item['industry']},
            'clients_by_status': {item['status']: item['count'] for item in clients_by_status},
            'clients_by_payment_status': {item['current_month_payment_status']: item['count'] for item in clients_by_payment_status},
            'clients_by_payment_timing': {item['payment_timing']: item['count'] for item in clients_by_payment_timing},
            'clients_by_payment_cycle': {item['payment_cycle']: item['count'] for item in clients_by_payment_cycle},
        }
        
        return Response(stats, status=status.HTTP_200_OK)

class ClientUpcomingPaymentsView(generics.ListAPIView):
    """
    View for listing clients with upcoming payments
    """
    serializer_class = ClientListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return clients with payments due in the next specified days
        """
        days = int(self.request.query_params.get('days', 7))
        target_date = timezone.now().date() + timezone.timedelta(days=days)
        
        queryset = Client.objects.filter(
            next_payment_date__lte=target_date,
            next_payment_date__gte=timezone.now().date(),
            status='active',
            is_deleted=False
        ).order_by('next_payment_date')
        
        return queryset

class ClientOverduePaymentsView(generics.ListAPIView):
    """
    View for listing clients with overdue payments
    """
    serializer_class = ClientListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return clients with overdue payments
        """
        queryset = Client.objects.filter(
            current_month_payment_status='overdue',
            status='active',
            is_deleted=False
        ).order_by('next_payment_date')
        
        return queryset

class ClientEarlyPaymentsView(generics.ListAPIView):
    """
    View for listing clients with early payments
    """
    serializer_class = ClientListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return clients with early payments
        """
        queryset = Client.objects.filter(
            current_month_payment_status='early_paid',
            status='active',
            is_deleted=False
        ).order_by('-early_payment_date')
        
        # Filter by recent early payments (optional)
        days = self.request.query_params.get('days', None)
        if days:
            target_date = timezone.now().date() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(early_payment_date__gte=target_date)
            
        return queryset




@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reset_monthly_payments(request):
    """
    Endpoint to reset payment status for all clients at beginning of month
    (To be called via cron job or manually)
    """
    if request.method == 'POST':
        updated_count = 0
        # Reset both paid and early_paid statuses for non-deleted clients
        clients = Client.objects.filter(
            is_deleted=False,
            current_month_payment_status__in=['paid', 'early_paid']
        )
        
        for client in clients:
            client.reset_payment_status_for_new_month()
            updated_count += 1
            
        return Response({
            'message': f'Payment status reset for {updated_count} clients',
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def client_payment_analytics(request):
    """
    Endpoint for detailed payment analytics
    """
    # Use base queryset excluding deleted clients
    base_queryset = Client.objects.filter(is_deleted=False)
    
    # Early payment analysis
    early_payment_analysis = base_queryset.filter(
        early_payment_date__isnull=False
    ).aggregate(
        total_early_payments=Count('id'),
        avg_early_days=Avg('early_payment_days'),
        total_early_revenue=Sum('early_payment_amount')
    )
    
    # Payment timing analysis
    payment_timing_analysis = base_queryset.values('payment_timing').annotate(
        count=Count('id'),
        avg_revenue=Avg('monthly_retainer')
    )
    
    # Monthly payment trends (you might want to create a separate Payment model for this)
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_stats = {
        'early_payment_analysis': early_payment_analysis,
        'payment_timing_analysis': list(payment_timing_analysis),
        'current_month': current_month,
        'current_year': current_year
    }
    
    return Response(monthly_stats, status=status.HTTP_200_OK)




