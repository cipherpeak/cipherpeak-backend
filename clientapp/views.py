from rest_framework import generics, permissions, status
from django.http import FileResponse
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import models
from django.db.models import Prefetch
from django.utils import timezone
from .models import Client, ClientDocument, ClientPayment
import calendar
from datetime import date
from .serializers import (
    ClientSerializer, 
    ClientDocumentSerializer, 
    ClientListSerializer,
    ClientDetailSerializer,
    ClientUpdateSerializer,
    ClientPaymentSerializer,
    ClientPaymentDetailSerializer,
)

 
#client create view
class ClientCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
       
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
    
    def get(self, request, id):
       
        client = Client.objects.filter(id=id, is_deleted=False).prefetch_related(
            Prefetch(
                'client_payments', 
                queryset=ClientPayment.objects.all().order_by('-created_at')
            ),

        ).first()

        if not client:
            return Response(
                {'error': 'Client not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClientDetailSerializer(client, context={'request': request})
        return Response(serializer.data)


#client  list view
class ClientListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        
        queryset = Client.objects.filter(status='active', is_deleted=False)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(client_name__icontains=search) |
                models.Q(contact_person_name__icontains=search)
            )

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

        client = generics.get_object_or_404(Client, id=id, is_deleted=False)
        
        serializer = ClientDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            document = serializer.save(client=client, uploaded_by=request.user)
            return Response({
                "message": "Document uploaded successfully",
                "document": ClientDocumentSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#client document delete view
class ClientDocumentDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            document = ClientDocument.objects.get(pk=pk)
        except ClientDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permissions: owner or admin/hr/director
        # Assuming uploaded_by is the user who uploaded it.
        # Admins should be able to delete any document.
        is_owner = request.user == document.uploaded_by
        is_admin = request.user.is_superuser or request.user.role in ['director', 'managing_director', 'admin']

        if not (is_owner or is_admin):
             return Response(
                {'error': 'You do not have permission to delete this document'},
                status=status.HTTP_403_FORBIDDEN
            )

        document.delete()
        return Response(
            {'message': 'Document deleted successfully'},
            status=status.HTTP_200_OK
        )


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


#process client payment view
class ProcessClientPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            client = Client.objects.get(pk=pk, is_deleted=False)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_superuser and request.user.role not in ['admin', 'hr', 'manager', 'director']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        today = timezone.now().date()
        
        target_month = request.data.get('month')
        target_year = request.data.get('year')
        
        if not target_month or not target_year:
            import calendar
            current_date_iter = date(client.onboarding_date.year, client.onboarding_date.month, 1)
            end_date_iter = date(today.year, today.month, 1)
            
            while current_date_iter <= end_date_iter:
                m = current_date_iter.month
                y = current_date_iter.year
                
                is_paid = ClientPayment.objects.filter(
                    client=client,
                    month=m,
                    year=y,
                    status__in=['paid', 'early_paid']
                ).exists()
                
                if not is_paid:
                    target_month = m
                    target_year = y
                    break
                    
                if current_date_iter.month == 12:
                    current_date_iter = date(current_date_iter.year + 1, 1, 1)
                else:
                    current_date_iter = date(current_date_iter.year, current_date_iter.month + 1, 1)
        
        if not target_month:
            return Response({'error': 'Payment already processed for all months'}, status=status.HTTP_400_BAD_REQUEST)
        
        target_month = int(target_month)
        target_year = int(target_year)

        existing_payment = ClientPayment.objects.filter(
            client=client,
            month=target_month,
            year=target_year,
            status__in=['paid', 'early_paid']
        ).exists()
        
        if existing_payment:
            return Response({'error': f'Payment already processed for {target_month}/{target_year}'}, status=status.HTTP_400_BAD_REQUEST)
        
        amount = request.data.get('amount', client.monthly_retainer)
        payment_method = request.data.get('payment_method', 'bank_transfer')
        transaction_id = request.data.get('transaction_id', '')
        remarks = request.data.get('remarks', '')
        
        try:
            amount = float(amount) if amount else 0
        except (ValueError, TypeError):
            return Response({'error': 'Invalid payment amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        import calendar
        try:
            
            last_day_of_month = calendar.monthrange(target_year, target_month)[1]
            scheduled_date = date(target_year, target_month, last_day_of_month)
        except (AttributeError, ValueError):
           
            last_day = calendar.monthrange(target_year, target_month)[1]
            scheduled_date = date(target_year, target_month, last_day)
        
        if today < scheduled_date:
            payment_status_val = 'early_paid'
        else:
            payment_status_val = 'paid'
        
        client_payment, created = ClientPayment.objects.update_or_create(
            client=client,
            month=target_month,
            year=target_year,
            defaults={
                'amount': amount,
                'net_amount': amount,
                'scheduled_date': scheduled_date,
                'payment_date': timezone.now(),
                'status': payment_status_val,
                'payment_method': payment_method,
                'transaction_id': transaction_id,
                'processed_by': request.user,
                'remarks': remarks
            }
        )
        
        client.current_month_payment_status = payment_status_val
        client.last_payment_date = today
        
        from . import utils
        utils.calculate_next_payment_date_after_payment(client)
        
        client.save(update_fields=['current_month_payment_status', 'last_payment_date', 'next_payment_date'])

        return Response({
            'message': f'Payment for {target_month}/{target_year} processed successfully',
            'payment_id': client_payment.id,
            'status': client_payment.get_status_display()
        }, status=status.HTTP_200_OK)


#client payment history list view
class ClientPaymentHistoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, client_id):
        try:
            client = Client.objects.get(pk=client_id, is_deleted=False)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        
        payments = ClientPayment.objects.filter(client=client)
        serializer = ClientPaymentSerializer(payments, many=True)
        
        return Response({
            'client_name': client.client_name,
            'total_payments': payments.count(),
            'payments': serializer.data
        })


#client payment detail view
class ClientPaymentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            payment = ClientPayment.objects.get(id=id)
            serializer = ClientPaymentDetailSerializer(payment)
            return Response(serializer.data)
        except ClientPayment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    
    