from django.contrib import admin
from .models import Contact, Inquiry, Quote, QuoteProduct, OutgoingMail, OrderService, SalesOrder, JobCard


admin.site.register([
    Contact,
    Inquiry,
    Quote,
    QuoteProduct,
    OutgoingMail,
    OrderService,
    SalesOrder,
    JobCard,
])