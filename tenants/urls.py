from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, validate_tenant, health_check, current_tenant_info,
    preview_document_number, increment_document_counter, 
    reset_document_counter, get_document_numbering_config,
    manage_document_numbering_config, tenant_vat_rates, tenant_payment_terms,
    tenant_setup_progress, retry_tenant_setup
)
from .views_document_appearance import (
    tenant_document_appearance, document_appearance_defaults,
    document_template_choices, document_template_presets, color_presets,
    logo_position_choices, table_style_choices
)
from .views_payment_methods import (
    tenant_payment_methods, tenant_payment_method_detail,
    payment_method_types, create_default_payment_methods
)

app_name = 'tenants'

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    # Endpoints spéciaux pour les autres services (AVANT le router)
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
    path('tenants/document_numbering/<int:numbering_id>/increment/', increment_document_counter, name='increment_document_counter'),
    path('tenants/document_numbering/<int:numbering_id>/reset/', reset_document_counter, name='reset_document_counter'),
    path('tenants/document_numbering/<str:document_type>/', get_document_numbering_config, name='get_document_numbering_config'),
    path('tenants/document_numbering/', manage_document_numbering_config, name='manage_document_numbering_config'),
    
    # Endpoints pour l'apparence des documents
    path('tenants/document_appearance/', tenant_document_appearance, name='tenant_document_appearance'),
    path('document_appearance/', tenant_document_appearance, name='tenant_document_appearance_alt'),
    path('document_appearance/defaults/', document_appearance_defaults, name='document_appearance_defaults'),
    path('document_appearance/templates/', document_template_choices, name='document_template_choices'),
    path('document_appearance/presets/', document_template_presets, name='document_template_presets'),
    path('document_appearance/colors/', color_presets, name='color_presets'),
    path('document_appearance/logo_positions/', logo_position_choices, name='logo_position_choices'),
    path('document_appearance/table_styles/', table_style_choices, name='table_style_choices'),
    
    # Endpoints pour les moyens de paiement
    path('payment_methods/', tenant_payment_methods, name='tenant_payment_methods'),
    path('payment_methods/<int:payment_method_id>/', tenant_payment_method_detail, name='tenant_payment_method_detail'),
    path('payment_methods/types/', payment_method_types, name='payment_method_types'),
    path('payment_methods/create_defaults/', create_default_payment_methods, name='create_default_payment_methods'),
    
    # Endpoints pour le suivi de création des schémas
    path('tenants/setup-progress/', tenant_setup_progress, name='tenant_setup_progress'),
    path('tenants/retry-setup/', retry_tenant_setup, name='retry_tenant_setup'),
    path('setup-progress/', tenant_setup_progress, name='tenant_setup_progress_alt'),
    path('retry-setup/', retry_tenant_setup, name='retry_tenant_setup_alt'),
    
    # Endpoint de santé
    path('health/', health_check, name='health_check'),
    
    # Routes du router (CRUD des tenants) - APRÈS les endpoints spécialisés
    path('', include(router.urls)),
]
