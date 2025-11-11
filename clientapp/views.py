# client/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from django.db.models import Sum, Count, Q
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
    ClientPaymentTimelineSerializer
)

class ClientListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating clients
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'client_name', 
        'contact_person_name', 
        'contact_email', 
        'owner_name',
        'company'
    ]
    ordering_fields = [
        'client_name', 
        'onboarding_date', 
        'created_at', 
        'status',
        'monthly_retainer',
        'next_payment_date',
        'early_payment_date',
        'last_payment_date'
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally filter by client_type, industry, status, payment_status, payment_timing, or overdue
        """
        queryset = Client.objects.all()
        
        # Manual filtering for client_type
        client_type = self.request.query_params.get('client_type', None)
        if client_type:
            queryset = queryset.filter(client_type=client_type)
            
        # Manual filtering for industry
        industry = self.request.query_params.get('industry', None)
        if industry:
            queryset = queryset.filter(industry=industry)
            
        # Manual filtering for status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Manual filtering for payment_status
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status:
            queryset = queryset.filter(current_month_payment_status=payment_status)
            
        # Manual filtering for payment_timing
        payment_timing = self.request.query_params.get('payment_timing', None)
        if payment_timing:
            queryset = queryset.filter(payment_timing=payment_timing)
            
        # Filter overdue payments
        overdue = self.request.query_params.get('overdue', None)
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(current_month_payment_status='overdue')
            
        # Filter early payments
        early_payments = self.request.query_params.get('early_payments', None)
        if early_payments and early_payments.lower() == 'true':
            queryset = queryset.filter(current_month_payment_status='early_paid')
            
        # Filter active clients only
        active_only = self.request.query_params.get('active_only', None)
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(status='active')
            
        # Filter by payment cycle
        payment_cycle = self.request.query_params.get('payment_cycle', None)
        if payment_cycle:
            queryset = queryset.filter(payment_cycle=payment_cycle)
            
        return queryset

    def get_serializer_class(self):
        """Use different serializer for list vs create"""
        if self.request.method == 'GET':
            return ClientListSerializer
        return ClientSerializer

    def perform_create(self, serializer):
        """Save the client"""
        serializer.save()

class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific client
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class ClientPaymentStatusUpdateView(generics.UpdateAPIView):
    """
    View for updating client payment status with support for early payments
    """
    queryset = Client.objects.all()
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
    queryset = Client.objects.all()
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
    queryset = Client.objects.all()
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
    queryset = Client.objects.all()
    serializer_class = ClientPaymentTimelineSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class ClientDocumentListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating client documents
    """
    queryset = ClientDocument.objects.all()
    serializer_class = ClientDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description', 'document_type']

    def get_queryset(self):
        """
        Optionally filter by client or document_type
        """
        queryset = ClientDocument.objects.all()
        
        # Filter by client
        client_id = self.request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
            
        # Filter by document_type
        document_type = self.request.query_params.get('document_type', None)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
            
        return queryset

    def perform_create(self, serializer):
        """Set the uploaded_by user when creating a document"""
        serializer.save(uploaded_by=self.request.user)

class ClientDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific client document
    """
    queryset = ClientDocument.objects.all()
    serializer_class = ClientDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class ClientStatsView(generics.GenericAPIView):
    """
    View for getting client statistics
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(status='active').count()
        prospect_clients = Client.objects.filter(status='prospect').count()
        
        # Payment statistics
        overdue_payments = Client.objects.filter(current_month_payment_status='overdue').count()
        paid_payments = Client.objects.filter(current_month_payment_status='paid').count()
        early_payments = Client.objects.filter(current_month_payment_status='early_paid').count()
        pending_payments = Client.objects.filter(current_month_payment_status='pending').count()
        partial_payments = Client.objects.filter(current_month_payment_status='partial').count()
        
        # Payment timing statistics
        early_timing = Client.objects.filter(payment_timing='early').count()
        on_time_timing = Client.objects.filter(payment_timing='on_time').count()
        late_timing = Client.objects.filter(payment_timing='late').count()
        
        # Revenue statistics
        total_monthly_revenue = Client.objects.filter(status='active').aggregate(
            total_revenue=Sum('monthly_retainer')
        )['total_revenue'] or 0
        
        # Early payment revenue
        early_payment_revenue = Client.objects.filter(
            current_month_payment_status='early_paid'
        ).aggregate(
            total_early_revenue=Sum('early_payment_amount')
        )['total_early_revenue'] or 0
        
        # Clients with overdue payments
        clients_with_overdue_payments = Client.objects.filter(
            current_month_payment_status='overdue',
            status='active'
        ).count()
        
        # Clients by type
        clients_by_type = Client.objects.values('client_type').annotate(count=Count('id'))
        
        # Clients by industry
        clients_by_industry = Client.objects.values('industry').annotate(count=Count('id'))
        
        # Clients by status
        clients_by_status = Client.objects.values('status').annotate(count=Count('id'))
        
        # Clients by payment status
        clients_by_payment_status = Client.objects.values('current_month_payment_status').annotate(count=Count('id'))
        
        # Clients by payment timing
        clients_by_payment_timing = Client.objects.values('payment_timing').annotate(count=Count('id'))
        
        # Clients by payment cycle
        clients_by_payment_cycle = Client.objects.values('payment_cycle').annotate(count=Count('id'))
        
        # Upcoming payments (due in next 7 days)
        next_week = timezone.now().date() + timezone.timedelta(days=7)
        upcoming_payments = Client.objects.filter(
            next_payment_date__lte=next_week,
            next_payment_date__gte=timezone.now().date(),
            current_month_payment_status__in=['pending', 'overdue']
        ).count()
        
        # Recent early payments (last 30 days)
        thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
        recent_early_payments = Client.objects.filter(
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
            status='active'
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
            status='active'
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
            status='active'
        ).order_by('-early_payment_date')
        
        # Filter by recent early payments (optional)
        days = self.request.query_params.get('days', None)
        if days:
            target_date = timezone.now().date() - timezone.timedelta(days=int(days))
            queryset = queryset.filter(early_payment_date__gte=target_date)
            
        return queryset

class ClientActiveListView(generics.ListAPIView):
    """
    View for listing active clients only
    """
    serializer_class = ClientListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['client_name', 'contact_person_name']
    ordering_fields = [
        'client_name', 
        'next_payment_date', 
        'monthly_retainer',
        'early_payment_date',
        'last_payment_date'
    ]
    ordering = ['client_name']

    def get_queryset(self):
        """
        Return only active clients
        """
        return Client.objects.filter(status='active')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reset_monthly_payments(request):
    """
    Endpoint to reset payment status for all clients at beginning of month
    (To be called via cron job or manually)
    """
    if request.method == 'POST':
        updated_count = 0
        # Reset both paid and early_paid statuses
        clients = Client.objects.filter(
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
    # Early payment analysis
    early_payment_analysis = Client.objects.filter(
        early_payment_date__isnull=False
    ).aggregate(
        total_early_payments=Count('id'),
        avg_early_days=Avg('early_payment_days'),
        total_early_revenue=Sum('early_payment_amount')
    )
    
    # Payment timing analysis
    payment_timing_analysis = Client.objects.values('payment_timing').annotate(
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


