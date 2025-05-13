from rest_framework import serializers
from .models import Contact, Inquiry, Quote, QuoteProduct, OutgoingMail, OrderService, SalesOrder, Vehicle, JobCard
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



class OrderServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderService
        fields = ['sorp', 'barcode', 'service_title', 'qty', 'rate', 'unit', 'amount']

    def validate(self, data):
        if not data.get('service_title'):
            raise serializers.ValidationError({"service_title": "Service title is required."})
        if data.get('qty', 0) <= 0:
            raise serializers.ValidationError({"qty": "Quantity must be greater than 0."})
        if data.get('rate', 0) <= 0:
            raise serializers.ValidationError({"rate": "Rate must be greater than 0."})
        return data

class SalesOrderSerializer(serializers.ModelSerializer):
    order_services = OrderServiceSerializer(many=True, required=False)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    contact_name = serializers.CharField(read_only=True, allow_null=True)
    contact_number = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'company_name', 'contact_email', 'order_no', 'company_email', 'lpo_no', 'address',
            'subject', 'terms_and_conditions', 'issue_date', 'currency',
            'cust_ref', 'our_ref', 'advance_amount', 'remarks', 'payment_terms',
            'delivery_terms', 'omc_cost', 'subtotal', 'vat', 'net_total', 'created_by',
            'created_by_username', 'created_on', 'order_services', 'status', 'accounts_status',
            'gm_status', 'mgmt_status', 'contact_name', 'contact_number'
        ]
        read_only_fields = ['id', 'order_no', 'created_by', 'created_by_username', 'created_on', 'contact_name', 'contact_number']

    def validate(self, data):
        
        print("Incoming data:", data)

        if self.partial:
            return data

        required_fields = [
            'company_name', 'contact_email', 'lpo_no', 'address', 'subject',
            'issue_date', 'currency', 'payment_terms', 'delivery_terms'
        ]
        errors = {}
        for field in required_fields:
            if not data.get(field):
                errors[field] = f"{field.replace('_', ' ')} is required."
        
        if not data.get('order_services'):
            errors['order_services'] = "At least one service is required."
        
        
        company_name = data.get('company_name')
        if company_name:
            try:
                contact = Contact.objects.get(company_name=company_name)
                data['contact_name'] = contact.contact_name
                data['contact_number'] = contact.contact_number
                
                if data.get('contact_email') and data['contact_email'] != contact.contact_email:
                    errors['contact_email'] = "Contact email must match the email of the selected company."
                else:
                    data['contact_email'] = contact.contact_email
                
                if not data.get('company_email'):
                    data['company_email'] = contact.company_email
            except Contact.DoesNotExist:
                errors['company_name'] = "Company does not exist in contacts."
        else:
            errors['company_name'] = "Company name is required."

        if errors:
            raise serializers.ValidationError(errors)
        
        
        services = data.get('order_services', [])
        subtotal = sum((service.get('qty', 0) * service.get('rate', 0)) for service in services)
        vat = subtotal * 0.05  
        net_total = subtotal + vat

        data['subtotal'] = subtotal
        data['vat'] = vat
        data['net_total'] = net_total

        return data

    def create(self, validated_data):
        services_data = validated_data.pop('order_services')
        validated_data['order_no'] = SalesOrder.generate_unique_order_no()
        sales_order = SalesOrder.objects.create(**validated_data)
        
        for service_data in services_data:
            OrderService.objects.create(sales_order=sales_order, **service_data)
        
        return sales_order

    def update(self, instance, validated_data):
        services_data = validated_data.pop('order_services', None)
        
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        
        if services_data is not None:
            instance.order_services.all().delete()
            for service_data in services_data:
                OrderService.objects.create(sales_order=instance, **service_data)
            
            
            instance.subtotal = sum(service.qty * service.rate for service in instance.order_services.all())
            instance.vat = instance.subtotal * 0.05
            instance.net_total = instance.subtotal + instance.vat

        instance.save()
        return instance
    
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['chassis_number', 'specification', 'remarks', 'vehicle_make', 'vehicle_type']

    def validate(self, data):
        if not data.get('chassis_number'):
            raise serializers.ValidationError({"chassis_number": "Chassis number is required."})
        return data

class JobCardSerializer(serializers.ModelSerializer):
    vehicles = VehicleSerializer(many=True, required=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    contact_name = serializers.CharField(read_only=True, allow_null=True)
    contact_number = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = JobCard
        fields = [
            'id', 'job_card_no', 'company_name', 'contact_email', 'sales_order_number', 'quantity', 'status',
            'remarks', 'created_by', 'created_by_username', 'created_on', 'vehicles',
            'contact_name', 'contact_number'
        ]
        read_only_fields = ['id', 'job_card_no', 'created_by', 'created_by_username', 'created_on', 'contact_name', 'contact_number']

    def validate(self, data):
        if self.partial:
            return data
        
        errors = {}
        required_fields = ['company_name', 'contact_email', 'sales_order_number', 'quantity']
        for field in required_fields:
            if not data.get(field):
                errors[field] = f"{field.replace('_', ' ')} is required."

        if data.get('quantity', 0) <= 0:
            errors['quantity'] = "Quantity must be greater than 0."

        if not data.get('vehicles'):
            errors['vehicles'] = "At least one vehicle is required."

        company_name = data.get('company_name')
        if company_name:
            try:
                contact = Contact.objects.get(company_name=company_name)
                data['contact_name'] = contact.contact_name
                data['contact_number'] = contact.contact_number
                if data.get('contact_email') and data['contact_email'] != contact.contact_email:
                    errors['contact_email'] = "Contact email must match the email of the selected company."
                else:
                    data['contact_email'] = contact.contact_email
            except Contact.DoesNotExist:
                errors['company_name'] = "Company does not exist in contacts."

        sales_order_number = data.get('sales_order_number')
        if sales_order_number and not SalesOrder.objects.filter(order_no=sales_order_number).exists():
            errors['sales_order_number'] = "Invalid sales order number."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        vehicles_data = validated_data.pop('vehicles')
        validated_data['created_by'] = self.context['request'].user
        job_card = JobCard.objects.create(**validated_data)

        for vehicle_data in vehicles_data:
            Vehicle.objects.create(job_card=job_card, **vehicle_data)

        return job_card

    def update(self, instance, validated_data):
        vehicles_data = validated_data.pop('vehicles', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if vehicles_data is not None:
            instance.vehicles.all().delete()
            for vehicle_data in vehicles_data:
                Vehicle.objects.create(job_card=instance, **vehicle_data)

        instance.save()
        return instance