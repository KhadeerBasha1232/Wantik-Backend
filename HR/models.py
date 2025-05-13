from django.db import models
from datetime import date, timedelta, datetime
from django.utils import timezone

class StaffDetails(models.Model):
    VISA_STATUS_CHOICES = (
        ('Renewed', 'Renewed'),
        ('In Progress', 'In Progress'),
        ('Expired', 'Expired'),
        ('Expiring Soon', 'Expiring Soon'),
        ('New Visa', 'New Visa'),
    )

    STAFF_TYPE_CHOICES = (
        ('Staff', 'Staff'),
        ('Manpower', 'Manpower'),
    )

    staff_id = models.CharField(max_length=50, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=255)
    passport_no = models.CharField(max_length=50, unique=True)
    visa_no = models.CharField(max_length=50, unique=True)
    emirates_id_number = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    insurance_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    passport_expiry = models.DateField()
    visa_expiry = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    emergency_contact = models.CharField(max_length=255)
    insurance_expiry = models.DateField()
    contact_number = models.CharField(max_length=20)
    profile_photo = models.ImageField(upload_to='staff_photos/', null=True, blank=True)
    offer_letter = models.FileField(upload_to='offer_letters/', null=True, blank=True)
    home_address = models.TextField()
    uae_address = models.TextField()
    joining_date = models.DateField(default=date.today, editable=False)
    visa_status = models.CharField(
        max_length=20,
        choices=VISA_STATUS_CHOICES,
        default='New Visa',
    )
    staff_type = models.CharField(
        max_length=20,
        choices=STAFF_TYPE_CHOICES,
        default='Staff',
    )

    def _get_visa_status(self):
        """Calculate visa_status based on visa_expiry and current date."""
        today = date.today()
        delta = self.visa_expiry - today

        if delta.days < 0:
            return 'Expired'
        elif delta.days <= 30:
            return 'Expiring Soon'
        else:
            return 'Renewed' if self.visa_status != 'New Visa' else 'New Visa'

    @property
    def visa_status_dynamic(self):
        """Dynamic property for visa_status."""
        return self._get_visa_status()

    def save(self, *args, **kwargs):
        if not self.staff_id:
            prefix = 'S' if self.staff_type == 'Staff' else 'M'
            last_staff = StaffDetails.objects.filter(staff_type=self.staff_type).order_by('-staff_id').first()
            if last_staff and last_staff.staff_id.startswith(prefix):
                last_number = int(last_staff.staff_id.replace(prefix, ''))
                new_number = last_number + 1
            else:
                new_number = 1
            self.staff_id = f'{prefix}{new_number}'
        self.visa_status = self._get_visa_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.staff_id})"

    class Meta:
        verbose_name = "Staff Detail"
        verbose_name_plural = "Staff Details"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('On Leave', 'On Leave'),
        ('Half Day', 'Half Day'),
    )

    staff = models.ForeignKey(StaffDetails, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('staff', 'date')
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"

    def __str__(self):
        return f"{self.staff.name} - {self.date} - {self.status}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Under Review', 'Under Review'),
        ('Rejected', 'Rejected'),
    ]
    EXTENDED_STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Under Review', 'Under Review'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending'),
    ]

    staff = models.ForeignKey(StaffDetails, on_delete=models.CASCADE, related_name='leave_requests')
    staff_name = models.CharField(max_length=100)  # Denormalized for display
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    submitted_by = models.CharField(max_length=100)  # Store username or user ID
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Under Review')
    gm_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    mgmt_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    request_date = models.DateField(default=date.today)

    class Meta:
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"

    def __str__(self):
        return f"{self.staff_name} ({self.staff.staff_id}) - {self.from_date} to {self.to_date}"

    def create_attendance_records(self):
        """Create or update Attendance records for each day in the leave period."""
        current_date = self.from_date
        while current_date <= self.to_date:
            attendance, created = Attendance.objects.get_or_create(
                staff=self.staff,
                date=current_date,
                defaults={
                    'status': 'On Leave',
                    'reason': self.reason,
                }
            )
            if not created and attendance.status != 'On Leave':
                attendance.status = 'On Leave'
                attendance.reason = self.reason
                attendance.save()
            current_date += timedelta(days=1)

    def remove_attendance_records(self):
        """Remove Attendance records marked as 'On Leave' for the leave period."""
        Attendance.objects.filter(
            staff=self.staff,
            date__range=(self.from_date, self.to_date),
            status='On Leave',
            reason=self.reason
        ).delete()

    def save(self, *args, **kwargs):
        # Ensure staff_name is set
        if not self.staff_name:
            self.staff_name = self.staff.name

        # Check if the instance already exists (update case)
        if self.pk:
            old_instance = LeaveRequest.objects.get(pk=self.pk)
            if old_instance.status == 'Approved' and self.status != 'Approved':
                # Status changed from Approved to something else, remove attendance records
                self.remove_attendance_records()
            elif self.status == 'Approved':
                # Status is Approved, create or update attendance records
                self.create_attendance_records()
        else:
            # New instance, only create attendance records if status is Approved
            if self.status == 'Approved':
                self.create_attendance_records()

        super().save(*args, **kwargs)

class LeaveComment(models.Model):
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commenter = models.CharField(max_length=100)  # Store username or role (e.g., GM, Mgmt)
    comment_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Leave Comment"
        verbose_name_plural = "Leave Comments"

    def __str__(self):
        return f"{self.commenter} on {self.leave_request} - {self.comment_date}"
    
class Loan(models.Model):
    LOAN_STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Cleared', 'Cleared'),
        ('Pending', 'Pending'),
    ]
    EXTENDED_STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Under Review', 'Under Review'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending'),
    ]

    staff = models.ForeignKey(StaffDetails, on_delete=models.CASCADE, related_name='loans')
    staff_name = models.CharField(max_length=100)  # Denormalized for display
    from_date = models.DateField()  # Borrowing date
    to_date = models.DateField()  # Return date
    reason = models.TextField()
    submitted_by = models.CharField(max_length=100)  # Store username or user ID
    loan_status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='Pending')
    gm_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    mgmt_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    request_date = models.DateField(default=date.today)

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"

    def __str__(self):
        return f"{self.staff_name} ({self.staff.staff_id}) - {self.from_date} to {self.to_date}"

    def save(self, *args, **kwargs):
        # Ensure staff_name is set
        if not self.staff_name:
            self.staff_name = self.staff.name
        super().save(*args, **kwargs)

class LoanComment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commenter = models.CharField(max_length=100)  # Store username or role (e.g., GM, Mgmt)
    comment_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Loan Comment"
        verbose_name_plural = "Loan Comments"

    def __str__(self):
        return f"{self.commenter} on {self.loan} - {self.comment_date}"
    
class Overtime(models.Model):
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending'),
    ]
    EXTENDED_STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Under Review', 'Under Review'),
        ('Pending', 'Pending'),
    ]

    staff = models.ForeignKey(StaffDetails, on_delete=models.CASCADE, related_name='overtimes')
    staff_name = models.CharField(max_length=100)  # Denormalized for display
    ot_date = models.DateField()  # Date of overtime work
    ot_start_time = models.TimeField()  # Start time of overtime
    ot_end_time = models.TimeField()  # End time of overtime
    duration = models.FloatField(blank=True)  # Duration in hours, calculated
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    gm_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    mgmt_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    request_date = models.DateField(default=date.today)
    submitted_by = models.CharField(max_length=100)  # Store username or user ID

    class Meta:
        verbose_name = "Overtime"
        verbose_name_plural = "Overtimes"

    def __str__(self):
        return f"{self.staff_name} ({self.staff.staff_id}) - {self.ot_date} ({self.ot_start_time} to {self.ot_end_time})"

    def calculate_duration(self):
        """Calculate duration in hours between ot_start_time and ot_end_time."""
        start = datetime.combine(self.ot_date, self.ot_start_time)
        end = datetime.combine(self.ot_date, self.ot_end_time)
        # Handle case where end_time is on the next day (e.g., 10 PM to 2 AM)
        if end < start:
            end = datetime.combine(self.ot_date + timezone.timedelta(days=1), self.ot_end_time)
        duration = (end - start).total_seconds() / 3600.0  # Convert to hours
        return round(duration, 2)  # Round to 2 decimal places

    def save(self, *args, **kwargs):
        # Ensure staff_name is set
        if not self.staff_name:
            self.staff_name = self.staff.name
        # Calculate duration
        self.duration = self.calculate_duration()
        super().save(*args, **kwargs)

class OvertimeComment(models.Model):
    overtime = models.ForeignKey(Overtime, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commenter = models.CharField(max_length=100)  # Store username or role (e.g., GM, Mgmt)
    comment_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Overtime Comment"
        verbose_name_plural = "Overtime Comments"

    def __str__(self):
        return f"{self.commenter} on {self.overtime} - {self.comment_date}"
    
class Fine(models.Model):
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending'),
    ]
    EXTENDED_STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Under Review', 'Under Review'),
        ('Pending', 'Pending'),
    ]

    staff = models.ForeignKey(StaffDetails, on_delete=models.CASCADE, related_name='fines')
    staff_name = models.CharField(max_length=100)  # Denormalized for display
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Fine amount in currency
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    gm_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    mgmt_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    request_date = models.DateField(default=date.today)
    submitted_by = models.CharField(max_length=100)  # Store username

    class Meta:
        verbose_name = "Fine"
        verbose_name_plural = "Fines"

    def __str__(self):
        return f"{self.staff_name} ({self.staff.staff_id}) - {self.fine_amount} ({self.request_date})"

    def save(self, *args, **kwargs):
        # Ensure staff_name is set
        if not self.staff_name:
            self.staff_name = self.staff.name
        super().save(*args, **kwargs)

class FineComment(models.Model):
    fine = models.ForeignKey(Fine, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commenter = models.CharField(max_length=100)  # Store username or role
    comment_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Fine Comment"
        verbose_name_plural = "Fine Comments"

    def __str__(self):
        return f"{self.commenter} on {self.fine} - {self.comment_date}"
    
class Appraisal(models.Model):
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending'),
    ]
    EXTENDED_STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Under Review', 'Under Review'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending'),
    ]

    staff = models.ForeignKey(StaffDetails, on_delete=models.CASCADE, related_name='appraisals')
    staff_name = models.CharField(max_length=100)  # Denormalized for display
    appraisal_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in currency
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    gm_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    mgmt_status = models.CharField(max_length=20, choices=EXTENDED_STATUS_CHOICES, default='Pending')
    request_date = models.DateField(default=date.today)
    submitted_by = models.CharField(max_length=100)  # Store username

    class Meta:
        verbose_name = "Appraisal"
        verbose_name_plural = "Appraisals"

    def __str__(self):
        return f"{self.staff_name} ({self.staff.staff_id}) - Amount: {self.appraisal_amount} ({self.request_date})"

    def save(self, *args, **kwargs):
        # Ensure staff_name is set
        if not self.staff_name:
            self.staff_name = self.staff.name
        super().save(*args, **kwargs)

class AppraisalComment(models.Model):
    appraisal = models.ForeignKey(Appraisal, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commenter = models.CharField(max_length=100)  # Store username or role
    comment_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Appraisal Comment"
        verbose_name_plural = "Appraisal Comments"

    def __str__(self):
        return f"{self.commenter} on {self.appraisal} - {self.comment_date}"