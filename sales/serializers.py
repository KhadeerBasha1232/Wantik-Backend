from rest_framework import serializers
from .models import Contact, Inquiry, Quote, QuoteProduct, OutgoingMail
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class ContactSerializer(serializers.ModelSerializer):
    license_file = serializers.FileField(required=False)
    class Meta:
        model = Contact
        exclude = ['created_by']

class InquirySerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(required=False)
    assign_to_username = serializers.CharField(source='assign_to.username', read_only=True)

    class Meta:
        model = Inquiry
        fields = ['id', 'company_name', 'contact_name', 'contact_number', 'status', 'inquiry', 
                  'assign_to', 'assign_to_username', 'created_on', 'year']

class QuoteProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteProduct
        fields = ['product', 'specification', 'qty', 'unit_price', 'total_price']
        read_only_fields = ['total_price']  

    def validate(self, data):
        if not data.get('product').strip():
            raise serializers.ValidationError({"product": "Product name cannot be empty."})
        if data.get('qty') <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than 0."})
        if data.get('unit_price') < 0:
            raise serializers.ValidationError({"unit_price": "Unit price cannot be negative."})
        return data

class QuoteSerializer(serializers.ModelSerializer):
    products = QuoteProductSerializer(many=True, required=False)
    assign_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )
    created_by = UserSerializer(read_only=True)
    quote_no = serializers.CharField(required=False)

    class Meta:
        model = Quote
        fields = [
            'id', 'year', 'quote_title', 'company_name', 'contact_name',
            'contact_number', 'contact_email', 'company_email', 'status',
            'quote_no', 'vat_applicable', 'vat_percentage', 'subtotal',
            'vat_amount', 'grand_total', 'notes_remarks', 'assign_to',
            'created_by', 'create_date', 'products', 'invoice_pdf'
        ]
        read_only_fields = ['id', 'created_by', 'create_date', 'contact_name', 'contact_number']

    def validate(self, data):
        if self.instance is None or 'products' in data:
            if not data.get('products'):
                raise serializers.ValidationError({"products": "At least one product is required."})

            
            expected_subtotal = sum(
                product_data['qty'] * product_data['unit_price']
                for product_data in data.get('products')
            )

            
            subtotal = data.get('subtotal', self.instance.subtotal if self.instance else 0)
            if not isinstance(subtotal, (int, float)) or subtotal <= 0:
                raise serializers.ValidationError({"subtotal": "Subtotal must be a positive number."})
            if abs(subtotal - expected_subtotal) > 0.01:  
                raise serializers.ValidationError({
                    "subtotal": f"Subtotal ({subtotal}) does not match the sum of product totals ({expected_subtotal})."
                })

            
            vat_percentage = data.get('vat_percentage', self.instance.vat_percentage if self.instance else 0)
            vat_applicable = data.get('vat_applicable', self.instance.vat_applicable if self.instance else False)
            expected_vat_amount = (subtotal * vat_percentage / 100) if vat_applicable else 0
            vat_amount = data.get('vat_amount', self.instance.vat_amount if self.instance else 0)
            if not isinstance(vat_amount, (int, float)):
                raise serializers.ValidationError({"vat_amount": "VAT amount must be a number."})
            if abs(vat_amount - expected_vat_amount) > 0.01:
                raise serializers.ValidationError({
                    "vat_amount": f"VAT amount ({vat_amount}) does not match expected value ({expected_vat_amount})."
                })

            
            grand_total = data.get('grand_total', self.instance.grand_total if self.instance else 0)
            expected_grand_total = subtotal + expected_vat_amount
            if not isinstance(grand_total, (int, float)):
                raise serializers.ValidationError({"grand_total": "Grand total must be a number."})
            if abs(grand_total - expected_grand_total) > 0.01:
                raise serializers.ValidationError({
                    "grand_total": f"Grand total ({grand_total}) does not match expected value ({expected_grand_total})."
                })

        return data

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        validated_data['created_by'] = self.context['request'].user
        validated_data['assign_to'] = validated_data.get('assign_to', self.context['request'].user)
        quote = Quote.objects.create(**validated_data)
        
        
        for product_data in products_data:
            QuoteProduct.objects.create(quote=quote, **product_data)
        
        return quote

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)
        
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        
        if products_data:
            instance.products.all().delete()
            for product_data in products_data:
                QuoteProduct.objects.create(quote=instance, **product_data)
        
        return instance
    

class OutgoingMailSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    company_name = serializers.CharField(required=False)
    mail_subject = serializers.CharField(required=False)
    class Meta:
        model = OutgoingMail
        fields = [
            'id', 'company_name', 'contact_name', 'contact_number', 'status', 'message',
            'created_on', 'year', 'created_by', 'created_by_username', 'company_email',
            'contact_email', 'mail_subject', 'quote_no'
        ]
        read_only_fields = ['created_by', 'created_by_username', 'created_on', 'year']

    def validate(self, data):
        
        if 'message' in data and not data.get('message'):
            raise serializers.ValidationError({"message": "This field is required."})
        return data