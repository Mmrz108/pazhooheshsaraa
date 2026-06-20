from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Enrollment
from apps.courses.serializers import EnrollmentSerializer
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.users.serializers import UserProfileSerializer, UserProfileUpdateSerializer


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)


class EnrolledCoursesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user,
        ).select_related('course', 'payment').order_by('-enrollment_date')


class PaymentHistoryView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user,
        ).select_related('course').order_by('-created_at')
