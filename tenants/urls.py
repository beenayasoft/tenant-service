from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, validate_tenant, health_check

app_name = 'tenants'

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    # Routes du router (CRUD des tenants)
    path('', include(router.urls)),
    
    # Endpoints spéciaux pour les autres services
    path('tenants/<uuid:tenant_id>/validate/', validate_tenant, name='validate_tenant'),
    
    # Endpoint de santé
    path('health/', health_check, name='health_check'),
]
