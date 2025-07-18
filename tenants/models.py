from django.db import models
import uuid
from django.utils import timezone

# Create your models here.

class Tenant(models.Model):
    """
    Modèle principal pour gérer les tenants (entreprises clientes)
    """
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nom de l\'entreprise', max_length=255, unique=True)
    slug = models.SlugField('Slug', max_length=255, unique=True, blank=True)
    domain = models.CharField('Domaine', max_length=255, unique=True, null=True, blank=True)
    
    # Informations de contact
    email = models.EmailField('Email principal', blank=True)
    phone = models.CharField('Téléphone', max_length=20, blank=True)
    website = models.URLField('Site web', blank=True)
    
    # Adresse
    address_line_1 = models.CharField('Adresse ligne 1', max_length=255, blank=True)
    address_line_2 = models.CharField('Adresse ligne 2', max_length=255, blank=True)
    city = models.CharField('Ville', max_length=100, blank=True)
    postal_code = models.CharField('Code postal', max_length=20, blank=True)
    country = models.CharField('Pays', max_length=100, default='France')
    
    # Informations légales
    siret = models.CharField('SIRET', max_length=14, blank=True)
    vat_number = models.CharField('Numéro de TVA', max_length=50, blank=True)
    legal_form = models.CharField('Forme juridique', max_length=100, blank=True)
    
    # Statut et gestion
    is_active = models.BooleanField('Actif', default=True)
    is_trial = models.BooleanField('En période d\'essai', default=True)
    trial_end_date = models.DateTimeField('Fin de la période d\'essai', null=True, blank=True)
    
    # Abonnement
    subscription_plan = models.CharField(
        'Plan d\'abonnement',
        max_length=50,
        choices=[
            ('trial', 'Essai gratuit'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='trial'
    )
    max_users = models.IntegerField('Nombre maximum d\'utilisateurs', default=5)
    max_storage_gb = models.IntegerField('Stockage maximum (GB)', default=1)
    
    # Métadonnées
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    created_by = models.UUIDField('Créé par (user_id)', null=True, blank=True)
    
    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['domain']),
            models.Index(fields=['is_active']),
            models.Index(fields=['subscription_plan']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le slug
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Définir la date de fin d'essai si c'est un nouveau tenant en trial
        if not self.pk and self.is_trial and not self.trial_end_date:
            from datetime import timedelta
            self.trial_end_date = timezone.now() + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    @property
    def is_trial_expired(self):
        """Vérifier si la période d'essai est expirée"""
        if not self.is_trial or not self.trial_end_date:
            return False
        return timezone.now() > self.trial_end_date
    
    @property
    def days_left_in_trial(self):
        """Nombre de jours restants dans la période d'essai"""
        if not self.is_trial or not self.trial_end_date:
            return 0
        delta = self.trial_end_date - timezone.now()
        return max(0, delta.days)
    
    @property
    def full_address(self):
        """Adresse complète formatée"""
        parts = [
            self.address_line_1,
            self.address_line_2,
            f"{self.postal_code} {self.city}".strip(),
            self.country
        ]
        return ', '.join([part for part in parts if part])


class TenantSettings(models.Model):
    """
    Paramètres spécifiques à chaque tenant
    """
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Paramètres d'apparence
    timezone = models.CharField('Fuseau horaire', max_length=50, default='Europe/Paris')
    language = models.CharField('Langue', max_length=10, default='fr')
    currency = models.CharField('Devise', max_length=3, default='EUR')
    date_format = models.CharField('Format de date', max_length=20, default='DD/MM/YYYY')
    
    # Paramètres visuels
    logo_url = models.URLField('URL du logo', max_length=255, blank=True)
    logo_data = models.TextField('Données du logo (base64)', blank=True, help_text='Logo encodé en base64')
    primary_color = models.CharField('Couleur principale', max_length=10, default='#007bff')
    secondary_color = models.CharField('Couleur secondaire', max_length=10, default='#6c757d')
    accent_color = models.CharField('Couleur d\'accent', max_length=10, default='#28a745')
    
    # Paramètres de notification
    email_notifications = models.BooleanField('Notifications par email', default=True)
    sms_notifications = models.BooleanField('Notifications par SMS', default=False)
    push_notifications = models.BooleanField('Notifications push', default=True)
    
    # Paramètres de sécurité
    password_expiry_days = models.IntegerField('Expiration mot de passe (jours)', default=90)
    max_login_attempts = models.IntegerField('Tentatives de connexion max', default=5)
    session_timeout_minutes = models.IntegerField('Timeout session (minutes)', default=480)
    require_2fa = models.BooleanField('Authentification à 2 facteurs obligatoire', default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_settings'
        verbose_name = 'Paramètres Tenant'
        verbose_name_plural = 'Paramètres Tenants'
    
    def __str__(self):
        return f"Paramètres de {self.tenant.name}"


class TenantBankInfo(models.Model):
    """
    Informations bancaires du tenant
    """
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='bank_info'
    )
    iban = models.CharField('IBAN', max_length=50, blank=True)
    bic = models.CharField('BIC/SWIFT', max_length=20, blank=True)
    bank_name = models.CharField('Nom de la banque', max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_bank_info'
        verbose_name = 'Informations bancaires'
        verbose_name_plural = 'Informations bancaires'
    
    def __str__(self):
        return f"Informations bancaires de {self.tenant.name}"


class TenantVatRate(models.Model):
    """
    Taux de TVA personnalisés par tenant
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='vat_rates'
    )
    code = models.CharField('Code', max_length=10)
    name = models.CharField('Nom', max_length=50)
    rate = models.DecimalField('Taux', max_digits=5, decimal_places=2)
    description = models.CharField('Description', max_length=255, blank=True)
    is_default = models.BooleanField('Par défaut', default=False)
    is_active = models.BooleanField('Actif', default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_vat_rates'
        verbose_name = 'Taux de TVA'
        verbose_name_plural = 'Taux de TVA'
        unique_together = ['tenant', 'code']
        
    def __str__(self):
        return f"{self.name} ({self.rate}%) - {self.tenant.name}"


class TenantPaymentTerm(models.Model):
    """
    Conditions de paiement personnalisées par tenant
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='payment_terms'
    )
    label = models.CharField('Libellé', max_length=100)
    description = models.CharField('Description', max_length=255, blank=True)
    days = models.IntegerField('Jours', default=0)
    is_default = models.BooleanField('Par défaut', default=False)
    is_active = models.BooleanField('Actif', default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_payment_terms'
        verbose_name = 'Condition de paiement'
        verbose_name_plural = 'Conditions de paiement'
        
    def __str__(self):
        if self.days == 0:
            return f"{self.label} - {self.tenant.name}"
        else:
            return f"{self.label} ({self.days} jours) - {self.tenant.name}"


class TenantDocumentAppearance(models.Model):
    """
    Configuration de l'apparence des documents par tenant
    """
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='document_appearance'
    )
    
    # En-tête et pied de page
    header_text = models.TextField('Texte d\'en-tête', blank=True)
    footer_text = models.TextField('Texte de pied de page', blank=True)
    show_logo = models.BooleanField('Afficher le logo', default=True)
    logo_position = models.CharField('Position du logo', max_length=10, default='left',
                                   choices=(
                                       ('left', 'Gauche'),
                                       ('center', 'Centre'),
                                       ('right', 'Droite')
                                   ))
    
    # Styles
    font_family = models.CharField('Police', max_length=50, default='Arial')
    font_size = models.IntegerField('Taille de police', default=11)
    line_spacing = models.FloatField('Interligne', default=1.5)
    
    # Marges (en mm)
    margin_top = models.IntegerField('Marge supérieure', default=25)
    margin_right = models.IntegerField('Marge droite', default=20)
    margin_bottom = models.IntegerField('Marge inférieure', default=25)
    margin_left = models.IntegerField('Marge gauche', default=20)
    
    # Autres options
    show_payment_details = models.BooleanField('Afficher les détails de paiement', default=True)
    show_legal_mentions = models.BooleanField('Afficher les mentions légales', default=True)
    legal_mentions = models.TextField('Mentions légales', blank=True)
    
    # Couleurs
    table_header_color = models.CharField('Couleur en-tête tableau', max_length=10, default='#f8f9fa')
    table_alternate_color = models.CharField('Couleur alternée tableau', max_length=10, default='#f2f2f2')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_document_appearance'
        verbose_name = 'Apparence des documents'
        verbose_name_plural = 'Apparence des documents'
    
    def __str__(self):
        return f"Apparence des documents - {self.tenant.name}"


class TenantDocumentNumbering(models.Model):
    """
    Configuration de la numérotation des documents par tenant
    """
    DOCUMENT_TYPES = (
        ('invoice', 'Facture'),
        ('quote', 'Devis'),
        ('order', 'Commande'),
        ('delivery', 'Bon de livraison'),
        ('credit_note', 'Avoir'),
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='document_numbering'
    )
    document_type = models.CharField('Type de document', max_length=20, choices=DOCUMENT_TYPES)
    prefix = models.CharField('Préfixe', max_length=10, blank=True)
    suffix = models.CharField('Suffixe', max_length=10, blank=True)
    next_number = models.IntegerField('Prochain numéro', default=1)
    padding = models.IntegerField('Nombre de chiffres', default=4,
                                 help_text='Nombre de chiffres pour le numéro (ex: 4 pour 0001)')
    include_year = models.BooleanField('Inclure l\'année', default=True)
    include_month = models.BooleanField('Inclure le mois', default=False)
    reset_yearly = models.BooleanField('Réinitialiser chaque année', default=True)
    reset_monthly = models.BooleanField('Réinitialiser chaque mois', default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_document_numbering'
        verbose_name = 'Numérotation de document'
        verbose_name_plural = 'Numérotations de documents'
        unique_together = ['tenant', 'document_type']
        
    def __str__(self):
        return f"Numérotation {self.get_document_type_display()} - {self.tenant.name}"
        
    def get_next_number(self):
        """
        Génère le prochain numéro de document selon le format configuré
        """
        import datetime
        now = datetime.datetime.now()
        
        parts = []
        
        # Ajouter le préfixe s'il existe
        if self.prefix:
            parts.append(self.prefix)
            
        # Ajouter l'année si demandé
        if self.include_year:
            parts.append(str(now.year))
            
        # Ajouter le mois si demandé
        if self.include_month:
            parts.append(f"{now.month:02d}")
            
        # Ajouter le numéro avec padding
        parts.append(f"{self.next_number:0{self.padding}d}")
        
        # Ajouter le suffixe s'il existe
        if self.suffix:
            parts.append(self.suffix)
            
        # Incrémenter le compteur
        self.next_number += 1
        self.save()
        
        return "-".join(parts)


class TenantInvitation(models.Model):
    """
    Invitations pour rejoindre un tenant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    email = models.EmailField('Email de l\'invité')
    invited_by = models.UUIDField('Invité par (user_id)')
    role = models.CharField(
        'Rôle',
        max_length=50,
        choices=[
            ('user', 'Utilisateur'),
            ('admin', 'Administrateur'),
            ('manager', 'Manager'),
        ],
        default='user'
    )
    
    # Token et statut
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_accepted = models.BooleanField('Acceptée', default=False)
    is_expired = models.BooleanField('Expirée', default=False)
    expires_at = models.DateTimeField('Expire le')
    accepted_at = models.DateTimeField('Acceptée le', null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_invitations'
        verbose_name = 'Invitation Tenant'
        verbose_name_plural = 'Invitations Tenants'
        unique_together = ['tenant', 'email']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Invitation de {self.email} pour {self.tenant.name}"
    
    def save(self, *args, **kwargs):
        # Définir la date d'expiration si pas définie
        if not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Vérifier si l'invitation est encore valide"""
        return (
            not self.is_accepted and
            not self.is_expired and
            timezone.now() < self.expires_at
        )
    
    def accept(self):
        """Marquer l'invitation comme acceptée"""
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()
    
    def expire(self):
        """Marquer l'invitation comme expirée"""
        self.is_expired = True
        self.save()


class TenantUsage(models.Model):
    """
    Suivi de l'utilisation des ressources par tenant
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='usage_records'
    )
    
    # Métriques d'usage
    date = models.DateField('Date')
    active_users_count = models.IntegerField('Nombre d\'utilisateurs actifs', default=0)
    storage_used_gb = models.DecimalField('Stockage utilisé (GB)', max_digits=10, decimal_places=2, default=0)
    api_calls_count = models.IntegerField('Nombre d\'appels API', default=0)
    
    # Statistiques d'activité
    logins_count = models.IntegerField('Nombre de connexions', default=0)
    documents_created = models.IntegerField('Documents créés', default=0)
    documents_updated = models.IntegerField('Documents modifiés', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_usage'
        verbose_name = 'Utilisation Tenant'
        verbose_name_plural = 'Utilisations Tenants'
        unique_together = ['tenant', 'date']
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Usage de {self.tenant.name} le {self.date}"
