from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import date
from django.db.models import Prefetch
from .models import Client, ClientDocument, ClientPaymentHistory, ClientAdminNote
from .serializers import (
    ClientSerializer, 
    ClientDocumentSerializer, 
    ClientListSerializer,
    ClientDetailSerializer,
    ClientUpdateSerializer,
    ClientPaymentHistorySerializer,
    ClientAdminNoteSerializer,
    ClientAdminNoteCreateSerializer,
    ClientMarkPaymentSerializer,
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
    

    def get(self, request, id):
        try:
            client = Client.objects.get(id=id, is_deleted=False)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Client not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prefetch related data for better performance
        client = Client.objects.filter(id=client.id, is_deleted=False).prefetch_related(
            Prefetch(
                'payment_history', 
                queryset=ClientPaymentHistory.objects.all().order_by('-created_at')
            ),
            Prefetch(
                'admin_notes', 
                queryset=ClientAdminNote.objects.all().order_by('-created_at')
            ),
        ).first()
        
        serializer = ClientDetailSerializer(client, context={'request': request})
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



class ClientPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        client = request.query_params.get('client')
        payment_history = ClientPaymentHistory.objects.filter(client=client)
        serializer = ClientPaymentHistorySerializer(payment_history, many=True)
        return Response(serializer.data)
        

class ClientPaymentProcessView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            client = Client.objects.get(id=id, is_deleted=False)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if payment already processed for this month
        now = timezone.now()
        if ClientPaymentHistory.objects.filter(
            client=client, 
            payment_date__year=now.year, 
            payment_date__month=now.month
        ).exists():
             return Response({'message': 'Payment already processed for this month'}, status=status.HTTP_400_BAD_REQUEST)

        # Create payment history record
        serializer = ClientPaymentHistorySerializer(data=request.data)
        if serializer.is_valid():
            payment_history = serializer.save(client=client, processed_by=request.user)
            
            # Update client model state
            client.mark_payment_as_paid(
                payment_date=payment_history.payment_date,
                amount=payment_history.amount,
                notes=payment_history.notes
            )
            
            return Response({'message': 'Payment processed successfully'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientAdminNoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        client = generics.get_object_or_404(Client, id=id, is_deleted=False)
        admin_notes = ClientAdminNote.objects.filter(client=client)
        serializer = ClientAdminNoteSerializer(admin_notes, many=True)
        return Response(serializer.data)
class ClientAdminNoteCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        client = generics.get_object_or_404(Client, id=id, is_deleted=False)
        serializer = ClientAdminNoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(client=client, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
