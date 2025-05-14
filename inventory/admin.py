from django.contrib import admin
from .models import Category, SubCategory, Product, RemovalRequest, RemovalRequestItem
# Register your models here.
admin.site.register([
    # Register your models here.
    Category,
    SubCategory,
    Product,
    RemovalRequest,
    RemovalRequestItem,
])