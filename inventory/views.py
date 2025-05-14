from rest_framework import generics
from rest_framework.exceptions import ValidationError
from .models import Category, SubCategory, Product, StockHistory, RemovalRequest, RemovalRequestItem
from .serializers import (
    CategorySerializer, SubCategorySerializer, ProductSerializer,
    StockHistorySerializer, RemovalRequestSerializer
)
from django.db import transaction

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class SubCategoryListCreateView(generics.ListCreateAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer

class SubCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        type_param = self.kwargs['type']
        if type_param not in ['local', 'imported']:
            raise ValidationError({'type': 'Invalid type. Must be "local" or "imported".'})
        return Product.objects.filter(type=type_param)

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        type_param = self.kwargs['type']
        if type_param not in ['local', 'imported']:
            raise ValidationError({'type': 'Invalid type. Must be "local" or "imported".'})
        return Product.objects.filter(type=type_param)

class StockHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = StockHistorySerializer

    def get_queryset(self):
        type_param = self.kwargs['type']
        if type_param not in ['local', 'imported']:
            raise ValidationError({'type': 'Invalid type. Must be "local" or "imported".'})
        return StockHistory.objects.filter(product__type=type_param)

    def perform_create(self, serializer):
        with transaction.atomic():
            product = serializer.validated_data['product']
            quantity_added = serializer.validated_data['quantity_added']
            product.stock_count += quantity_added
            product.quantity_added += quantity_added
            product.save()
            serializer.save(added_by=self.request.user)

class StockHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StockHistorySerializer

    def get_queryset(self):
        type_param = self.kwargs['type']
        if type_param not in ['local', 'imported']:
            raise ValidationError({'type': 'Invalid type. Must be "local" or "imported".'})
        return StockHistory.objects.filter(product__type=type_param)

class RemovalRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = RemovalRequestSerializer

    def get_queryset(self):
        type_param = self.kwargs['type']
        if type_param not in ['local', 'imported']:
            raise ValidationError({'type': 'Invalid type. Must be "local" or "imported".'})
        return RemovalRequest.objects.filter(type=type_param)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

class RemovalRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RemovalRequestSerializer

    def get_queryset(self):
        type_param = self.kwargs['type']
        if type_param not in ['local', 'imported']:
            raise ValidationError({'type': 'Invalid type. Must be "local" or "imported".'})
        return RemovalRequest.objects.filter(type=type_param)

    def perform_update(self, serializer):
        instance = serializer.save()
        print(f"Updated RemovalRequest {instance.request_no}")
        if (
            instance.accounts_status == "approved"
            and instance.gm_status == "approved"
            and instance.mgmt_status == "approved"
            and not instance.stock_deducted
        ):
            print(f"All statuses approved for RemovalRequest {instance.request_no}, deducting stock")
            try:
                with transaction.atomic():
                    for item in instance.items.select_related('product').all():
                        product = item.product
                        if product.stock_count >= item.quantity and product.quantity_added >= item.quantity:
                            print(
                                f"Deducting {item.quantity} from {product.product_name} "
                                f"(current stock_count: {product.stock_count}, quantity_added: {product.quantity_added})"
                            )
                            product.stock_count -= item.quantity
                            product.quantity_added -= item.quantity
                            product.save()
                        else:
                            error_message = (
                                f"Insufficient values for {product.product_name}: "
                                f"Requested {item.quantity}, "
                                f"Available stock_count: {product.stock_count}, "
                                f"Available quantity_added: {product.quantity_added}"
                            )
                            print(error_message)
                            raise ValueError(error_message)
                    instance.stock_deducted = True
                    instance.save()
                    print(f"Stock deducted and stock_deducted set to True for RemovalRequest {instance.request_no}")
            except Exception as e:
                print(f"Error deducting stock for RemovalRequest {instance.request_no}: {str(e)}")
                raise
        else:
            print(
                f"Conditions not met for stock deduction: "
                f"accounts_status={instance.accounts_status}, "
                f"gm_status={instance.gm_status}, "
                f"mgmt_status={instance.mgmt_status}, "
                f"stock_deducted={instance.stock_deducted}"
            )
