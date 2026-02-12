from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ClientVerification
from .serializers import ClientVerificationSerializer

from django.utils import timezone

class ClientVerificationList(APIView):
    def get(self, request):
        try:
            now = timezone.now()

            client_verifications = ClientVerification.objects.filter(is_completed=False).exclude(
                verified_date__year=now.year,
                verified_date__month=now.month
            )
            serializer = ClientVerificationSerializer(client_verifications, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            from .models import MonthlyVerification
            verification_id = request.data.get('id')
            if not verification_id:
                return Response({'error': 'Verification ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            client_verification = ClientVerification.objects.get(id=verification_id)
            now = timezone.now()
            
            monthly_stat, created = MonthlyVerification.objects.get_or_create(
                clientverification=client_verification,
                month=now.month,
                year=now.year
            )
            
           
            if 'posters_completed' in request.data:
                monthly_stat.posters_completed = request.data.get('posters_completed')
            if 'videos_completed' in request.data:
                monthly_stat.videos_completed = request.data.get('videos_completed')
            if 'posters_posted' in request.data:
                monthly_stat.posters_posted = request.data.get('posters_posted')
            if 'videos_posted' in request.data:
                monthly_stat.videos_posted = request.data.get('videos_posted')
            
            monthly_stat.save()
            
            return Response({'message': 'Data updated successfully'}, status=status.HTTP_200_OK)
        except ClientVerification.DoesNotExist:
            return Response({'error': 'ClientVerification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CloseMonthlyVerification(APIView):
    def post(self, request):
        try:
            from .models import MonthlyVerification
            verification_id = request.data.get('id')
            if not verification_id:
                return Response({'error': 'Verification ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            client_verification = ClientVerification.objects.get(id=verification_id)
            now = timezone.now()
            
            monthly_stat, created = MonthlyVerification.objects.get_or_create(
                clientverification=client_verification,
                month=now.month,
                year=now.year
            )
            
            monthly_stat.is_verified = True
            monthly_stat.save()

            # Update ClientVerification.verified_date to current time to exclude it from the list for this month
            client_verification.verified_date = now
            client_verification.save()
            
            return Response({'message': 'Month closed successfully'}, status=status.HTTP_200_OK)
        except ClientVerification.DoesNotExist:
            return Response({'error': 'ClientVerification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifiedClientList(APIView):
    def get(self, request):
        try:
            now = timezone.now()
            month = request.query_params.get('month', now.month)
            year = request.query_params.get('year', now.year)

            client_verifications = ClientVerification.objects.filter(
                is_completed=False,
                verified_date__year=year,
                verified_date__month=month
            )
            serializer = ClientVerificationSerializer(client_verifications, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    