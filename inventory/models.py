
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

def generate_product_id():
    """Generate a random 5-digit product ID."""
    return ''.join(random.choices(string.digits, k=5))

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        verbose_name_plural = "SubCategories"
        unique_together = ['name', 'category']

class Product(models.Model):
    TYPE_CHOICES = [
        ('local', 'Local'),
        ('imported', 'Imported'),
    ]
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]

    product_id = models.CharField(max_length=5, unique=True, default=generate_product_id)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, related_name="products")
    product_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    part_no = models.CharField(max_length=100, unique=True)
    storage_location = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)
    origin = models.CharField(max_length=100, blank=True, null=True)
    measurement_unit = models.CharField(max_length=50)
    stock_count = models.PositiveIntegerField(default=0)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="products_added")
    added_on = models.DateTimeField(auto_now_add=True)
    quantity_added = models.PositiveIntegerField(default=0)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')

    def __str__(self):
        return f"{self.product_name} ({self.product_id})"

    class Meta:
        verbose_name_plural = "Products"

class StockHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_history")
    quantity_added = models.PositiveIntegerField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="stock_additions")
    added_on = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity_added} added on {self.added_on}"

    class Meta:
        verbose_name_plural = "Stock Histories"

def generate_request_no():
    """Generate a random 5-digit request number."""
    return ''.join(random.choices(string.digits, k=5))

class RemovalRequest(models.Model):
    TYPE_CHOICES = [
        ('local', 'Local'),
        ('imported', 'Imported'),
    ]
    REMOVAL_TYPE_CHOICES = [
        ('sales', 'Sales'),
        ('deadstock', 'Deadstock'),
    ]
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('underreview', 'Under Review'),
        ('rejected', 'Rejected'),
    ]

    request_no = models.CharField(max_length=5, unique=True, default=generate_request_no)
    remarks = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    removal_type = models.CharField(max_length=20, choices=REMOVAL_TYPE_CHOICES)
    accounts_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gm_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mgmt_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="removal_requests")
    created_date = models.DateTimeField(auto_now_add=True)
    gm_remarks = models.TextField(blank=True)
    mgmt_remarks = models.TextField(blank=True)
    stock_deducted = models.BooleanField(default=False)  # Flag to prevent duplicate deductions

    def __str__(self):
        return f"Removal Request {self.request_no} ({self.type}, {self.removal_type})"

    class Meta:
        verbose_name_plural = "Removal Requests"

class RemovalRequestItem(models.Model):
    request = models.ForeignKey(RemovalRequest, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="removal_request_items")
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} (Request {self.request.request_no})"

    class Meta:
        verbose_name_plural = "Removal Request Items"
