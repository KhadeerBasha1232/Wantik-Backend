from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
import random 

class Contact(models.Model):
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    company_email = models.EmailField()
    contact_email = models.EmailField()
    company_number = models.CharField(max_length=20)
    contact_number = models.CharField(max_length=20)
    license_number = models.CharField(max_length=100)
    license_expiry_date = models.DateField()
    tirn_number = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contacts")
    created_on = models.DateTimeField(default=timezone.now)
    license_file = models.FileField(upload_to='licenses/')

    def __str__(self):
        return f"{self.company_name} - {self.contact_name}"
    
class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    inquiry = models.TextField()
    assign_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="inquiries")
    assign_to_username = models.CharField(max_length=255, blank=True)  
    created_on = models.DateTimeField(default=timezone.now)
    year = models.PositiveIntegerField(default=timezone.now().year)  

    def save(self, *args, **kwargs):
        
        if not self.year:
            self.year = self.created_on.year
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Inquiry from {self.company_name} - {self.contact_name} ({self.status})"


class Quote(models.Model):

    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    year = models.IntegerField()
    quote_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField()
    company_email = models.EmailField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    quote_no = models.CharField(max_length=5)
    vat_applicable = models.BooleanField(default=False)
    vat_percentage = models.FloatField(default=0)
    subtotal = models.FloatField()
    vat_amount = models.FloatField()
    grand_total = models.FloatField()
    notes_remarks = models.TextField(blank=True)
    assign_to = models.ForeignKey(User, related_name="assigned_quotes", on_delete=models.SET_NULL, null=True)
    created_by = models.ForeignKey(User, related_name="created_quotes", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField(auto_now_add=True)
    invoice_pdf = models.FileField(upload_to='invoices/', blank=True, null=True)

    def __str__(self):
        return f"{self.quote_title} ({self.quote_no})"


    @staticmethod
    def generate_unique_quote_no():
        max_attempts = 10
        for _ in range(max_attempts):
            
            new_quote_no = random.randint(10000, 99999)
            
            if not Quote.objects.filter(quote_no=str(new_quote_no).zfill(5)).exists():
                return str(new_quote_no).zfill(5)
        raise ValueError("Unable to generate a unique quote number after multiple attempts.")

class QuoteProduct(models.Model):
    quote = models.ForeignKey(Quote, related_name='products', on_delete=models.CASCADE)
    product = models.CharField(max_length=255)
    specification = models.TextField(blank=True)
    qty = models.IntegerField()
    unit_price = models.FloatField()
    total_price = models.FloatField()

    def save(self, *args, **kwargs):
        self.total_price = self.qty * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.qty} x {self.unit_price}"

class OutgoingMail(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    company_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True, null=True)  
    contact_number = models.CharField(max_length=20, blank=True, null=True)  
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    message = models.TextField()
    created_on = models.DateTimeField(default=timezone.now)
    year = models.PositiveIntegerField(default=timezone.now().year)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outgoing_mails")
    company_email = models.EmailField(blank=True, null=True)  
    contact_email = models.EmailField(blank=True, null=True)  
    mail_subject = models.CharField(max_length=255)
    quote_no = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.year:
            self.year = self.created_on.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mail to {self.company_name} - {self.contact_name or 'No Contact'} ({self.status})"