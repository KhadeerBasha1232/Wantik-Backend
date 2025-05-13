from django.urls import path
from .views import index, ContactCreateView, ContactListView,SalesOrderDetailView, SalesOrderListCreateView,OrderCompanyListView, ContactDetailView, InquiryListCreateView, InquiryDetailView, IncomingCompanyListView, user_list, QuoteListCreateView, QuoteDetailView, QuotationCompanyListView, OutgoingMailListCreateView, OutgoingMailDetailView, JobCardListCreateView, JobCardDetailView

urlpatterns = [
    path('', index, name='index'),
    path('contacts/', ContactCreateView.as_view(), name='contact-create'),
    path('contacts/all/', ContactListView.as_view(), name='contact-list'),
    path('contacts/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
    path('inquiries/', InquiryListCreateView.as_view(), name='inquiry_list_create'),
    path('inquiries/<int:pk>/', InquiryDetailView.as_view(), name='inquiry_detail'),
    path('quotes/', QuoteListCreateView.as_view(), name='quote-list-create'),
    path('quotes/<int:pk>/', QuoteDetailView.as_view(), name='quote-detail'),
    path('outgoing-mails/', OutgoingMailListCreateView.as_view(), name='outgoing-mail-list-create'),
    path('outgoing-mails/<int:pk>/', OutgoingMailDetailView.as_view(), name='outgoing-mail-detail'),
    path('incoming-companies/', IncomingCompanyListView.as_view(), name='company-list'),  
    path('quotation-companies/', QuotationCompanyListView.as_view(), name='company-list'),  
    path('order-companies/', OrderCompanyListView.as_view(), name='company-list'),  
    path('users/', user_list, name='user-list'), 
    path('sales-orders/', SalesOrderListCreateView.as_view(), name='sales-order-list-create'),
    path('sales-orders/<int:pk>/', SalesOrderDetailView.as_view(), name='sales-order-detail'),
    path('job-cards/', JobCardListCreateView.as_view(), name='job-card-list-create'),
    path('job-cards/<int:pk>/', JobCardDetailView.as_view(), name='job-card-detail'),
]
