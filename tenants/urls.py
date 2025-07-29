from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, validate_tenant, health_check, current_tenant_info,
    preview_document_number, increment_document_counter, 
    reset_document_counter, get_document_numbering_config,
    tenant_vat_rates, tenant_payment_terms
)
from .views_document_appearance import (
    tenant_document_appearance, document_appearance_defaults,
    document_template_choices, document_template_presets, color_presets
)

app_name = 'tenants'

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    # Routes du router (CRUD des tenants)
    path('', include(router.urls)),
    
    # Endpoints spéciaux pour les autres services
    path('tenants/<uuid:tenant_id>/validate/', validate_tenant, name='validate_tenant'),
    path('tenants/current_tenant_info/', current_tenant_info, name='current_tenant_info'),
    
    # Endpoints pour les taux de TVA
    # Corriger le chemin en supprimant le préfixe 'tenants/' redondant
    path('tenants/vat_rates/', tenant_vat_rates, name='tenant_vat_rates'),
    # Ajouter une route alternative sans le préfixe 'tenants/'
    path('vat_rates/', tenant_vat_rates, name='tenant_vat_rates_alt'),
    
    # Endpoints pour les conditions de paiement
    path('tenants/payment_terms/', tenant_payment_terms, name='tenant_payment_terms'),
    path('payment_terms/', tenant_payment_terms, name='tenant_payment_terms_alt'),
    
    # Endpoints pour la numérotation des documents
    path('tenants/preview-numbering/', preview_document_number, name='preview_document_number'),
    path('tenants/document_numbering/<str:document_type>/', get_document_numbering_config, name='get_document_numbering_config'),
    path('tenants/document_numbering/<uuid:numbering_id>/increment/', increment_document_counter, name='increment_document_counter'),
    path('tenants/document_numbering/<uuid:numbering_id>/reset/', reset_document_counter, name='reset_document_counter'),
    
    # Endpoints pour l'apparence des documents
    path('tenants/document_appearance/', tenant_document_appearance, name='tenant_document_appearance'),
    path('document_appearance/', tenant_document_appearance, name='tenant_document_appearance_alt'),
    path('document_appearance/defaults/', document_appearance_defaults, name='document_appearance_defaults'),
    path('document_appearance/templates/', document_template_choices, name='document_template_choices'),
    path('document_appearance/presets/', document_template_presets, name='document_template_presets'),
    path('document_appearance/colors/', color_presets, name='color_presets'),
    
    # Endpoint de santé
    path('health/', health_check, name='health_check'),
]
