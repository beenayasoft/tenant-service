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
    """Serializer pour l'apparence des documents"""
    logo_position_display = serializers.CharField(source='get_logo_position_display', read_only=True)
    logo_position_type_display = serializers.CharField(source='get_logo_position_type_display', read_only=True)
    document_template_display = serializers.CharField(source='get_document_template_display', read_only=True)
    
    class Meta:
        model = TenantDocumentAppearance
        exclude = ['tenant', 'created_at', 'updated_at']
    
    def validate_logo_size(self, value):
        """Valider que la taille du logo est dans les limites acceptables"""
        if value < 50 or value > 200:
            raise serializers.ValidationError("La taille du logo doit être entre 50% et 200%")
        return value
    
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
