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
                        serializer = TenantDocumentNumberingSerializer(data=numbering_data)
                        if serializer.is_valid():
                            serializer.save(tenant=tenant)
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
            logger.info(f"🔍 DÉBUT DEBUG - Données reçues dans la requête:")
            logger.info(f"🔍 Clés disponibles: {list(data.keys())}")
            logger.info(f"🔍 Taille totale des données: {len(str(data))} caractères")
            
            # Debug spécifique pour vat_rates
            if 'vat_rates' in data:
                logger.info(f"🔍 ✅ VAT_RATES TROUVÉ!")
                logger.info(f"🔍 Type de vat_rates: {type(data['vat_rates'])}")
                logger.info(f"🔍 Contenu vat_rates: {data['vat_rates']}")
                logger.info(f"🔍 Nombre d'éléments vat_rates: {len(data['vat_rates']) if isinstance(data['vat_rates'], list) else 'N/A'}")
            else:
                logger.info(f"🔍 ❌ VAT_RATES PAS TROUVÉ!")
                logger.info(f"🔍 Toutes les clés: {list(data.keys())}")
                
            # Log de toutes les données pour debug complet
            for key, value in data.items():
                if key != 'vat_rates':  # On évite de logger 2 fois vat_rates
                    logger.info(f"🔍 {key}: {type(value)} - {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
            
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
            if 'ice' in data:
                tenant.ice = data['ice']
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
                    logo_data = settings_data['logo_base64']
                    logger.info(f"🖼️ Logo reçu: {len(logo_data) if logo_data else 0} caractères")
                    tenant_settings.logo_data = logo_data
                    logger.info(f"🖼️ Logo sauvegardé en DB")
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
            
            # Mettre à jour les taux de TVA si présents
            logger.info(f"🔧 DÉBUT TRAITEMENT VAT_RATES")
            logger.info(f"🔧 'vat_rates' in data: {'vat_rates' in data}")
            logger.info(f"🔧 Type de data['vat_rates']: {type(data.get('vat_rates', 'NON_TROUVE'))}")
            if 'vat_rates' in data:
                logger.info(f"🔧 Contenu vat_rates: {data['vat_rates']}")
                logger.info(f"🔧 isinstance list: {isinstance(data['vat_rates'], list)}")
            
            if 'vat_rates' in data and isinstance(data['vat_rates'], list):
                logger.info(f"🔧 ✅ CONDITION REMPLIE - Processing vat_rates with {len(data['vat_rates'])} items")
                
                from django.db import transaction
                
                try:
                    with transaction.atomic():
                        # Supprimer les taux de TVA existants pour ce tenant
                        deleted_count = TenantVatRate.objects.filter(tenant=tenant).count()
                        TenantVatRate.objects.filter(tenant=tenant).delete()
                        logger.info(f"Deleted {deleted_count} existing VAT rates")
                        
                        # Créer les nouveaux taux de TVA
                        for i, vat_rate_data in enumerate(data['vat_rates']):
                            logger.info(f"Creating VAT rate {i+1}: {vat_rate_data}")
                            
                            # S'assurer qu'un seul taux est défini par défaut
                            is_default = vat_rate_data.get('is_default', False)
                            
                            # Créer le nouveau taux de TVA
                            vat_rate = TenantVatRate.objects.create(
                                tenant=tenant,
                                code=vat_rate_data.get('code', ''),
                                name=vat_rate_data.get('name', ''),
                                rate=vat_rate_data.get('rate', 0),
                                description=vat_rate_data.get('description', ''),
                                is_default=is_default,
                                is_active=vat_rate_data.get('is_active', True)
                            )
                            logger.info(f"✅ Created VAT rate with ID: {vat_rate.id}, tenant_id: {vat_rate.tenant_id}")
                        
                        # S'assurer qu'un seul taux est défini par défaut après création
                        default_rates = TenantVatRate.objects.filter(tenant=tenant, is_default=True)
                        if default_rates.count() > 1:
                            # Garder seulement le premier comme défaut
                            first_default = default_rates.first()
                            default_rates.exclude(id=first_default.id).update(is_default=False)
                            logger.info(f"Kept only one default VAT rate: {first_default.code}")
                        elif default_rates.count() == 0:
                            # S'il n'y a pas de taux par défaut, définir le premier comme défaut
                            first_rate = TenantVatRate.objects.filter(tenant=tenant).first()
                            if first_rate:
                                first_rate.is_default = True
                                first_rate.save()
                                logger.info(f"Set first VAT rate as default: {first_rate.code}")
                        
                        logger.info(f"Taux de TVA mis à jour pour le tenant {tenant_id} - Transaction commitée")
                        
                except Exception as vat_error:
                    logger.error(f"❌ Erreur lors de la mise à jour des taux de TVA: {str(vat_error)}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    # La transaction sera automatiquement rollback
            
            # Mettre à jour la numérotation des documents si présente
            logger.info(f"Données reçues: {data.keys()}")
            logger.info(f"Tenant ID: {tenant_id}, Tenant object ID: {tenant.id}")
            
            if 'document_numbering' in data and isinstance(data['document_numbering'], list):
                logger.info(f"Processing document_numbering with {len(data['document_numbering'])} items")
                
                # Supprimer les configurations existantes pour ce tenant
                deleted_count = TenantDocumentNumbering.objects.filter(tenant=tenant).count()
                TenantDocumentNumbering.objects.filter(tenant=tenant).delete()
                logger.info(f"Deleted {deleted_count} existing numbering configurations")
                
                # Créer les nouvelles configurations
                for i, numbering_data in enumerate(data['document_numbering']):
                    logger.info(f"Creating numbering config {i+1}: {numbering_data}")
                    
                    # Créer la nouvelle configuration avec le tenant
                    numbering = TenantDocumentNumbering.objects.create(
                        tenant=tenant,
                        document_type=numbering_data.get('document_type'),
                        prefix=numbering_data.get('prefix', ''),
                        suffix=numbering_data.get('suffix', ''),
                        next_number=numbering_data.get('next_number', 1),
                        padding=numbering_data.get('padding', 3),
                        include_year=numbering_data.get('include_year', True),
                        include_month=numbering_data.get('include_month', False),
                        include_day=numbering_data.get('include_day', False),
                        date_format=numbering_data.get('date_format', 'YYYY-MM-DD'),
                        separator=numbering_data.get('separator', '-'),
                        custom_format=numbering_data.get('custom_format', ''),
                        reset_yearly=numbering_data.get('reset_yearly', True),
                        reset_monthly=numbering_data.get('reset_monthly', False)
                    )
                    logger.info(f"Created numbering config with ID: {numbering.id}, tenant_id: {numbering.tenant_id}")
                
                logger.info(f"Configurations de numérotation mises à jour pour le tenant {tenant_id}")
            else:
                logger.info(f"No document_numbering found in data or not a list")
                
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
        
        # Log pour débugger le logo renvoyé
        logger.info(f"🔍 Logo renvoyé au frontend: {len(tenant_settings.logo_data) if tenant_settings.logo_data else 0} caractères")
        
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
                'ice': tenant.ice,
                'legal_form': tenant.legal_form
            },
            
            # Paramètres visuels et généraux
            'settings': {
                'logo_url': tenant_settings.logo_url,
                'logo_data': tenant_settings.logo_data,
                'primary_color': tenant_settings.primary_color,
                'secondary_color': tenant_settings.secondary_color,
                'accent_color': tenant_settings.accent_color,
                'timezone': tenant_settings.timezone,
                'language': tenant_settings.language,
                'currency': tenant_settings.currency,
                'date_format': tenant_settings.date_format,
                'notifications': {
                    'email_enabled': tenant_settings.email_notifications,
                    'sms_enabled': tenant_settings.sms_notifications,
                    'push_enabled': tenant_settings.push_notifications
                },
                'security': {
                    'two_factor_required': tenant_settings.require_2fa,
                    'password_expiry_days': tenant_settings.password_expiry_days,
                    'session_timeout_minutes': tenant_settings.session_timeout_minutes
                }
            },
            
            # Informations bancaires
            'bank_info': {
                'bank_name': bank_info.bank_name,
                'iban': bank_info.iban,
                'bic': bank_info.bic,
                'account_owner': ''  # Champ pas encore implémenté dans le modèle
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
                'include_day': numbering.include_day,
                'date_format': numbering.date_format,
                'separator': numbering.separator,
                'custom_format': numbering.custom_format,
                'reset_yearly': numbering.reset_yearly,
                'reset_monthly': numbering.reset_monthly,
                'format_description': numbering.get_format_description(),
                'preview': numbering.preview_next_number(),
                'created_at': numbering.created_at,
                'updated_at': numbering.updated_at
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

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def preview_document_number(request):
    """
    Aperçu de numérotation sans sauvegarder
    POST /api/tenants/preview-numbering/
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response({'error': 'X-Tenant-ID header requis'}, status=400)
    
    try:
        # Créer un objet temporaire pour l'aperçu
        temp_numbering = TenantDocumentNumbering(
            document_type=request.data.get('document_type', 'quote'),
            prefix=request.data.get('prefix', ''),
            suffix=request.data.get('suffix', ''),
            next_number=request.data.get('next_number', 1),
            padding=request.data.get('padding', 3),
            include_year=request.data.get('include_year', True),
            include_month=request.data.get('include_month', False),
            include_day=request.data.get('include_day', False),
            date_format=request.data.get('date_format', 'YYYY-MM-DD'),
            separator=request.data.get('separator', '-'),
            custom_format=request.data.get('custom_format', ''),
            reset_yearly=request.data.get('reset_yearly', True),
            reset_monthly=request.data.get('reset_monthly', False)
        )
        
        preview = temp_numbering.preview_next_number()
        format_description = temp_numbering.get_format_description()
        
        return Response({
            'preview': preview,
            'format_description': format_description,
            'config': request.data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['PATCH'])
@permission_classes([permissions.AllowAny])
def increment_document_counter(request, numbering_id):
    """
    Incrémente le compteur d'un document numbering
    PATCH /api/tenants/document_numbering/{id}/increment/
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response({'error': 'X-Tenant-ID header requis'}, status=400)
    
    try:
        numbering = TenantDocumentNumbering.objects.get(
            id=numbering_id,
            tenant_id=tenant_id
        )
        
        old_counter = numbering.increment_counter()
        
        return Response({
            'old_counter': old_counter,
            'new_counter': numbering.next_number,
            'message': 'Compteur incrémenté avec succès'
        })
        
    except TenantDocumentNumbering.DoesNotExist:
        return Response(
            {'error': 'Configuration de numérotation non trouvée'}, 
            status=404
        )
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_document_counter(request, numbering_id):
    """
    Remet à zéro le compteur d'un document numbering
    POST /api/tenants/document_numbering/{id}/reset/
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response({'error': 'X-Tenant-ID header requis'}, status=400)
    
    try:
        numbering = TenantDocumentNumbering.objects.get(
            id=numbering_id,
            tenant_id=tenant_id
        )
        
        new_value = request.data.get('new_value', 1)
        if not isinstance(new_value, int) or new_value < 1:
            return Response({'error': 'new_value doit être un entier >= 1'}, status=400)
        
        numbering.reset_counter(new_value)
        
        return Response({
            'new_counter': numbering.next_number,
            'message': f'Compteur remis à {new_value}'
        })
        
    except TenantDocumentNumbering.DoesNotExist:
        return Response(
            {'error': 'Configuration de numérotation non trouvée'}, 
            status=404
        )
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_document_numbering_config(request, document_type):
    """
    Récupère la configuration de numérotation pour un type de document
    GET /api/tenants/document_numbering/{document_type}/
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response({'error': 'X-Tenant-ID header requis'}, status=400)
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        try:
            numbering = TenantDocumentNumbering.objects.get(
                tenant=tenant,
                document_type=document_type
            )
            
            # Sérialiser la configuration
            config_data = {
                'id': str(numbering.id),
                'document_type': numbering.document_type,
                'document_type_display': numbering.get_document_type_display(),
                'prefix': numbering.prefix,
                'suffix': numbering.suffix,
                'next_number': numbering.next_number,
                'padding': numbering.padding,
                'include_year': numbering.include_year,
                'include_month': numbering.include_month,
                'include_day': numbering.include_day,
                'date_format': numbering.date_format,
                'separator': numbering.separator,
                'custom_format': numbering.custom_format,
                'reset_yearly': numbering.reset_yearly,
                'reset_monthly': numbering.reset_monthly,
                'format_description': numbering.get_format_description(),
                'preview': numbering.preview_next_number(),
                'created_at': numbering.created_at,
                'updated_at': numbering.updated_at
            }
            
            return Response(config_data)
            
        except TenantDocumentNumbering.DoesNotExist:
            # Créer une configuration par défaut
            defaults = {
                'quote': {'prefix': 'DEV', 'padding': 3},
                'invoice': {'prefix': 'FAC', 'padding': 3},
                'credit_note': {'prefix': 'AV', 'padding': 3}
            }
            
            config = defaults.get(document_type, {'prefix': 'DOC', 'padding': 3})
            
            numbering = TenantDocumentNumbering.objects.create(
                tenant=tenant,
                document_type=document_type,
                **config,
                include_year=True,
                include_month=False,
                include_day=False,
                separator='-'
            )
            
            config_data = {
                'id': str(numbering.id),
                'document_type': numbering.document_type,
                'document_type_display': numbering.get_document_type_display(),
                'prefix': numbering.prefix,
                'suffix': numbering.suffix,
                'next_number': numbering.next_number,
                'padding': numbering.padding,
                'include_year': numbering.include_year,
                'include_month': numbering.include_month,
                'include_day': numbering.include_day,
                'date_format': numbering.date_format,
                'separator': numbering.separator,
                'custom_format': numbering.custom_format,
                'reset_yearly': numbering.reset_yearly,
                'reset_monthly': numbering.reset_monthly,
                'format_description': numbering.get_format_description(),
                'preview': numbering.preview_next_number(),
                'created_at': numbering.created_at,
                'updated_at': numbering.updated_at
            }
            
            return Response(config_data, status=201)
        
    except Tenant.DoesNotExist:
        return Response(
            {'error': f'Tenant {tenant_id} non trouvé'}, 
            status=404
        )
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST', 'PUT', 'PATCH'])
@permission_classes([permissions.AllowAny])
def manage_document_numbering_config(request):
    """
    Endpoint pour créer/modifier les configurations de numérotation
    POST /api/tenants/document_numbering/
    PUT/PATCH /api/tenants/document_numbering/
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response({'error': 'X-Tenant-ID header requis'}, status=400)
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        if request.method == 'POST':
            # Créer une nouvelle configuration
            document_type = request.data.get('document_type')
            if not document_type:
                return Response({'error': 'document_type requis'}, status=400)
            
            # Vérifier si la configuration existe déjà
            existing_config = TenantDocumentNumbering.objects.filter(
                tenant=tenant,
                document_type=document_type
            ).first()
            
            if existing_config:
                # Mettre à jour la configuration existante
                serializer = TenantDocumentNumberingSerializer(
                    existing_config, 
                    data=request.data, 
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=200)
                return Response(serializer.errors, status=400)
            else:
                # Créer une nouvelle configuration
                data = request.data.copy()
                data['tenant'] = tenant.id
                serializer = TenantDocumentNumberingSerializer(data=data)
                if serializer.is_valid():
                    serializer.save(tenant=tenant)
                    return Response(serializer.data, status=201)
                return Response(serializer.errors, status=400)
                
        elif request.method in ['PUT', 'PATCH']:
            # Mettre à jour les configurations existantes (bulk update)
            document_numbering_list = request.data.get('document_numbering', [])
            if not document_numbering_list:
                return Response({'error': 'document_numbering list requis'}, status=400)
            
            updated_configs = []
            for config_data in document_numbering_list:
                document_type = config_data.get('document_type')
                if not document_type:
                    continue
                    
                numbering, created = TenantDocumentNumbering.objects.get_or_create(
                    tenant=tenant,
                    document_type=document_type,
                    defaults={
                        'prefix': config_data.get('prefix', 'DOC'),
                        'padding': config_data.get('padding', 3),
                        'include_year': config_data.get('include_year', True),
                        'include_month': config_data.get('include_month', False),
                        'include_day': config_data.get('include_day', False),
                        'separator': config_data.get('separator', '-'),
                    }
                )
                
                # Mettre à jour avec les nouvelles données
                serializer = TenantDocumentNumberingSerializer(
                    numbering, 
                    data=config_data, 
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    updated_configs.append(serializer.data)
            
            return Response({
                'message': f'{len(updated_configs)} configurations mises à jour',
                'configurations': updated_configs
            }, status=200)
            
    except Tenant.DoesNotExist:
        return Response(
            {'error': f'Tenant {tenant_id} non trouvé'}, 
            status=404
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur gestion configuration numérotation: {e}")
        return Response({'error': str(e)}, status=500)


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.AllowAny])
def tenant_vat_rates(request):
    """
    Endpoint spécifique pour gérer les taux de TVA d'un tenant
    GET: Récupérer les taux de TVA
    POST: Créer un nouveau taux de TVA
    PUT/PATCH: Mettre à jour les taux de TVA existants
    DELETE: Supprimer un taux de TVA
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log détaillé pour le débogage
    logger.info(f"Appel à tenant_vat_rates - Méthode: {request.method} - Headers: {request.headers}")
    logger.info(f"Appel à tenant_vat_rates - URL: {request.path}")
    if request.body:
        logger.info(f"Contenu de la requête: {request.body.decode('utf-8')}")
    
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        # GET: Récupérer les taux de TVA
        if request.method == 'GET':
            vat_rates = tenant.vat_rates.all()
            response_data = []
            
            for vat_rate in vat_rates:
                response_data.append({
                    'id': str(vat_rate.id),
                    'code': vat_rate.code,
                    'name': vat_rate.name,
                    'rate': vat_rate.rate,
                    'rate_display': f"{vat_rate.rate}%",
                    'description': vat_rate.description,
                    'is_default': vat_rate.is_default,
                    'is_active': vat_rate.is_active
                })
            
            return Response(response_data)
        
        # POST: Créer un nouveau taux de TVA
        elif request.method == 'POST':
            data = request.data
            
            # Vérifier si un taux avec le même code existe déjà
            if TenantVatRate.objects.filter(tenant=tenant, code=data.get('code', '')).exists():
                return Response(
                    {"detail": f"Un taux de TVA avec le code {data.get('code', '')} existe déjà"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer le nouveau taux de TVA
            is_default = data.get('is_default', False)
            if is_default:
                # Désactiver les autres taux par défaut
                TenantVatRate.objects.filter(tenant=tenant, is_default=True).update(is_default=False)
            
            vat_rate = TenantVatRate.objects.create(
                tenant=tenant,
                code=data.get('code', ''),
                name=data.get('name', ''),
                rate=data.get('rate', 0),
                description=data.get('description', ''),
                is_default=is_default,
                is_active=data.get('is_active', True)
            )
            
            return Response({
                'id': str(vat_rate.id),
                'code': vat_rate.code,
                'name': vat_rate.name,
                'rate': vat_rate.rate,
                'rate_display': f"{vat_rate.rate}%",
                'description': vat_rate.description,
                'is_default': vat_rate.is_default,
                'is_active': vat_rate.is_active
            }, status=status.HTTP_201_CREATED)
        
        # PUT/PATCH: Mettre à jour les taux de TVA
        elif request.method in ['PUT', 'PATCH']:
            data = request.data
            
            # Si on reçoit une liste de taux de TVA
            if isinstance(data, list):
                # Supprimer tous les taux existants
                TenantVatRate.objects.filter(tenant=tenant).delete()
                
                # Créer les nouveaux taux
                created_rates = []
                for rate_data in data:
                    is_default = rate_data.get('is_default', False)
                    if is_default and created_rates:
                        # Désactiver les autres taux par défaut
                        for rate in created_rates:
                            if rate.is_default:
                                rate.is_default = False
                                rate.save()
                    
                    vat_rate = TenantVatRate.objects.create(
                        tenant=tenant,
                        code=rate_data.get('code', ''),
                        name=rate_data.get('name', ''),
                        rate=rate_data.get('rate', 0),
                        description=rate_data.get('description', ''),
                        is_default=is_default,
                        is_active=rate_data.get('is_active', True)
                    )
                    created_rates.append(vat_rate)
                
                # Préparer la réponse
                response_data = []
                for rate in created_rates:
                    response_data.append({
                        'id': str(rate.id),
                        'code': rate.code,
                        'name': rate.name,
                        'rate': rate.rate,
                        'rate_display': f"{rate.rate}%",
                        'description': rate.description,
                        'is_default': rate.is_default,
                        'is_active': rate.is_active
                    })
                
                return Response(response_data)
            
            # Si on reçoit un seul taux de TVA
            else:
                rate_id = data.get('id')
                if not rate_id:
                    return Response(
                        {"detail": "ID du taux de TVA manquant"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    vat_rate = TenantVatRate.objects.get(tenant=tenant, id=rate_id)
                    
                    # Mettre à jour les champs
                    if 'code' in data:
                        vat_rate.code = data['code']
                    if 'name' in data:
                        vat_rate.name = data['name']
                    if 'rate' in data:
                        vat_rate.rate = data['rate']
                    if 'description' in data:
                        vat_rate.description = data['description']
                    if 'is_active' in data:
                        vat_rate.is_active = data['is_active']
                    
                    # Gérer le champ is_default
                    if 'is_default' in data and data['is_default'] and not vat_rate.is_default:
                        # Désactiver les autres taux par défaut
                        TenantVatRate.objects.filter(tenant=tenant, is_default=True).update(is_default=False)
                        vat_rate.is_default = True
                    
                    vat_rate.save()
                    
                    return Response({
                        'id': str(vat_rate.id),
                        'code': vat_rate.code,
                        'name': vat_rate.name,
                        'rate': vat_rate.rate,
                        'rate_display': f"{vat_rate.rate}%",
                        'description': vat_rate.description,
                        'is_default': vat_rate.is_default,
                        'is_active': vat_rate.is_active
                    })
                except TenantVatRate.DoesNotExist:
                    return Response(
                        {"detail": f"Taux de TVA avec ID {rate_id} non trouvé"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
        
        # DELETE: Supprimer un taux de TVA
        elif request.method == 'DELETE':
            rate_id = request.query_params.get('id')
            if not rate_id:
                return Response(
                    {"detail": "ID du taux de TVA manquant"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                vat_rate = TenantVatRate.objects.get(tenant=tenant, id=rate_id)
                
                # Empêcher la suppression du taux par défaut s'il n'y a pas d'autre taux
                if vat_rate.is_default and TenantVatRate.objects.filter(tenant=tenant).count() > 1:
                    # Trouver un autre taux à définir comme défaut
                    other_rate = TenantVatRate.objects.filter(tenant=tenant).exclude(id=rate_id).first()
                    if other_rate:
                        other_rate.is_default = True
                        other_rate.save()
                
                vat_rate.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except TenantVatRate.DoesNotExist:
                return Response(
                    {"detail": f"Taux de TVA avec ID {rate_id} non trouvé"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({"detail": "Méthode non autorisée"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant avec ID {tenant_id} non trouvé"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la gestion des taux de TVA: {str(e)}")
        return Response(
            {"detail": f"Une erreur est survenue: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.AllowAny])
def tenant_payment_terms(request):
    """
    Endpoint spécifique pour gérer les conditions de paiement d'un tenant
    GET: Récupérer les conditions de paiement
    POST: Créer une nouvelle condition de paiement
    PUT/PATCH: Mettre à jour les conditions de paiement existantes
    DELETE: Supprimer une condition de paiement
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log détaillé pour le débogage
    logger.info(f"Appel à tenant_payment_terms - Méthode: {request.method} - Headers: {request.headers}")
    logger.info(f"Appel à tenant_payment_terms - URL: {request.path}")
    if request.body:
        logger.info(f"Contenu de la requête: {request.body.decode('utf-8')}")
    
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        # GET: Récupérer les conditions de paiement
        if request.method == 'GET':
            payment_terms = tenant.payment_terms.all()
            response_data = []
            
            for term in payment_terms:
                response_data.append({
                    'id': str(term.id),
                    'label': term.label,
                    'days': term.days,
                    'description': term.description,
                    'is_default': term.is_default,
                    'is_active': term.is_active
                })
            
            return Response(response_data)
        
        # POST: Créer une nouvelle condition de paiement
        elif request.method == 'POST':
            data = request.data
            
            # Vérifier si une condition avec le même libellé existe déjà
            if TenantPaymentTerm.objects.filter(tenant=tenant, label=data.get('label', '')).exists():
                return Response(
                    {"detail": f"Une condition de paiement avec le libellé {data.get('label', '')} existe déjà"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer la nouvelle condition de paiement
            is_default = data.get('is_default', False)
            if is_default:
                # Désactiver les autres conditions par défaut
                TenantPaymentTerm.objects.filter(tenant=tenant, is_default=True).update(is_default=False)
            
            payment_term = TenantPaymentTerm.objects.create(
                tenant=tenant,
                label=data.get('label', ''),
                days=data.get('days', 0),
                description=data.get('description', ''),
                is_default=is_default,
                is_active=data.get('is_active', True)
            )
            
            return Response({
                'id': str(payment_term.id),
                'label': payment_term.label,
                'days': payment_term.days,
                'description': payment_term.description,
                'is_default': payment_term.is_default,
                'is_active': payment_term.is_active
            }, status=status.HTTP_201_CREATED)
        
        # PUT/PATCH: Mettre à jour les conditions de paiement
        elif request.method in ['PUT', 'PATCH']:
            data = request.data
            
            # Si on reçoit une liste de conditions de paiement
            if isinstance(data, list):
                # Supprimer toutes les conditions existantes
                TenantPaymentTerm.objects.filter(tenant=tenant).delete()
                
                # Créer les nouvelles conditions
                created_terms = []
                for term_data in data:
                    is_default = term_data.get('is_default', False)
                    if is_default and created_terms:
                        # Désactiver les autres conditions par défaut
                        for term in created_terms:
                            if term.is_default:
                                term.is_default = False
                                term.save()
                    
                    payment_term = TenantPaymentTerm.objects.create(
                        tenant=tenant,
                        label=term_data.get('label', ''),
                        days=term_data.get('days', 0),
                        description=term_data.get('description', ''),
                        is_default=is_default,
                        is_active=term_data.get('is_active', True)
                    )
                    created_terms.append(payment_term)
                
                # Préparer la réponse
                response_data = []
                for term in created_terms:
                    response_data.append({
                        'id': str(term.id),
                        'label': term.label,
                        'days': term.days,
                        'description': term.description,
                        'is_default': term.is_default,
                        'is_active': term.is_active
                    })
                
                return Response(response_data)
            
            # Si on reçoit une seule condition de paiement
            else:
                term_id = data.get('id')
                if not term_id:
                    return Response(
                        {"detail": "ID de la condition de paiement manquant"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    payment_term = TenantPaymentTerm.objects.get(tenant=tenant, id=term_id)
                    
                    # Mettre à jour les champs
                    if 'label' in data:
                        payment_term.label = data['label']
                    if 'days' in data:
                        payment_term.days = data['days']
                    if 'description' in data:
                        payment_term.description = data['description']
                    if 'is_active' in data:
                        payment_term.is_active = data['is_active']
                    
                    # Gérer le champ is_default
                    if 'is_default' in data and data['is_default'] and not payment_term.is_default:
                        # Désactiver les autres conditions par défaut
                        TenantPaymentTerm.objects.filter(tenant=tenant, is_default=True).update(is_default=False)
                        payment_term.is_default = True
                    
                    payment_term.save()
                    
                    return Response({
                        'id': str(payment_term.id),
                        'label': payment_term.label,
                        'days': payment_term.days,
                        'description': payment_term.description,
                        'is_default': payment_term.is_default,
                        'is_active': payment_term.is_active
                    })
                except TenantPaymentTerm.DoesNotExist:
                    return Response(
                        {"detail": f"Condition de paiement avec ID {term_id} non trouvée"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
        
        # DELETE: Supprimer une condition de paiement
        elif request.method == 'DELETE':
            term_id = request.query_params.get('id')
            if not term_id:
                return Response(
                    {"detail": "ID de la condition de paiement manquant"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                payment_term = TenantPaymentTerm.objects.get(tenant=tenant, id=term_id)
                
                # Empêcher la suppression de la condition par défaut s'il n'y a pas d'autre condition
                if payment_term.is_default and TenantPaymentTerm.objects.filter(tenant=tenant).count() > 1:
                    # Trouver une autre condition à définir comme défaut
                    other_term = TenantPaymentTerm.objects.filter(tenant=tenant).exclude(id=term_id).first()
                    if other_term:
                        other_term.is_default = True
                        other_term.save()
                
                payment_term.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
                
            except TenantPaymentTerm.DoesNotExist:
                return Response(
                    {"detail": f"Condition de paiement avec ID {term_id} non trouvée"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({"detail": "Méthode non autorisée"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant with id {tenant_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors du traitement des conditions de paiement: {str(e)}")
        return Response(
            {"detail": f"Une erreur est survenue: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Endpoint de santé du service tenant"""
    return Response({
        "service": "tenant-service",
        "status": "healthy",
        "version": "2.0.0"
    })
