from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    CATEGORY_CHOICES = [
        ('OPEN', 'Open / General'),
        ('OBC', 'OBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('EWS', 'EWS'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    prn_number = models.CharField(max_length=30, unique=True, verbose_name="PRN / Roll No")
    course = models.CharField(max_length=100, default="B.C.A")
    current_year = models.CharField(max_length=20, default="Third Year")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Previous exam percentage")
    annual_income = models.DecimalField(max_digits=10, decimal_places=2, help_text="Annual family income in INR")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='OPEN')
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.prn_number})"


class Scholarship(models.Model):
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=150, help_text="e.g., Govt. of Maharashtra / College Trust")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    max_income = models.DecimalField(max_digits=10, decimal_places=2, default=800000.00)
    allowed_category = models.CharField(max_length=50, default="ALL", help_text="ALL, OPEN, OBC, SC, ST, EWS")
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Verification'),
        ('Verified', 'Documents Verified'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE)
    marksheet = models.FileField(upload_to='documents/marksheets/')
    income_certificate = models.FileField(upload_to='documents/income_certs/')
    id_proof = models.FileField(upload_to='documents/id_proofs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_remarks = models.TextField(blank=True, null=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'scholarship')

    def __str__(self):
        return f"{self.student.prn_number} - {self.scholarship.title} ({self.status})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To {self.user.username}: {self.message}"
