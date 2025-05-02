from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from .models import Inquiry, Contact
from .serializers import ContactSerializer, QuoteSerializer, OutgoingMailSerializer
import os
from .models import Inquiry, Quote, OutgoingMail
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from .serializers import InquirySerializer

def index(request):
    return HttpResponse("Hello, world. You're at the sales index.")


class ContactCreateView(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContactListView(generics.ListAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()  # Create a mutable copy of request.data

        # Handle license_file replacement
        if 'license_file' in data and data['license_file'] and data['license_file'] != 'null':
            # Delete existing file if it exists
            if instance.license_file:
                file_path = instance.license_file.path
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        return JsonResponse({"error": f"Failed to delete existing file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        elif 'license_file' in data and (data['license_file'] is None or data['license_file'] == 'null'):
            # Remove license_file from data if not provided or invalid
            data.pop('license_file')

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return JsonResponse(serializer.data)

    def delete(self, request, *args, **kwargs):
        contact = self.get_object()
        if contact.license_file:
            file_path = contact.license_file.path
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    return JsonResponse({"error": f"File deletion failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        return super().delete(request, *args, **kwargs)
    
class InquiryListCreateView(generics.ListCreateAPIView):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        
        company_name = self.request.data.get('company_name')
        contact_number = self.request.data.get('contact_number')

        if not company_name or not contact_number:
            raise ValueError("Company name and contact number are required.")

        
        try:
            company = Contact.objects.get(company_name=company_name, contact_number=contact_number)
        except Contact.DoesNotExist:
            return HttpResponse({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        
        data = {
            'company_name': company.company_name,
            'contact_name': company.contact_name,
            'contact_number': company.contact_number,
            'status': 'new',  
            'inquiry': self.request.data.get('inquiry'),
            'assign_to': self.request.user  
        }

        
        serializer.save(**data)

    def get_queryset(self):
        
        year = self.request.query_params.get('year', None)
        if year is not None:
            
            return Inquiry.objects.filter(year=year)
        
        return Inquiry.objects.all()



class InquiryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Inquiry.objects.all()
    
    
from django.http import JsonResponse

class IncomingCompanyListView(generics.ListAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        
        companies = Contact.objects.values('company_name','contact_number').distinct()
        return JsonResponse(list(companies), safe=False)

class QuotationCompanyListView(generics.ListAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        
        companies = Contact.objects.values('company_name','contact_email', 'company_email').distinct()
        return JsonResponse(list(companies), safe=False)
    
@api_view(['GET'])
def user_list(request):
    users = User.objects.all()
    user_data = [{"id": user.id, "username": user.username} for user in users]
    return JsonResponse(user_data, safe=False, status=200)

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from .utils import generate_invoice_pdf
from django.core.files import File

class QuoteListCreateView(generics.ListCreateAPIView):
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        year = self.request.query_params.get('year')
        if year:
            return Quote.objects.filter(year=year)
        return Quote.objects.all()

    def perform_create(self, serializer):
        
        quote_no = Quote.generate_unique_quote_no()
        while Quote.objects.filter(quote_no=quote_no).exists():
            quote_no = Quote.generate_unique_quote_no()

        
        company_name = self.request.data.get('company_name')
        try:
            contact = Contact.objects.get(company_name=company_name)
            quote = serializer.save(
                created_by=self.request.user,
                assign_to=self.request.user,
                contact_name=contact.contact_name,
                contact_number=contact.contact_number,
                quote_no=quote_no  
            )
        except ObjectDoesNotExist:
            quote = serializer.save(
                created_by=self.request.user,
                assign_to=self.request.user,
                contact_name='',
                contact_number='',
                quote_no=quote_no  
            )

        
        invoice_filename = f"invoice_{quote.quote_no}_{quote.id}.pdf"
        invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
        invoice_path = os.path.join(invoice_dir, invoice_filename)

        
        os.makedirs(invoice_dir, exist_ok=True)

        try:
            generate_invoice_pdf(quote, invoice_path)
            
            with open(invoice_path, 'rb') as pdf_file:
                quote.invoice_pdf.save(invoice_filename, File(pdf_file), save=True)
        except Exception as e:
            
            print(f"Failed to generate PDF for quote {quote.quote_no}: {str(e)}")
            
            quote.invoice_pdf = None
            quote.save()

class QuoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated]



from rest_framework.exceptions import ValidationError
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


class OutgoingMailListCreateView(generics.ListCreateAPIView):
    queryset = OutgoingMail.objects.all()
    serializer_class = OutgoingMailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        company_name = self.request.data.get('company_name')
        mail_subject = self.request.data.get('mail_subject')
        message = self.request.data.get('message')
        quote_no = self.request.data.get('quote_no', '')

        if not company_name:
            raise ValidationError({"company_name": "This field is required."})
        if not mail_subject:
            raise ValidationError({"mail_subject": "This field is required."})
        if not message:
            raise ValidationError({"message": "This field is required."})

        
        contact_name = ''
        contact_number = ''
        company_email = ''
        contact_email = ''
        email_status = 'new'  

        try:
            contact = Contact.objects.get(company_name=company_name)
            contact_name = contact.contact_name
            contact_number = contact.contact_number
            company_email = contact.company_email
            contact_email = contact.contact_email
        except Contact.DoesNotExist:
            
            pass

        
        outgoing_mail = serializer.save(
            created_by=self.request.user,
            contact_name=contact_name,
            contact_number=contact_number,
            company_email=company_email,
            contact_email=contact_email,
            status=email_status  
        )

        
        recipient_list = [email for email in [company_email, contact_email] if email]
        if recipient_list:
            try:
                
                email_context = {
                    'company_name': company_name,
                    'contact_name': contact_name or 'Recipient',
                    'message': message,
                    'quote_no': quote_no,
                    'sender': self.request.user.username,
                }
                email_body = render_to_string('email_template.html', email_context)
                
                email = EmailMessage(
                    subject=mail_subject,
                    body=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=recipient_list
                )
                email.content_subtype = 'html' if '<html' in email_body else 'plain'

                
                if quote_no:
                    print(quote_no)
                    try:
                        quote = Quote.objects.get(quote_no=quote_no)
                        print(quote.invoice_pdf)
                        if quote.invoice_pdf:
                            with quote.invoice_pdf.open('rb') as pdf_file:
                                email.attach(
                                    f'invoice_{quote_no}.pdf',
                                    pdf_file.read(),
                                    'application/pdf'
                                )
                        else:
                            print(f"No invoice PDF found for quote {quote_no}")
                    except Quote.DoesNotExist:
                        print(f"Quote with quote_no {quote_no} not found")

                
                email.send(fail_silently=False)
                outgoing_mail.status = 'new'
                outgoing_mail.save()
            except Exception as e:
                
                print(f"Failed to send email: {str(e)}")
                outgoing_mail.status = 'failed'
                outgoing_mail.save()
                
                raise ValidationError({"email": f"Failed to send email: {str(e)}"})
        else:
            
            outgoing_mail.status = 'failed'
            outgoing_mail.save()
            raise ValidationError({"email": "No valid email addresses found for this company."})

    def get_queryset(self):
        year = self.request.query_params.get('year', None)
        if year is not None:
            return OutgoingMail.objects.filter(year=year)
        return OutgoingMail.objects.all()

class OutgoingMailDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OutgoingMail.objects.all()
    serializer_class = OutgoingMailSerializer
    permission_classes = [permissions.IsAuthenticated]