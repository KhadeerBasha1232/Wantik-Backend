from django.contrib import admin
from .models import Contact, Inquiry, Quote, QuoteProduct, OutgoingMail


admin.site.register([
    Contact,
    Inquiry,
    Quote,
    QuoteProduct,
    OutgoingMail
])