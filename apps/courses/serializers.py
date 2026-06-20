from rest_framework import serializers

from apps.courses.models import Course, CourseCategory, Enrollment


class CourseCategorySerializer(serializers.ModelSerializer):
    course_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = CourseCategory
        fields = [
            'id', 'title', 'slug', 'description',
            'meta_title', 'meta_description', 'order', 'course_count',
        ]


class CourseListSerializer(serializers.ModelSerializer):
    category = CourseCategorySerializer(read_only=True)
    enrolled_count = serializers.SerializerMethodField()
    remaining_capacity = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'image', 'price',
            'category', 'age_group', 'level', 'capacity', 'start_date', 'end_date',
            'enrolled_count', 'remaining_capacity', 'is_full', 'created_at',
        ]

    def get_enrolled_count(self, obj):
        if hasattr(obj, 'paid_enrollment_count'):
            return obj.paid_enrollment_count
        return obj.enrolled_count

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_remaining_capacity(self, obj):
        enrolled = self.get_enrolled_count(obj)
        return max(0, obj.capacity - enrolled)

    def get_is_full(self, obj):
        return self.get_enrolled_count(obj) >= obj.capacity


class CourseDetailSerializer(CourseListSerializer):
    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields


class CourseCategoryDetailSerializer(CourseCategorySerializer):
    courses = CourseListSerializer(many=True, read_only=True)

    class Meta(CourseCategorySerializer.Meta):
        fields = CourseCategorySerializer.Meta.fields + ['courses']


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    payment_status = serializers.CharField(source='payment.status', read_only=True, default=None)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'course', 'course_title', 'course_slug',
            'payment', 'payment_status', 'enrollment_date', 'status',
        ]
        read_only_fields = fields
