from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CountryViewSet, DocumentSetViewSet, CustomerViewSet, CustomerDocumentViewSet, extract_details_from_id,login_view,list_customers,save_details,get_country

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'countries', CountryViewSet)
router.register(r'documentsets', DocumentSetViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'customerdocuments', CustomerDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('extract-details/', extract_details_from_id, name='extract_details'),
    path('login/', login_view, name='login'),
    path('customers/', list_customers, name='list_customers'),
    path('save-details/',save_details,name='save-details'),
    path('countries/',get_country,name='get_country'),
]
