from rest_framework import serializers
from django.utils import timezone
from .models import (
    Tenant, TenantSettings, TenantInvitation, TenantUsage,
    TenantBankInfo, TenantVatRate, TenantPaymentTerm,
    TenantDocumentNumbering, TenantDocumentAppearance, TenantPaymentMethod
)


class TenantSettingsSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres de tenant"""
    
    class Meta:
        model = TenantSettings
        exclude = ['tenant', 'created_at', 'updated_at']


class TenantBankInfoSerializer(serializers.ModelSerializer):
    """Serializer pour les informations bancaires du tenant"""
    
    class Meta:
        model = TenantBankInfo
        exclude = ['tenant', 'created_at', 'updated_at']


class TenantVatRateSerializer(serializers.ModelSerializer):
    """Serializer pour les taux de TVA personnalisés"""
    rate_display = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantVatRate
        exclude = ['tenant', 'created_at', 'updated_at']
    
    def get_rate_display(self, obj):
        return f"{obj.rate}%"


class TenantPaymentTermSerializer(serializers.ModelSerializer):
    """Serializer pour les conditions de paiement"""
    
    class Meta:
        model = TenantPaymentTerm
        exclude = ['tenant', 'created_at', 'updated_at']


class TenantDocumentNumberingSerializer(serializers.ModelSerializer):
    """Serializer pour la numérotation des documents"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = TenantDocumentNumbering
        exclude = ['tenant', 'created_at', 'updated_at']


class TenantDocumentAppearanceSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'apparence des documents
    Compatible avec l'interface frontend DocumentAppearanceConfig
    """
    logo_position_display = serializers.CharField(source='get_logo_position_display', read_only=True)
    logo_position_type_display = serializers.CharField(source='get_logo_position_type_display', read_only=True)
    document_template_display = serializers.CharField(source='get_document_template_display', read_only=True)
    
    class Meta:
        model = TenantDocumentAppearance
        exclude = ['tenant', 'created_at', 'updated_at']
    
    def validate_logo_size(self, value):
        """Valider que la taille du logo est dans les limites acceptables"""
        if value < 20 or value > 120:
            raise serializers.ValidationError("La taille du logo doit être entre 20px et 120px")
        return value
    
    def to_representation(self, instance):
        """
        Transformer la représentation pour correspondre à l'interface frontend
        """
        data = super().to_representation(instance)
        
        # Mapper les champs du modèle Django vers l'interface TypeScript
        frontend_config = {
            # Configuration générale
            'documentTemplate': data.get('document_template', 'modern'),
            'primaryColor': data.get('primary_color', '#1B333F'),
            'secondaryColor': data.get('secondary_color', '#64748B') if hasattr(instance, 'secondary_color') else '#64748B',
            'fontFamily': data.get('font_family', 'Inter'),
            'fontSize': data.get('font_size', 11),
            
            # Logo et branding
            'showLogo': data.get('show_logo', True),
            'logoData': data.get('logo_data'),
            'logoSize': data.get('logo_size', 60),
            'logoPositionType': data.get('logo_position_type', 'left'),
            'logoCenterInHeader': data.get('logo_center_in_header', False),
            
            # Informations entreprise
            'showCompanyName': data.get('show_company_name', True),
            'showCompanyAddress': data.get('show_company_address', True),
            'showCompanyEmail': data.get('show_company_email', True),
            'showCompanyPhone': data.get('show_company_phone', True),
            'showCompanyWebsite': data.get('show_company_website', True),
            'showCompanySiret': data.get('show_company_siret', True),
            'showCompanyIce': data.get('show_company_ice', True),
            
            # Informations client et projet
            'showClientAddress': data.get('show_client_address', True),
            'showProjectInfo': data.get('show_project_info', True),
            
            # Contenu et notes
            'showNotes': data.get('show_notes', True),
            'showPaymentTerms': data.get('show_payment_terms', True),
            'showBankDetails': data.get('show_bank_details', True),
            'showSignatureArea': data.get('show_signature_area', True),
            
            # Style des tableaux
            'tableHeaderColor': data.get('table_header_color', '#F8F9FA'),
            'tableAlternateColor': data.get('table_alternate_color', '#F2F2F2'),
            'tableBorderStyle': data.get('table_border_style', 'rounded'),
            'tableBorderHorizontal': data.get('table_border_horizontal', True),
            'tableBorderVertical': data.get('table_border_vertical', True),
            'tableBorderWidth': data.get('table_border_width', 1),
            'tableBorderColor': data.get('table_border_color', '#E2E8F0'),
            'sectionContrast': data.get('section_contrast', True),
            'sectionContrastColor': data.get('section_contrast_color', '#EEF2FF'),
            'showSectionSubtotals': data.get('show_section_subtotals', True),
            'tableRowPadding': data.get('table_row_padding', 8),
            'tableColumnSpacing': data.get('table_column_spacing', 12),
            
            # Moyens de paiement
            'showPaymentMethods': data.get('show_payment_methods', True),
            'paymentMethodsTitle': data.get('payment_methods_title', 'Moyens de paiement'),
            'paymentMethodsLayout': data.get('payment_methods_layout', 'horizontal'),
            'paymentMethodsStyle': data.get('payment_methods_style', 'modern'),
        }
        
        return frontend_config
    
    def to_internal_value(self, data):
        """
        Transformer les données frontend vers le format Django
        """
        # Mapper les champs TypeScript vers Django - Support des deux formats
        django_data = {
            # Configuration générale
            'document_template': data.get('document_template', data.get('documentTemplate', 'modern')),
            'primary_color': data.get('primary_color', data.get('primaryColor', '#1B333F')),
            'font_family': data.get('font_family', data.get('fontFamily', 'Inter')),
            'font_size': data.get('font_size', data.get('fontSize', 11)),
            
            # Logo et branding - Support des deux formats (camelCase et snake_case)
            'show_logo': data.get('show_logo', data.get('showLogo', True)),
            'logo_data': data.get('logo_data', data.get('logoData')),
            'logo_size': data.get('logo_size', data.get('logoSize', 60)),
            'logo_position_type': data.get('logo_position_type', data.get('logoPositionType', 'left')),
            'logo_center_in_header': data.get('logo_center_in_header', data.get('logoCenterInHeader', False)),
            
            # Informations entreprise
            'show_company_name': data.get('show_company_name', data.get('showCompanyName', True)),
            'show_company_address': data.get('show_company_address', data.get('showCompanyAddress', True)),
            'show_company_email': data.get('show_company_email', data.get('showCompanyEmail', True)),
            'show_company_phone': data.get('show_company_phone', data.get('showCompanyPhone', True)),
            'show_company_website': data.get('show_company_website', data.get('showCompanyWebsite', True)),
            'show_company_siret': data.get('show_company_siret', data.get('showCompanySiret', True)),
            'show_company_ice': data.get('show_company_ice', data.get('showCompanyIce', True)),
            
            # Informations client et projet
            'show_client_address': data.get('show_client_address', data.get('showClientAddress', True)),
            'show_project_info': data.get('show_project_info', data.get('showProjectInfo', True)),
            
            # Contenu et notes
            'show_notes': data.get('show_notes', data.get('showNotes', True)),
            'show_payment_terms': data.get('show_payment_terms', data.get('showPaymentTerms', True)),
            'show_bank_details': data.get('show_bank_details', data.get('showBankDetails', True)),
            'show_signature_area': data.get('show_signature_area', data.get('showSignatureArea', True)),
            
            # Style des tableaux
            'table_header_color': data.get('table_header_color', data.get('tableHeaderColor', '#F8F9FA')),
            'table_alternate_color': data.get('table_alternate_color', data.get('tableAlternateColor', '#F2F2F2')),
            'table_border_style': data.get('table_border_style', data.get('tableBorderStyle', 'rounded')),
            'table_border_horizontal': data.get('table_border_horizontal', data.get('tableBorderHorizontal', True)),
            'table_border_vertical': data.get('table_border_vertical', data.get('tableBorderVertical', True)),
            'table_border_width': data.get('table_border_width', data.get('tableBorderWidth', 1)),
            'table_border_color': data.get('table_border_color', data.get('tableBorderColor', '#E2E8F0')),
            'section_contrast': data.get('section_contrast', data.get('sectionContrast', True)),
            'section_contrast_color': data.get('section_contrast_color', data.get('sectionContrastColor', '#EEF2FF')),
            'show_section_subtotals': data.get('show_section_subtotals', data.get('showSectionSubtotals', True)),
            'table_row_padding': data.get('table_row_padding', data.get('tableRowPadding', 8)),
            'table_column_spacing': data.get('table_column_spacing', data.get('tableColumnSpacing', 12)),
            
            # Moyens de paiement
            'show_payment_methods': data.get('show_payment_methods', data.get('showPaymentMethods', True)),
            'payment_methods_title': data.get('payment_methods_title', data.get('paymentMethodsTitle', 'Moyens de paiement')),
            'payment_methods_layout': data.get('payment_methods_layout', data.get('paymentMethodsLayout', 'horizontal')),
            'payment_methods_style': data.get('payment_methods_style', data.get('paymentMethodsStyle', 'modern')),
        }
        
        # Ajouter la couleur secondaire si disponible dans les données
        if 'secondaryColor' in data or 'secondary_color' in data:
            django_data['secondary_color'] = data.get('secondary_color', data.get('secondaryColor', '#64748B'))
        
        return super().to_internal_value(django_data)
    
    def validate_logo_data(self, value):
        """Valider les données du logo en base64"""
        if value and not value.startswith('data:image/'):
            raise serializers.ValidationError("Le logo doit être au format base64 valide")
        return value
    
    def validate_table_border_width(self, value):
        """Valider l'épaisseur des bordures"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("L'épaisseur des bordures doit être entre 0 et 10 pixels")
        return value
    
    def validate_table_row_padding(self, value):
        """Valider l'espacement des lignes"""
        if value < 0 or value > 50:
            raise serializers.ValidationError("L'espacement des lignes doit être entre 0 et 50 pixels")
        return value
    
    def validate_table_column_spacing(self, value):
        """Valider l'espacement des colonnes"""
        if value < 0 or value > 50:
            raise serializers.ValidationError("L'espacement des colonnes doit être entre 0 et 50 pixels")
        return value


class TenantPaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer pour les moyens de paiement personnalisés"""
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    formatted_details = serializers.ReadOnlyField()
    
    class Meta:
        model = TenantPaymentMethod
        exclude = ['tenant', 'created_at', 'updated_at']
    
    def validate_details(self, value):
        """Valider les détails selon le type de moyen de paiement"""
        method_type = self.initial_data.get('method_type')
        
        if method_type == 'bank_transfer':
            # Pour les virements, l'IBAN est requis
            if not value.get('iban'):
                raise serializers.ValidationError("L'IBAN est requis pour les virements bancaires")
        elif method_type == 'check':
            # Pour les chèques, l'ordre de paiement est requis
            if not value.get('payable_to'):
                raise serializers.ValidationError("L'ordre de paiement est requis pour les chèques")
        
        return value
    
    def validate_background_color(self, value):
        """Valider la couleur de fond"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("La couleur doit être au format hexadécimal (#RRGGBB)")
        return value
    
    def validate_text_color(self, value):
        """Valider la couleur du texte"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("La couleur doit être au format hexadécimal (#RRGGBB)")
        return value
    
    def validate_border_color(self, value):
        """Valider la couleur de la bordure"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("La couleur doit être au format hexadécimal (#RRGGBB)")
        return value


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un tenant"""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'email', 'phone', 'website',
            'address_line_1', 'address_line_2', 'city', 'postal_code', 'country',
            'siret', 'ice', 'legal_form'
        ]
        extra_kwargs = {
            'name': {'required': True},
        }
    
    def create(self, validated_data):
        """Créer un tenant avec ses paramètres par défaut"""
        tenant = Tenant.objects.create(**validated_data)
        
        # Créer les paramètres par défaut
        TenantSettings.objects.create(tenant=tenant)
        
        return tenant


class TenantListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des tenants"""
    days_left_in_trial = serializers.ReadOnlyField()
    is_trial_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'domain', 'email', 'subscription_plan',
            'is_active', 'is_trial', 'days_left_in_trial', 'is_trial_expired',
            'created_at'
        ]


class TenantDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail complet d'un tenant"""
    settings = TenantSettingsSerializer(read_only=True)
    bank_info = TenantBankInfoSerializer(read_only=True)
    vat_rates = TenantVatRateSerializer(many=True, read_only=True)
    payment_terms = TenantPaymentTermSerializer(many=True, read_only=True)
    document_appearance = TenantDocumentAppearanceSerializer(read_only=True)
    document_numbering = TenantDocumentNumberingSerializer(many=True, read_only=True)
    days_left_in_trial = serializers.ReadOnlyField()
    is_trial_expired = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slogan', 'slug', 'domain', 'schema_name', 'email', 'phone', 'website',
            'address_line_1', 'address_line_2', 'city', 'postal_code', 'country',
            'full_address', 'siret', 'ice', 'legal_form',
            'is_active', 'is_trial', 'trial_end_date', 'days_left_in_trial', 'is_trial_expired',
            'subscription_plan', 'max_users', 'max_storage_gb',
            'settings', 'bank_info', 'vat_rates', 'payment_terms', 
            'document_appearance', 'document_numbering',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at', 'trial_end_date'
        ]


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un tenant"""
    settings = TenantSettingsSerializer(required=False)
    bank_info = TenantBankInfoSerializer(required=False)
    document_appearance = TenantDocumentAppearanceSerializer(required=False)
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'slogan', 'domain', 'email', 'phone', 'website',
            'address_line_1', 'address_line_2', 'city', 'postal_code', 'country',
            'siret', 'ice', 'legal_form', 
            'settings', 'bank_info', 'document_appearance'
        ]
    
    def update(self, instance, validated_data):
        """Mise à jour avec gestion des paramètres et relations"""
        settings_data = validated_data.pop('settings', None)
        bank_info_data = validated_data.pop('bank_info', None)
        document_appearance_data = validated_data.pop('document_appearance', None)
        
        # Mettre à jour le tenant
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les paramètres si fournis
        if settings_data:
            settings, created = TenantSettings.objects.get_or_create(tenant=instance)
            for attr, value in settings_data.items():
                setattr(settings, attr, value)
            settings.save()
        
        # Mettre à jour les informations bancaires si fournies
        if bank_info_data:
            bank_info, created = TenantBankInfo.objects.get_or_create(tenant=instance)
            for attr, value in bank_info_data.items():
                setattr(bank_info, attr, value)
            bank_info.save()
        
        # Mettre à jour l'apparence des documents si fournie
        if document_appearance_data:
            appearance, created = TenantDocumentAppearance.objects.get_or_create(tenant=instance)
            for attr, value in document_appearance_data.items():
                setattr(appearance, attr, value)
            appearance.save()
        
        return instance


class TenantInvitationSerializer(serializers.ModelSerializer):
    """Serializer pour les invitations"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = TenantInvitation
        fields = [
            'id', 'tenant', 'tenant_name', 'email', 'role', 'token',
            'is_accepted', 'is_expired', 'is_valid',
            'expires_at', 'accepted_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'token', 'is_accepted', 'is_expired', 'expires_at',
            'accepted_at', 'created_at'
        ]


class TenantInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une invitation"""
    
    class Meta:
        model = TenantInvitation
        fields = ['email', 'role']
    
    def validate_email(self, value):
        """Vérifier que l'email n'est pas déjà invité"""
        tenant = self.context['tenant']
        if TenantInvitation.objects.filter(
            tenant=tenant,
            email=value,
            is_accepted=False,
            is_expired=False
        ).exists():
            raise serializers.ValidationError(
                "Une invitation est déjà en cours pour cette adresse email."
            )
        return value
    
    def create(self, validated_data):
        """Créer une invitation avec le tenant du contexte"""
        validated_data['tenant'] = self.context['tenant']
        validated_data['invited_by'] = self.context['invited_by']
        return TenantInvitation.objects.create(**validated_data)


class TenantUsageSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques d'usage"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = TenantUsage
        fields = [
            'tenant', 'tenant_name', 'date',
            'active_users_count', 'storage_used_gb', 'api_calls_count',
            'logins_count', 'documents_created', 'documents_updated'
        ]
        read_only_fields = ['tenant']


class TenantStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques agrégées d'un tenant"""
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    storage_used_gb = serializers.DecimalField(max_digits=10, decimal_places=2)
    storage_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    api_calls_today = serializers.IntegerField()
    documents_count = serializers.IntegerField()
    last_activity = serializers.DateTimeField()


class TenantValidationSerializer(serializers.Serializer):
    """Serializer pour la validation d'existence d'un tenant"""
    tenant_id = serializers.UUIDField()
    exists = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    name = serializers.CharField(read_only=True)
