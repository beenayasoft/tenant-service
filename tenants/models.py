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
    schema_name = models.CharField(
        'Nom du schéma PostgreSQL',
        max_length=63,
        unique=True,
        blank=True,
        help_text='Nom du schéma PostgreSQL pour django-tenants'
    )
    
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
    ice = models.CharField('ICE (Identifiant Commun de l\'Entreprise)', max_length=50, blank=True)
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
        
        # Générer le nom du schéma si non défini
        if not self.schema_name:
            # Utiliser le slug pour générer un nom de schéma valide
            from django.utils.text import slugify
            schema_base = slugify(self.slug).replace('-', '_')
            schema_name = f"tenant_{schema_base}"[:63]  # Limite PostgreSQL de 63 caractères
            counter = 1
            while Tenant.objects.filter(schema_name=schema_name).exclude(pk=self.pk).exists():
                suffix = f"_{counter}"
                schema_name = f"tenant_{schema_base}{suffix}"[:63]
                counter += 1
            self.schema_name = schema_name
        
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
    currency = models.CharField('Devise', max_length=3, default='MAD')
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
    DOCUMENT_TEMPLATE_CHOICES = (
        ('modern', 'Moderne'),
        ('classic', 'Classique'),
        ('minimal', 'Minimal'),
    )
    
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='document_appearance'
    )
    
    # Template et couleur principale
    document_template = models.CharField(
        'Modèle de document',
        max_length=20,
        choices=DOCUMENT_TEMPLATE_CHOICES,
        default='modern'
    )
    primary_color = models.CharField(
        'Couleur principale',
        max_length=10,
        default='#1B333F',
        help_text='Couleur principale utilisée dans les documents (format HEX)'
    )
    
    # Options de visibilité des éléments
    show_logo = models.BooleanField('Afficher le logo', default=True)
    
    # Informations d'entreprise granulaires
    show_company_name = models.BooleanField('Afficher le nom de l\'entreprise', default=True)
    show_company_address = models.BooleanField('Afficher l\'adresse de l\'entreprise', default=True)
    show_company_email = models.BooleanField('Afficher l\'email de l\'entreprise', default=True)
    show_company_phone = models.BooleanField('Afficher le téléphone de l\'entreprise', default=True)
    show_company_website = models.BooleanField('Afficher le site web de l\'entreprise', default=True)
    show_company_siret = models.BooleanField('Afficher le SIRET', default=True)
    show_company_ice = models.BooleanField('Afficher l\'ICE', default=True)
    
    show_client_address = models.BooleanField('Afficher l\'adresse du client', default=True)
    show_project_info = models.BooleanField('Afficher les informations du projet', default=True)
    show_notes = models.BooleanField('Afficher les notes', default=True)
    show_payment_terms = models.BooleanField('Afficher les conditions de paiement', default=True)
    show_bank_details = models.BooleanField('Afficher les coordonnées bancaires', default=True)
    show_signature_area = models.BooleanField('Afficher la zone de signature (devis)', default=True)
    
    # En-tête et pied de page
    header_text = models.TextField('Texte d\'en-tête', blank=True)
    footer_text = models.TextField('Texte de pied de page', blank=True)
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
    
    # Options héritées (compatibilité)
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
    Supporte les formats standards et personnalisés
    """
    DOCUMENT_TYPES = (
        ('invoice', 'Facture'),
        ('quote', 'Devis'),
        ('order', 'Commande'),
        ('delivery', 'Bon de livraison'),
        ('credit_note', 'Avoir'),
    )
    
    DATE_FORMAT_CHOICES = (
        ('YYYY-MM-DD', '2024-07-23'),
        ('YYYY-MM', '2024-07'),
        ('YYYY', '2024'),
        ('DD-MM-YYYY', '23-07-2024'),
        ('MM-DD-YYYY', '07-23-2024'),
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='document_numbering'
    )
    document_type = models.CharField('Type de document', max_length=20, choices=DOCUMENT_TYPES)
    
    # Configuration de base
    prefix = models.CharField('Préfixe', max_length=20, blank=True, 
                             help_text='Préfixe du numéro (ex: MEAK, CONSTRUCTION)')
    suffix = models.CharField('Suffixe', max_length=10, blank=True,
                             help_text='Suffixe optionnel')
    next_number = models.IntegerField('Prochain numéro', default=1)
    padding = models.IntegerField('Nombre de chiffres', default=3,
                                 help_text='Nombre de chiffres pour le numéro (ex: 3 pour 001)')
    
    # Configuration de date
    include_year = models.BooleanField('Inclure l\'année', default=True)
    include_month = models.BooleanField('Inclure le mois', default=False)
    include_day = models.BooleanField('Inclure le jour', default=False)
    date_format = models.CharField('Format de date', max_length=20, 
                                  choices=DATE_FORMAT_CHOICES, default='YYYY-MM-DD',
                                  help_text='Format d\'affichage de la date')
    
    # Configuration de formatage
    separator = models.CharField('Séparateur', max_length=3, default='-',
                                help_text='Caractère de séparation entre les parties')
    custom_format = models.CharField('Format personnalisé', max_length=100, blank=True,
                                   help_text='Format libre : {prefix}-{year}-{month}-{day}-{number}')
    
    # Configuration de réinitialisation
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
        Supporte les formats standards et personnalisés
        """
        import datetime
        now = datetime.datetime.now()
        
        # Vérifier si c'est le moment de réinitialiser le compteur
        self._check_and_reset_counter(now)
        
        # Format personnalisé
        if self.custom_format:
            number = self._generate_custom_format(now)
        else:
            # Format standard amélioré
            number = self._generate_standard_format(now)
        
        # Incrémenter le compteur
        self.next_number += 1
        self.save()
        
        return number
    
    def preview_next_number(self):
        """
        Aperçu du prochain numéro sans incrémenter le compteur
        """
        import datetime
        now = datetime.datetime.now()
        
        if self.custom_format:
            return self._generate_custom_format(now, preview=True)
        else:
            return self._generate_standard_format(now, preview=True)
    
    def _check_and_reset_counter(self, now):
        """
        Vérifie si le compteur doit être réinitialisé
        """
        should_reset = False
        
        if self.reset_yearly:
            # Réinitialiser si on change d'année
            if self.updated_at.year != now.year:
                should_reset = True
        
        if self.reset_monthly:
            # Réinitialiser si on change de mois
            if (self.updated_at.year != now.year or 
                self.updated_at.month != now.month):
                should_reset = True
        
        if should_reset:
            self.next_number = 1
    
    def _generate_custom_format(self, now, preview=False):
        """
        Génère un numéro selon le format personnalisé
        """
        format_vars = {
            'prefix': self.prefix or '',
            'year': now.year,
            'month': f"{now.month:02d}",
            'day': f"{now.day:02d}",
            'number': f"{self.next_number:0{self.padding}d}",
            'suffix': self.suffix or ''
        }
        
        try:
            return self.custom_format.format(**format_vars)
        except (KeyError, ValueError) as e:
            # Fallback vers le format standard en cas d'erreur
            return self._generate_standard_format(now, preview)
    
    def _generate_standard_format(self, now, preview=False):
        """
        Génère un numéro selon le format standard
        """
        parts = []
        
        # Préfixe
        if self.prefix:
            parts.append(self.prefix)
        
        # Construction de la partie date
        date_parts = []
        if self.include_year:
            date_parts.append(str(now.year))
        if self.include_month:
            date_parts.append(f"{now.month:02d}")
        if self.include_day:
            date_parts.append(f"{now.day:02d}")
        
        if date_parts:
            parts.append(self.separator.join(date_parts))
        
        # Numéro avec padding
        parts.append(f"{self.next_number:0{self.padding}d}")
        
        # Suffixe
        if self.suffix:
            parts.append(self.suffix)
        
        return self.separator.join(parts)
    
    def increment_counter(self):
        """
        Incrémente le compteur manuellement (pour les appels externes)
        """
        self.next_number += 1
        self.save(update_fields=['next_number', 'updated_at'])
        return self.next_number - 1  # Retourne l'ancien numéro
    
    def reset_counter(self, new_value=1):
        """
        Remet le compteur à une valeur spécifique
        """
        self.next_number = new_value
        self.save(update_fields=['next_number', 'updated_at'])
    
    def get_format_description(self):
        """
        Retourne une description du format configuré
        """
        if self.custom_format:
            return f"Format personnalisé : {self.custom_format}"
        
        parts = []
        if self.prefix:
            parts.append(f"Préfixe: {self.prefix}")
        
        date_parts = []
        if self.include_year:
            date_parts.append("ANNÉE")
        if self.include_month:
            date_parts.append("MOIS")
        if self.include_day:
            date_parts.append("JOUR")
        
        if date_parts:
            parts.append(f"Date: {self.separator.join(date_parts)}")
        
        parts.append(f"Numéro: {'0' * (self.padding - 1)}1")
        
        if self.suffix:
            parts.append(f"Suffixe: {self.suffix}")
        
        return f"Format standard : {self.separator.join(parts)}"


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
