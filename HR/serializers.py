from rest_framework import serializers
from .models import StaffDetails, Attendance, LeaveRequest, LeaveComment, Loan, LoanComment, Overtime, OvertimeComment, Fine, FineComment, Appraisal, AppraisalComment
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, date

class CoerceDateField(serializers.DateField):
    """Custom DateField that coerces datetime to date."""
    def to_representation(self, value):
        if isinstance(value, datetime):
            value = value.date()
        return super().to_representation(value)

    def to_internal_value(self, value):
        if isinstance(value, str):
            try:
                parsed_date = datetime.strptime(value, '%Y-%m-%d').date()
                return parsed_date
            except ValueError:
                raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD.")
        return super().to_internal_value(value)

def validate_pdf(file):
    if file and not file.name.endswith('.pdf'):
        raise ValidationError('File must be a PDF.')

class StaffDetailsSerializer(serializers.ModelSerializer):
    passport_expiry = CoerceDateField()
    visa_expiry = CoerceDateField()
    insurance_expiry = CoerceDateField()
    joining_date = CoerceDateField(read_only=True)
    visa_status = serializers.ReadOnlyField(source='visa_status_dynamic')

    class Meta:
        model = StaffDetails
        fields = [
            'staff_id', 'staff_type', 'name', 'passport_no', 'visa_no', 'emirates_id_number',
            'designation', 'nationality', 'insurance_number', 'email',
            'passport_expiry', 'visa_expiry', 'salary', 'emergency_contact',
            'insurance_expiry', 'contact_number', 'profile_photo', 'offer_letter',
            'home_address', 'uae_address', 'joining_date', 'visa_status'
        ]

    def validate(self, data):
        # Validate date fields
        for field in ['passport_expiry', 'visa_expiry', 'insurance_expiry']:
            if data.get(field) and not isinstance(data[field], date):
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').capitalize()} must be a date."})

        # Validate staff_type against URL parameter
        staff_type = data.get('staff_type')
        url_type = self.context.get('type', '').capitalize()  # Get type from URL (e.g., 'staff' -> 'Staff')
        if url_type and staff_type and staff_type != url_type:
            raise serializers.ValidationError({
                'staff_type': f"Staff type must be '{url_type}' to match the URL."
            })
        if staff_type not in ['Staff', 'Manpower']:
            raise serializers.ValidationError({
                'staff_type': "Staff type must be either 'Staff' or 'Manpower'."
            })
        return data

class VisaDetailsSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(read_only=True)
    joining_date = serializers.DateField(read_only=True)
    visa_status = serializers.ReadOnlyField(source='visa_status_dynamic')
    visa_expiry = CoerceDateField()

    class Meta:
        model = StaffDetails
        fields = [
            'staff_id', 'staff_type', 'name', 'contact_number', 'email', 'passport_no', 'visa_no',
            'visa_expiry', 'emirates_id_number', 'emergency_contact', 'joining_date',
            'uae_address', 'nationality', 'visa_status'
        ]

    def validate(self, data):
        # Validate staff_type against URL parameter
        staff_type = data.get('staff_type')
        url_type = self.context.get('type', '').capitalize()
        if url_type and staff_type and staff_type != url_type:
            raise serializers.ValidationError({
                'staff_type': f"Staff type must be '{url_type}' to match the URL."
            })
        if staff_type not in ['Staff', 'Manpower']:
            raise serializers.ValidationError({
                'staff_type': "Staff type must be either 'Staff' or 'Manpower'."
            })
        return data

class AttendanceSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(write_only=True)
    output_staff_id = serializers.CharField(source='staff.staff_id', read_only=True)
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    date = CoerceDateField()

    class Meta:
        model = Attendance
        fields = ['id', 'staff', 'staff_id', 'output_staff_id', 'staff_name', 'date', 'status', 'reason']
        read_only_fields = ['staff', 'output_staff_id', 'staff_name']

    def validate_staff_id(self, value):
        try:
            url_type = self.context.get('type', '').capitalize()
            staff = StaffDetails.objects.get(staff_id=value)
            if url_type and staff.staff_type != url_type:
                raise serializers.ValidationError(
                    f"Staff with staff_id {value} is not of type '{url_type}'."
                )
            return staff
        except StaffDetails.DoesNotExist:
            raise serializers.ValidationError(f"Staff with staff_id {value} does not exist.")

    def create(self, validated_data):
        staff = validated_data.pop('staff_id')
        validated_data['staff'] = staff
        return super().create(validated_data)

    def update(self, instance, validated_data):
        staff = validated_data.pop('staff_id', None)
        if staff:
            instance.staff = staff
        return super().update(instance, validated_data)

class LeaveCommentSerializer(serializers.ModelSerializer):
    leave_request = serializers.PrimaryKeyRelatedField(queryset=LeaveRequest.objects.all())
    comment_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = LeaveComment
        fields = ['id', 'leave_request', 'comment', 'commenter', 'comment_date']

class LeaveRequestSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    output_staff_id = serializers.CharField(source='staff.staff_id', read_only=True)
    staff_name = serializers.CharField(read_only=True)
    from_date = CoerceDateField()
    to_date = CoerceDateField()
    request_date = CoerceDateField(read_only=True)
    comments = LeaveCommentSerializer(many=True, read_only=True)
    submitted_by = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'staff', 'staff_id', 'output_staff_id', 'staff_name', 'from_date', 'to_date',
            'reason', 'submitted_by', 'status', 'gm_status', 'mgmt_status', 'request_date', 'comments'
        ]
        read_only_fields = ['staff', 'output_staff_id', 'staff_name', 'request_date']

    def validate(self, data):
        if data.get('from_date') and data.get('to_date'):
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError({"to_date": "To date must be on or after from date."})
        return data

    def validate_staff_id(self, value):
        if not value:
            return None
        try:
            url_type = self.context.get('type', '').capitalize()
            staff = StaffDetails.objects.get(staff_id=value)
            if url_type and staff.staff_type != url_type:
                raise serializers.ValidationError(
                    f"Staff with staff_id {value} is not of type '{url_type}'."
                )
            return staff
        except StaffDetails.DoesNotExist:
            raise serializers.ValidationError(f"Staff with staff_id {value} does not exist.")

    def create(self, validated_data):
        staff = validated_data.pop('staff_id')
        validated_data['staff'] = staff
        validated_data['staff_name'] = staff.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        staff = validated_data.pop('staff_id', None)
        if staff:
            instance.staff = staff
            instance.staff_name = staff.name
        return super().update(instance, validated_data)

class LoanCommentSerializer(serializers.ModelSerializer):
    loan = serializers.PrimaryKeyRelatedField(queryset=Loan.objects.all())
    comment_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = LoanComment
        fields = ['id', 'loan', 'comment', 'commenter', 'comment_date']

class LoanSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    output_staff_id = serializers.CharField(source='staff.staff_id', read_only=True)
    staff_name = serializers.CharField(read_only=True)
    from_date = CoerceDateField()
    to_date = CoerceDateField()
    request_date = CoerceDateField(read_only=True)
    comments = LoanCommentSerializer(many=True, read_only=True)
    submitted_by = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'staff', 'staff_id', 'output_staff_id', 'staff_name', 'from_date', 'to_date',
            'reason', 'loan_status', 'gm_status', 'mgmt_status', 'request_date', 'comments',
            'submitted_by'
        ]
        read_only_fields = ['staff', 'output_staff_id', 'staff_name', 'request_date']

    def validate(self, data):
        if data.get('from_date') and data.get('to_date'):
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError({"to_date": "To date must be on or after from date."})
        return data

    def validate_staff_id(self, value):
        if not value:
            return None
        try:
            url_type = self.context.get('type', '').capitalize()
            staff = StaffDetails.objects.get(staff_id=value)
            if url_type and staff.staff_type != url_type:
                raise serializers.ValidationError(
                    f"Staff with staff_id {value} is not of type '{url_type}'."
                )
            return staff
        except StaffDetails.DoesNotExist:
            raise serializers.ValidationError(f"Staff with staff_id {value} does not exist.")

    def create(self, validated_data):
        staff = validated_data.pop('staff_id')
        validated_data['staff'] = staff
        validated_data['staff_name'] = staff.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        staff = validated_data.pop('staff_id', None)
        if staff:
            instance.staff = staff
            instance.staff_name = staff.name
        return super().update(instance, validated_data)

class OvertimeCommentSerializer(serializers.ModelSerializer):
    overtime = serializers.PrimaryKeyRelatedField(queryset=Overtime.objects.all())
    comment_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = OvertimeComment
        fields = ['id', 'overtime', 'comment', 'commenter', 'comment_date']

class OvertimeSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    output_staff_id = serializers.CharField(source='staff.staff_id', read_only=True)
    staff_name = serializers.CharField(read_only=True)
    ot_date = CoerceDateField()
    ot_start_time = serializers.TimeField()
    ot_end_time = serializers.TimeField()
    duration = serializers.FloatField(read_only=True)
    request_date = CoerceDateField(read_only=True)
    comments = OvertimeCommentSerializer(many=True, read_only=True)
    submitted_by = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Overtime
        fields = [
            'id', 'staff', 'staff_id', 'output_staff_id', 'staff_name', 'ot_date',
            'ot_start_time', 'ot_end_time', 'duration', 'reason', 'status',
            'gm_status', 'mgmt_status', 'request_date', 'submitted_by', 'comments'
        ]
        read_only_fields = ['staff', 'output_staff_id', 'staff_name', 'request_date', 'duration']

    def validate(self, data):
        if data.get('ot_date') and data.get('ot_start_time') and data.get('ot_end_time'):
            start = datetime.combine(data['ot_date'], data['ot_start_time'])
            end = datetime.combine(data['ot_date'], data['ot_end_time'])
            if end < start:
                end = datetime.combine(data['ot_date'] + timezone.timedelta(days=1), data['ot_end_time'])
            if end <= start:
                raise serializers.ValidationError({"ot_end_time": "End time must be after start time."})
        return data

    def validate_staff_id(self, value):
        if not value:
            return None
        try:
            url_type = self.context.get('type', '').capitalize()
            staff = StaffDetails.objects.get(staff_id=value)
            if url_type and staff.staff_type != url_type:
                raise serializers.ValidationError(
                    f"Staff with staff_id {value} is not of type '{url_type}'."
                )
            return staff
        except StaffDetails.DoesNotExist:
            raise serializers.ValidationError(f"Staff with staff_id {value} does not exist.")

    def create(self, validated_data):
        staff = validated_data.pop('staff_id')
        validated_data['staff'] = staff
        validated_data['staff_name'] = staff.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        staff = validated_data.pop('staff_id', None)
        if staff:
            instance.staff = staff
            instance.staff_name = staff.name
        return super().update(instance, validated_data)

class FineCommentSerializer(serializers.ModelSerializer):
    fine = serializers.PrimaryKeyRelatedField(queryset=Fine.objects.all())
    comment_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = FineComment
        fields = ['id', 'fine', 'comment', 'commenter', 'comment_date']

class FineSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    output_staff_id = serializers.CharField(source='staff.staff_id', read_only=True)
    staff_name = serializers.CharField(read_only=True)
    request_date = CoerceDateField(read_only=True)
    comments = FineCommentSerializer(many=True, read_only=True)
    submitted_by = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Fine
        fields = [
            'id', 'staff', 'staff_id', 'output_staff_id', 'staff_name', 'fine_amount',
            'reason', 'status', 'gm_status', 'mgmt_status', 'request_date',
            'submitted_by', 'comments'
        ]
        read_only_fields = ['staff', 'output_staff_id', 'staff_name', 'request_date']

    def validate_staff_id(self, value):
        if not value:
            return None
        try:
            url_type = self.context.get('type', '').capitalize()
            staff = StaffDetails.objects.get(staff_id=value)
            if url_type and staff.staff_type != url_type:
                raise serializers.ValidationError(
                    f"Staff with staff_id {value} is not of type '{url_type}'."
                )
            return staff
        except StaffDetails.DoesNotExist:
            raise serializers.ValidationError(f"Staff with staff_id {value} does not exist.")

    def validate_fine_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Fine amount must be greater than zero.")
        return value

    def create(self, validated_data):
        staff = validated_data.pop('staff_id')
        validated_data['staff'] = staff
        validated_data['staff_name'] = staff.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        staff = validated_data.pop('staff_id', None)
        if staff:
            instance.staff = staff
            instance.staff_name = staff.name
        return super().update(instance, validated_data)

class AppraisalCommentSerializer(serializers.ModelSerializer):
    appraisal = serializers.PrimaryKeyRelatedField(queryset=Appraisal.objects.all())
    comment_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AppraisalComment
        fields = ['id', 'appraisal', 'comment', 'commenter', 'comment_date']

class AppraisalSerializer(serializers.ModelSerializer):
    staff_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    output_staff_id = serializers.CharField(source='staff.staff_id', read_only=True)
    staff_name = serializers.CharField(read_only=True)
    request_date = CoerceDateField(read_only=True)
    comments = AppraisalCommentSerializer(many=True, read_only=True)
    submitted_by = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Appraisal
        fields = [
            'id', 'staff', 'staff_id', 'output_staff_id', 'staff_name', 'appraisal_amount',
            'reason', 'status', 'gm_status', 'mgmt_status', 'request_date',
            'submitted_by', 'comments'
        ]
        read_only_fields = ['staff', 'output_staff_id', 'staff_name', 'request_date']

    def validate_staff_id(self, value):
        if not value:
            return None
        try:
            url_type = self.context.get('type', '').capitalize()
            staff = StaffDetails.objects.get(staff_id=value)
            if url_type and staff.staff_type != url_type:
                raise serializers.ValidationError(
                    f"Staff with staff_id {value} is not of type '{url_type}'."
                )
            return staff
        except StaffDetails.DoesNotExist:
            raise serializers.ValidationError(f"Staff with staff_id {value} does not exist.")

    def validate_appraisal_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Appraisal amount must be greater than zero.")
        return value

    def create(self, validated_data):
        staff = validated_data.pop('staff_id')
        validated_data['staff'] = staff
        validated_data['staff_name'] = staff.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        staff = validated_data.pop('staff_id', None)
        if staff:
            instance.staff = staff
            instance.staff_name = staff.name
        return super().update(instance, validated_data)