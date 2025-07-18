from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import (
    Tenant, TenantSettings, TenantInvitation, TenantUsage,
    TenantBankInfo, TenantVatRate, TenantPaymentTerm,
    TenantDocumentNumbering, TenantDocumentAppearance
)
from .serializers import (
    TenantCreateSerializer, TenantListSerializer, TenantDetailSerializer, TenantUpdateSerializer,
    TenantSettingsSerializer, TenantInvitationSerializer, TenantInvitationCreateSerializer,
    TenantUsageSerializer, TenantStatsSerializer, TenantValidationSerializer,
    TenantBankInfoSerializer, TenantVatRateSerializer, TenantPaymentTermSerializer,
    TenantDocumentNumberingSerializer, TenantDocumentAppearanceSerializer
)
from django.utils import timezone

class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal pour la gestion des tenants (CRUD)
    """
    queryset = Tenant.objects.all()
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TenantListSerializer
        elif self.action == 'retrieve':
            return TenantDetailSerializer
        elif self.action == 'create':
            return TenantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TenantUpdateSerializer
        elif self.action == 'current_tenant_info':
            return TenantDetailSerializer
        return TenantListSerializer
        
    @action(detail=False, methods=['get', 'put', 'patch'], url_path='current_tenant_info')
    def current_tenant_info(self, request):
        """
        Endpoint pour récupérer et mettre à jour les informations du tenant actuel
        Utilisé par le frontend pour afficher et modifier les informations de l'entreprise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log détaillé pour le débogage
        logger.info(f"Appel à current_tenant_info - Méthode: {request.method} - Headers: {request.headers}")
        logger.info(f"Appel à current_tenant_info - URL: {request.path}")
        
        tenant_id = request.headers.get('X-Tenant-ID')
        if not tenant_id:
            return Response(
                {"detail": "X-Tenant-ID header is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            
            # Traiter les requêtes PUT ou PATCH pour mettre à jour le tenant
            if request.method in ['PUT', 'PATCH']:
                # Vérifier les droits d'administration (pourrait être implémenté avec un système de rôles)
                # Pour l'instant, nous permettons à tout utilisateur authentifié de modifier son tenant
                
                # Utiliser le serializer approprié pour la mise à jour
                serializer = self.get_serializer(tenant, data=request.data, partial=request.method=='PATCH')
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                
                # Mettre à jour les paramètres du tenant si présents
                if 'settings' in request.data and isinstance(request.data['settings'], dict):
                    settings_data = request.data['settings']
                    try:
                        tenant_settings = tenant.settings
                    except TenantSettings.DoesNotExist:
                        tenant_settings = TenantSettings.objects.create(tenant=tenant)
                        
                    # Mettre à jour les champs des paramètres
                    settings_serializer = TenantSettingsSerializer(tenant_settings, data=settings_data, partial=True)
                    if settings_serializer.is_valid():
                        settings_serializer.save()
                
                # Mettre à jour les informations bancaires si présentes
                if 'bank_info' in request.data and isinstance(request.data['bank_info'], dict):
                    bank_data = request.data['bank_info']
                    try:
                        bank_info = tenant.bank_info
                    except TenantBankInfo.DoesNotExist:
                        bank_info = TenantBankInfo.objects.create(tenant=tenant)
                        
                    # Mettre à jour les champs bancaires
                    bank_serializer = TenantBankInfoSerializer(bank_info, data=bank_data, partial=True)
                    if bank_serializer.is_valid():
                        bank_serializer.save()
                
                # Mettre à jour l'apparence des documents si présente
                if 'document_appearance' in request.data and isinstance(request.data['document_appearance'], dict):
                    appearance_data = request.data['document_appearance']
                    try:
                        document_appearance = tenant.document_appearance
                    except TenantDocumentAppearance.DoesNotExist:
                        document_appearance = TenantDocumentAppearance.objects.create(tenant=tenant)
                        
                    # Mettre à jour les champs d'apparence
                    appearance_serializer = TenantDocumentAppearanceSerializer(document_appearance, data=appearance_data, partial=True)
                    if appearance_serializer.is_valid():
                        appearance_serializer.save()
                
                # Mettre à jour la numérotation des documents si présente
                if 'document_numbering' in request.data and isinstance(request.data['document_numbering'], list):
                    from .models import TenantDocumentNumbering
                    from .serializers import TenantDocumentNumberingSerializer
                    
                    # Supprimer les configurations existantes pour ce tenant
                    # pour éviter les doublons et simplifier la gestion
                    TenantDocumentNumbering.objects.filter(tenant=tenant).delete()
                    
                    # Créer les nouvelles configurations
                    for numbering_data in request.data['document_numbering']:
                        numbering_data['tenant'] = tenant.id
                        serializer = TenantDocumentNumberingSerializer(data=numbering_data)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            logger.warning(f"Données de numérotation invalides: {serializer.errors}")
                
                logger.info(f"Mise à jour réussie du tenant {tenant_id}")
            
            # Pour GET et après les mises à jour, récupérer les informations complètes
            serializer = TenantDetailSerializer(tenant)
            return Response(serializer.data)
            
        except Tenant.DoesNotExist:
            return Response(
                {"detail": f"Tenant with id {tenant_id} not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors du traitement de current_tenant_info: {str(e)}")
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """Créer un tenant et retourner sa représentation complète"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()
        
        # Utiliser TenantDetailSerializer pour la réponse
        response_serializer = TenantDetailSerializer(tenant)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def tenant_settings(self, request, pk=None):
        tenant = self.get_object()
        serializer = TenantSettingsSerializer(tenant.settings)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        tenant = self.get_object()
        usage = TenantUsage.objects.filter(tenant=tenant).order_by('-date')
        serializer = TenantUsageSerializer(usage, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invitations(self, request, pk=None):
        tenant = self.get_object()
        invitations = TenantInvitation.objects.filter(tenant=tenant)
        serializer = TenantInvitationSerializer(invitations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        tenant = self.get_object()
        serializer = TenantInvitationCreateSerializer(
            data=request.data,
            context={'tenant': tenant, 'invited_by': request.data.get('invited_by')}
        )
        if serializer.is_valid():
            invitation = serializer.save()
            return Response(TenantInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def validate_tenant(request, tenant_id):
    """
    Endpoint pour valider l'existence d'un tenant (utilisé par auth-service)
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        data = {
            'tenant_id': str(tenant.id),
            'exists': True,
            'is_active': tenant.is_active,
            'name': tenant.name
        }
    except Tenant.DoesNotExist:
        data = {
            'tenant_id': tenant_id,
            'exists': False,
            'is_active': False,
            'name': None
        }
    return Response(data)

@api_view(['GET', 'PATCH', 'PUT'])
@permission_classes([permissions.AllowAny])
def current_tenant_info(request):
    """
    Endpoint pour récupérer et mettre à jour les informations du tenant actuel
    Utilisé par le frontend pour afficher et modifier les informations de l'entreprise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log détaillé pour le débogage
    logger.info(f"Appel à current_tenant_info - Méthode: {request.method} - Headers: {request.headers}")
    logger.info(f"Appel à current_tenant_info - URL: {request.path}")
    
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        # Traiter les requêtes PATCH ou PUT pour mettre à jour le tenant
        if request.method in ['PATCH', 'PUT']:
            # Vérifier les droits d'administration (pourrait être implémenté avec un système de rôles)
            # Pour l'instant, nous permettons à tout utilisateur authentifié de modifier son tenant
            
            # Mettre à jour les champs de base du tenant
            data = request.data
            
            # Champs de base
            if 'name' in data:
                tenant.name = data['name']
            if 'email' in data:
                tenant.email = data['email']
            if 'phone' in data:
                tenant.phone = data['phone']
            if 'website' in data:
                tenant.website = data['website']
                
            # Champs d'adresse
            if 'address_line_1' in data:
                tenant.address_line_1 = data['address_line_1']
            if 'address_line_2' in data:
                tenant.address_line_2 = data['address_line_2']
            if 'city' in data:
                tenant.city = data['city']
            if 'postal_code' in data:
                tenant.postal_code = data['postal_code']
            if 'country' in data:
                tenant.country = data['country']
                
            # Champs légaux
            if 'siret' in data:
                tenant.siret = data['siret']
            if 'vat_number' in data:
                tenant.vat_number = data['vat_number']
            if 'legal_form' in data:
                tenant.legal_form = data['legal_form']
                
            # Sauvegarder les modifications du tenant
            tenant.save()
            
            # Mettre à jour les paramètres du tenant si présents
            if 'settings' in data and isinstance(data['settings'], dict):
                settings_data = data['settings']
                try:
                    tenant_settings = tenant.settings
                except TenantSettings.DoesNotExist:
                    tenant_settings = TenantSettings.objects.create(tenant=tenant)
                    
                # Mettre à jour les champs des paramètres
                if 'logo_url' in settings_data:
                    tenant_settings.logo_url = settings_data['logo_url']
                if 'logo_base64' in settings_data:
                    tenant_settings.logo_base64 = settings_data['logo_base64']
                if 'primary_color' in settings_data:
                    tenant_settings.primary_color = settings_data['primary_color']
                if 'secondary_color' in settings_data:
                    tenant_settings.secondary_color = settings_data['secondary_color']
                if 'accent_color' in settings_data:
                    tenant_settings.accent_color = settings_data['accent_color']
                if 'timezone' in settings_data:
                    tenant_settings.timezone = settings_data['timezone']
                if 'language' in settings_data:
                    tenant_settings.language = settings_data['language']
                if 'currency' in settings_data:
                    tenant_settings.currency = settings_data['currency']
                if 'date_format' in settings_data:
                    tenant_settings.date_format = settings_data['date_format']
                    
                # Notifications
                if 'email_notifications_enabled' in settings_data:
                    tenant_settings.email_notifications_enabled = settings_data['email_notifications_enabled']
                if 'sms_notifications_enabled' in settings_data:
                    tenant_settings.sms_notifications_enabled = settings_data['sms_notifications_enabled']
                if 'push_notifications_enabled' in settings_data:
                    tenant_settings.push_notifications_enabled = settings_data['push_notifications_enabled']
                    
                # Sécurité
                if 'two_factor_required' in settings_data:
                    tenant_settings.two_factor_required = settings_data['two_factor_required']
                if 'password_expiry_days' in settings_data:
                    tenant_settings.password_expiry_days = settings_data['password_expiry_days']
                if 'session_timeout_minutes' in settings_data:
                    tenant_settings.session_timeout_minutes = settings_data['session_timeout_minutes']
                    
                # Sauvegarder les modifications des paramètres
                tenant_settings.save()
                
            # Mettre à jour les informations bancaires si présentes
            if 'bank_info' in data and isinstance(data['bank_info'], dict):
                bank_data = data['bank_info']
                try:
                    bank_info = tenant.bank_info
                except TenantBankInfo.DoesNotExist:
                    bank_info = TenantBankInfo.objects.create(tenant=tenant)
                    
                # Mettre à jour les champs bancaires
                if 'bank_name' in bank_data:
                    bank_info.bank_name = bank_data['bank_name']
                if 'iban' in bank_data:
                    bank_info.iban = bank_data['iban']
                if 'bic' in bank_data:
                    bank_info.bic = bank_data['bic']
                if 'account_owner' in bank_data:
                    bank_info.account_owner = bank_data['account_owner']
                    
                # Sauvegarder les modifications des informations bancaires
                bank_info.save()
                
            # Mettre à jour l'apparence des documents si présente
            if 'document_appearance' in data and isinstance(data['document_appearance'], dict):
                appearance_data = data['document_appearance']
                try:
                    document_appearance = tenant.document_appearance
                except TenantDocumentAppearance.DoesNotExist:
                    document_appearance = TenantDocumentAppearance.objects.create(tenant=tenant)
                    
                # Mettre à jour les champs d'apparence
                for field, value in appearance_data.items():
                    if hasattr(document_appearance, field):
                        setattr(document_appearance, field, value)
                        
                # Sauvegarder les modifications d'apparence
                document_appearance.save()
                
            logger.info(f"Mise à jour réussie du tenant {tenant_id}")
            
            # Continuer avec la logique de récupération pour renvoyer les données mises à jour
        
        # Récupérer les paramètres du tenant et créer par défaut si inexistants
        try:
            tenant_settings = tenant.settings
        except TenantSettings.DoesNotExist:
            tenant_settings = TenantSettings.objects.create(tenant=tenant)
        
        # Récupérer les informations bancaires ou créer par défaut
        try:
            bank_info = tenant.bank_info
        except TenantBankInfo.DoesNotExist:
            bank_info = TenantBankInfo.objects.create(tenant=tenant)
            
        # Récupérer l'apparence des documents ou créer par défaut
        try:
            document_appearance = tenant.document_appearance
        except TenantDocumentAppearance.DoesNotExist:
            document_appearance = TenantDocumentAppearance.objects.create(tenant=tenant)
            
        # Récupérer les taux de TVA personnalisés
        vat_rates = tenant.vat_rates.all()
        
        # Récupérer les conditions de paiement
        payment_terms = tenant.payment_terms.all()
        
        # Récupérer les configurations de numérotation
        document_numbering = tenant.document_numbering.all()
        
        # Construire la réponse avec toutes les informations nécessaires
        response_data = {
            # Informations de base
            'id': str(tenant.id),
            'name': tenant.name,
            'email': tenant.email,
            'phone': tenant.phone,
            'website': tenant.website,
            
            # Adresse
            'address': {
                'line1': tenant.address_line_1,
                'line2': tenant.address_line_2,
                'city': tenant.city,
                'postal_code': tenant.postal_code,
                'country': tenant.country,
                'full_address': tenant.full_address
            },
            
            # Informations légales
            'legal': {
                'siret': tenant.siret,
                'vat_number': tenant.vat_number,
                'legal_form': tenant.legal_form
            },
            
            # Paramètres visuels et généraux
            'settings': {
                'logo_url': tenant_settings.logo_url,
                'logo_base64': tenant_settings.logo_base64,
                'primary_color': tenant_settings.primary_color,
                'secondary_color': tenant_settings.secondary_color,
                'accent_color': tenant_settings.accent_color,
                'timezone': tenant_settings.timezone,
                'language': tenant_settings.language,
                'currency': tenant_settings.currency,
                'date_format': tenant_settings.date_format,
                'notifications': {
                    'email_enabled': tenant_settings.email_notifications_enabled,
                    'sms_enabled': tenant_settings.sms_notifications_enabled,
                    'push_enabled': tenant_settings.push_notifications_enabled
                },
                'security': {
                    'two_factor_required': tenant_settings.two_factor_required,
                    'password_expiry_days': tenant_settings.password_expiry_days,
                    'session_timeout_minutes': tenant_settings.session_timeout_minutes
                }
            },
            
            # Informations bancaires
            'bank_info': {
                'bank_name': bank_info.bank_name,
                'iban': bank_info.iban,
                'bic': bank_info.bic,
                'account_owner': bank_info.account_owner
            },
            
            # Taux de TVA personnalisés
            'vat_rates': []
        }
        
        # Ajouter les taux de TVA par défaut si aucun taux personnalisé
        if not vat_rates.exists():
            response_data['vat_rates'] = [
                {
                    'code': "0", 
                    'name': "0%", 
                    'rate': 0.0,
                    'rate_display': "0%",
                    'description': "Taux de TVA à 0%",
                    'is_default': False,
                    'is_active': True
                },
                {
                    'code': "5.5", 
                    'name': "5.5%", 
                    'rate': 5.5,
                    'rate_display': "5.5%",
                    'description': "Taux de TVA à 5.5%",
                    'is_default': False,
                    'is_active': True
                },
                {
                    'code': "10", 
                    'name': "10%", 
                    'rate': 10.0,
                    'rate_display': "10%",
                    'description': "Taux de TVA à 10%",
                    'is_default': False,
                    'is_active': True
                },
                {
                    'code': "20", 
                    'name': "20%", 
                    'rate': 20.0,
                    'rate_display': "20%",
                    'description': "Taux de TVA à 20%",
                    'is_default': True,
                    'is_active': True
                }
            ]
        else:
            # Utiliser les taux personnalisés
            for vat_rate in vat_rates:
                response_data['vat_rates'].append({
                    'id': str(vat_rate.id),
                    'code': vat_rate.code,
                    'name': vat_rate.name,
                    'rate': vat_rate.rate,
                    'rate_display': f"{vat_rate.rate}%",
                    'description': vat_rate.description,
                    'is_default': vat_rate.is_default,
                    'is_active': vat_rate.is_active
                })
        
        # Ajouter les conditions de paiement
        response_data['payment_terms'] = []
        for term in payment_terms:
            response_data['payment_terms'].append({
                'id': str(term.id),
                'label': term.label,
                'days': term.days,
                'description': term.description,
                'is_default': term.is_default,
                'is_active': term.is_active
            })
        
        # Ajouter la numérotation des documents
        response_data['document_numbering'] = []
        for numbering in document_numbering:
            response_data['document_numbering'].append({
                'id': str(numbering.id),
                'document_type': numbering.document_type,
                'document_type_display': numbering.get_document_type_display(),
                'prefix': numbering.prefix,
                'suffix': numbering.suffix,
                'padding': numbering.padding,
                'next_number': numbering.next_number,
                'include_year': numbering.include_year,
                'include_month': numbering.include_month,
                'reset_yearly': numbering.reset_yearly,
                'reset_monthly': numbering.reset_monthly
            })
        
        # Ajouter l'apparence des documents
        response_data['document_appearance'] = {
            'header_text': document_appearance.header_text,
            'footer_text': document_appearance.footer_text,
            'show_logo': document_appearance.show_logo,
            'logo_position': document_appearance.logo_position,
            'logo_position_display': document_appearance.get_logo_position_display(),
            'font_family': document_appearance.font_family,
            'font_size': document_appearance.font_size,
            'line_spacing': document_appearance.line_spacing,
            'margin_top': document_appearance.margin_top,
            'margin_right': document_appearance.margin_right,
            'margin_bottom': document_appearance.margin_bottom,
            'margin_left': document_appearance.margin_left,
            'show_payment_details': document_appearance.show_payment_details,
            'show_legal_mentions': document_appearance.show_legal_mentions,
            'legal_mentions': document_appearance.legal_mentions,
            'table_header_color': document_appearance.table_header_color,
            'table_alternate_color': document_appearance.table_alternate_color
        }
        
        return Response(response_data)
        
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant with id {tenant_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Endpoint de santé du service tenant"""
    return Response({
        "service": "tenant-service",
        "status": "healthy",
        "version": "1.0.0"
    })
