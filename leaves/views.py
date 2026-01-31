from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from .models import LeaveApplication
from .serializers import LeaveApplicationSerializer, LeaveProcessSerializer

class LeaveListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Admin roles see all, others see own (though this page is for Admin)
        if (request.user.role in ['admin', 'superuser'] or 
            request.user.user_type in ['hr', 'manager', 'director'] or 
            request.user.is_superuser):
            leaves = LeaveApplication.objects.all()
        else:
            leaves = LeaveApplication.objects.filter(employee=request.user)

        # Filtering
        status_filter = request.query_params.get('status')
        if status_filter:
            leaves = leaves.filter(status=status_filter)

        employee_filter = request.query_params.get('employee')
        if employee_filter:
            leaves = leaves.filter(employee_id=employee_filter)

        from_date = request.query_params.get('from_date')
        if from_date:
            leaves = leaves.filter(start_date__gte=from_date)

        to_date = request.query_params.get('to_date')
        if to_date:
            leaves = leaves.filter(end_date__lte=to_date)

        leave_type = request.query_params.get('leave_type')
        if leave_type:
            leaves = leaves.filter(leave_type=leave_type)

        serializer = LeaveApplicationSerializer(leaves, many=True)
        return Response(serializer.data)

class LeaveProcessView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, pk):
        if (request.user.role not in ['admin', 'superuser'] and 
            request.user.user_type not in ['hr', 'manager', 'director'] and 
            not request.user.is_superuser):
            return Response({"error": "Only admins can process leaves"}, status=status.HTTP_403_FORBIDDEN)

        try:
            leave = LeaveApplication.objects.get(pk=pk)
        except LeaveApplication.DoesNotExist:
            return Response({"error": "Leave application not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = LeaveProcessSerializer(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data['action']
            remarks = serializer.validated_data.get('remarks', '')

            if action == 'approve':
                leave.status = 'approved'
            elif action == 'reject':
                leave.status = 'rejected'

            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.remarks = remarks
            leave.save()

            return Response({
                "message": f"Leave application {leave.status} successfully",
                "data": LeaveApplicationSerializer(leave).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
