from rest_framework import serializers
from .models import Category, SubCategory, Product, StockHistory, RemovalRequest, RemovalRequestItem
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'created_at']

class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'category_id', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    subcategory = SubCategorySerializer(read_only=True)
    subcategory_id = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(), source='subcategory', write_only=True
    )
    measurement_unit = serializers.CharField(max_length=50)
    added_by = serializers.StringRelatedField(read_only=True)

    def validate(self, data):
        if data['type'] == 'imported' and not data.get('origin'):
            raise serializers.ValidationError({"origin": "Origin is required for imported products."})
        if data['type'] == 'local' and data.get('origin'):
            raise serializers.ValidationError({"origin": "Origin should not be set for local products."})
        return data

    class Meta:
        model = Product
        fields = [
            'id', 'product_id', 'type', 'origin', 'category', 'category_id', 'subcategory', 'subcategory_id',
            'product_name', 'description', 'part_no', 'storage_location', 'remarks',
            'measurement_unit', 'stock_count', 'added_by', 'added_on', 'quantity_added', 'condition'
        ]

class StockHistorySerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    added_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StockHistory
        fields = [
            'id', 'product', 'product_id', 'quantity_added', 'added_by',
            'added_on', 'remarks'
        ]

class RemovalRequestItemSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        product = data['product_id']
        quantity = data['quantity']
        if quantity > product.stock_count:
            raise serializers.ValidationError({
                'quantity': f"Quantity ({quantity}) exceeds available stock ({product.stock_count}) for product {product.product_name}."
            })
        return data

class RemovalRequestSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    product_items = RemovalRequestItemSerializer(many=True, write_only=True)
    requested_by = serializers.StringRelatedField(read_only=True)
    type = serializers.ChoiceField(choices=RemovalRequest.TYPE_CHOICES)
    removal_type = serializers.ChoiceField(choices=RemovalRequest.REMOVAL_TYPE_CHOICES)
    accounts_status = serializers.ChoiceField(choices=RemovalRequest.STATUS_CHOICES, default='pending')
    gm_status = serializers.ChoiceField(choices=RemovalRequest.STATUS_CHOICES, default='pending')
    mgmt_status = serializers.ChoiceField(choices=RemovalRequest.STATUS_CHOICES, default='pending')

    def validate(self, data):
        type_value = data.get('type')
        product_items = data.get('product_items', [])
        for item in product_items:
            product = item['product_id']
            if product.type != type_value:
                raise serializers.ValidationError({
                    'product_items': f"Product {product.product_id} type ({product.type}) does not match request type ({type_value})."
                })
        return data

    def create(self, validated_data):
        product_items = validated_data.pop('product_items', [])
        request = RemovalRequest.objects.create(**validated_data)
        for item in product_items:
            RemovalRequestItem.objects.create(
                request=request,
                product=item['product_id'],
                quantity=item['quantity']
            )
        return request

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['products'] = ProductSerializer(
            [item.product for item in instance.items.all()], many=True
        ).data
        representation['product_items'] = [
            {'product_id': item.product.id, 'quantity': item.quantity}
            for item in instance.items.all()
        ]
        return representation

    class Meta:
        model = RemovalRequest
        fields = [
            'id', 'request_no', 'products', 'product_items', 'remarks', 'type', 'removal_type',
            'accounts_status', 'gm_status', 'mgmt_status', 'requested_by', 'created_date',
            'gm_remarks', 'mgmt_remarks'
        ]