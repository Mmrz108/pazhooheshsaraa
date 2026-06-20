from django.db.models import Count, Q
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, CourseCategory, EnrollmentStatus
from apps.courses.serializers import (
    CourseCategoryDetailSerializer,
    CourseCategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
)


def course_queryset():
    return Course.objects.filter(is_active=True).select_related('category').annotate(
        paid_enrollment_count=Count(
            'enrollments',
            filter=Q(enrollments__status=EnrollmentStatus.PAID),
        ),
    ).order_by('-created_at')


class CourseListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CourseListSerializer

    def get_queryset(self):
        qs = course_queryset()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category, category__is_active=True)
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            return qs[:int(limit)]
        return qs


class CourseDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CourseDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return course_queryset()

    def get_object(self):
        try:
            return self.get_queryset().get(slug=self.kwargs['slug'])
        except Course.DoesNotExist as exc:
            raise NotFound('دوره یافت نشد.') from exc


class CourseCategoryListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CourseCategorySerializer

    def get_queryset(self):
        return CourseCategory.objects.filter(is_active=True).annotate(
            course_count=Count(
                'courses',
                filter=Q(courses__is_active=True),
            ),
        )


class CourseCategoryDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            category = CourseCategory.objects.filter(is_active=True).annotate(
                course_count=Count(
                    'courses',
                    filter=Q(courses__is_active=True),
                ),
            ).get(slug=slug)
        except CourseCategory.DoesNotExist as exc:
            raise NotFound('دسته‌بندی یافت نشد.') from exc

        courses = course_queryset().filter(category=category)
        serializer = CourseCategoryDetailSerializer(
            category,
            context={'request': request},
        )
        data = serializer.data
        data['courses'] = CourseListSerializer(
            courses, many=True, context={'request': request},
        ).data
        return Response(data)
