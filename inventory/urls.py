from django.urls import path
from .views import (
    CategoryListCreateView, CategoryDetailView,
    SubCategoryListCreateView, SubCategoryDetailView,
    ProductListCreateView, ProductDetailView,
    StockHistoryListCreateView, StockHistoryDetailView,
    RemovalRequestListCreateView, RemovalRequestDetailView
)

urlpatterns = [
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('subcategories/', SubCategoryListCreateView.as_view(), name='subcategory-list-create'),
    path('subcategories/<int:pk>/', SubCategoryDetailView.as_view(), name='subcategory-detail'),
    path('<str:type>/products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('<str:type>/products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<str:type>/stock-history/', StockHistoryListCreateView.as_view(), name='stock-history-list-create'),
    path('<str:type>/stock-history/<int:pk>/', StockHistoryDetailView.as_view(), name='stock-history-detail'),
    path('<str:type>/removal-requests/', RemovalRequestListCreateView.as_view(), name='removal-request-list-create'),
    path('<str:type>/removal-requests/<int:pk>/', RemovalRequestDetailView.as_view(), name='removal-request-detail'),
]