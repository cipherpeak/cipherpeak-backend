from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from emplyees.models import LeaveManagement
from .serializers import LeaveApplicationSerializer, LeaveProcessSerializer
from datetime import datetime

class LeaveListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Admin roles see all, others see own (though this page is for Admin)
        user = request.user
        role_lower = (user.role or '').lower()
        user_type_lower = (user.user_type or '').lower()
        
        is_admin = (
            role_lower in ['admin', 'superuser'] or 
            user_type_lower in ['hr', 'manager', 'director', 'admin'] or 
            user.is_superuser
        )

        if is_admin:
            leaves = LeaveManagement.objects.all()
        else:
            leaves = LeaveManagement.objects.filter(employee=user)

        # Filtering
        status_filter = request.query_params.get('status')
        if status_filter:
            today_str = datetime.now().strftime('%Y-%m-%d')
            if status_filter == 'active':
                leaves = leaves.filter(status='approved', start_date__lte=today_str, end_date__gte=today_str)
            elif status_filter == 'upcoming':
                leaves = leaves.filter(status='approved', start_date__gt=today_str)
            else:
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
            leaves = leaves.filter(category=leave_type)

        serializer = LeaveApplicationSerializer(leaves, many=True)
        return Response(serializer.data)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class LeaveProcessView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, pk):
        user = request.user
        role_lower = (user.role or '').lower()
        user_type_lower = (user.user_type or '').lower()
        
        is_admin = (
            role_lower in ['admin', 'superuser'] or 
            user_type_lower in ['hr', 'manager', 'director', 'admin'] or 
            user.is_superuser
        )

        if not is_admin:
            return Response({
                "error": "Only admins can process leaves",
                "debug": {
                    "role": role_lower,
                    "user_type": user_type_lower,
                    "is_superuser": user.is_superuser,
                    "username": user.username
                }
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            leave = LeaveManagement.objects.get(pk=pk)
        except LeaveManagement.DoesNotExist:
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
