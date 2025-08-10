"""
Utilitaires pour le service tenant
"""
import requests
import logging
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

def get_client_ip(request) -> str:
    """
    Récupère l'adresse IP réelle du client
    """
    # Headers possibles pour l'IP réelle (proxy, load balancer, etc.)
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_X_FORWARDED',
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR',
    ]
    
    for header in headers_to_check:
        ip = request.META.get(header)
        if ip:
            # Prendre la première IP si plusieurs séparées par des virgules
            ip = ip.split(',')[0].strip()
            # Vérifier que ce n'est pas une IP locale/privée
            if not _is_private_ip(ip):
                return ip
    
    # Fallback sur REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', '127.0.0.1')

def _is_private_ip(ip: str) -> bool:
    """
    Vérifie si l'IP est privée/locale
    """
    if not ip or ip == '127.0.0.1' or ip == 'localhost':
        return True
    
    # Plages IP privées
    private_ranges = [
        '10.',
        '172.16.', '172.17.', '172.18.', '172.19.',
        '172.20.', '172.21.', '172.22.', '172.23.',
        '172.24.', '172.25.', '172.26.', '172.27.',
        '172.28.', '172.29.', '172.30.', '172.31.',
        '192.168.',
        '169.254.',  # Link-local
    ]
    
    return any(ip.startswith(prefix) for prefix in private_ranges)

def detect_location_from_ip(ip_address: str) -> Dict[str, Optional[str]]:
    """
    Détecte la localisation à partir d'une adresse IP
    Utilise l'API ipapi.co (gratuite, 1000 requêtes/jour)
    """
    default_result = {
        'country_code': 'MA',  # Maroc par défaut pour Beenaya
        'country_name': 'Morocco',
        'currency': 'MAD',
        'timezone': 'Africa/Casablanca',
        'language': 'fr',
        'region': None,
        'city': None,
        'postal_code': None,
        'error': None
    }
    
    # Si IP locale, retourner les valeurs par défaut
    if _is_private_ip(ip_address):
        logger.info(f"IP privée détectée ({ip_address}), utilisation des valeurs par défaut")
        return default_result
    
    try:
        # Utiliser ipapi.co (service gratuit et fiable)
        url = f"https://ipapi.co/{ip_address}/json/"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # Vérifier si l'API a retourné une erreur
        if 'error' in data:
            logger.warning(f"Erreur API ipapi.co: {data['error']}")
            return {**default_result, 'error': data['error']}
        
        # Mapper les devises selon les pays
        currency_mapping = {
            'FR': 'EUR',  # France
            'BE': 'EUR',  # Belgique
            'LU': 'EUR',  # Luxembourg
            'CH': 'CHF',  # Suisse
            'MA': 'MAD',  # Maroc
            'TN': 'TND',  # Tunisie
            'DZ': 'DZD',  # Algérie
            'ES': 'EUR',  # Espagne
            'IT': 'EUR',  # Italie
            'DE': 'EUR',  # Allemagne
            'CA': 'CAD',  # Canada
            'US': 'USD',  # États-Unis
            'GB': 'GBP',  # Royaume-Uni
        }
        
        # Mapper les langues selon les pays
        language_mapping = {
            'FR': 'fr',  # France
            'BE': 'fr',  # Belgique (français par défaut)
            'MA': 'fr',  # Maroc (français comme langue d'affaires)
            'TN': 'fr',  # Tunisie
            'DZ': 'fr',  # Algérie
            'ES': 'es',  # Espagne
            'IT': 'it',  # Italie
            'DE': 'de',  # Allemagne
            'US': 'en',  # États-Unis
            'GB': 'en',  # Royaume-Uni
            'CA': 'fr',  # Canada (français par défaut pour notre contexte)
        }
        
        country_code = data.get('country_code', 'MA')
        
        result = {
            'country_code': country_code,
            'country_name': data.get('country_name', 'Morocco'),
            'currency': currency_mapping.get(country_code, data.get('currency', 'MAD')),
            'timezone': data.get('timezone', 'Africa/Casablanca'),
            'language': language_mapping.get(country_code, 'fr'),
            'region': data.get('region'),
            'city': data.get('city'),
            'postal_code': data.get('postal'),
            'error': None
        }
        
        logger.info(f"Géolocalisation réussie pour IP {ip_address}: {country_code}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau lors de la géolocalisation IP {ip_address}: {e}")
        return {**default_result, 'error': f"Erreur réseau: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la géolocalisation IP {ip_address}: {e}")
        return {**default_result, 'error': f"Erreur inattendue: {str(e)}"}

def get_vat_rates_for_country(country_code: str) -> list:
    """
    Retourne les taux de TVA standards pour un pays donné
    """
    vat_rates_by_country = {
        'FR': [  # France
            {'code': '20', 'name': 'TVA Normale', 'rate': 20.0, 'description': 'Taux normal applicable à la plupart des biens et services', 'is_default': True},
            {'code': '10', 'name': 'TVA Intermédiaire', 'rate': 10.0, 'description': 'Restauration, transport, travaux de logement', 'is_default': False},
            {'code': '5.5', 'name': 'TVA Réduite', 'rate': 5.5, 'description': 'Produits alimentaires, livres, spectacles', 'is_default': False},
            {'code': '0', 'name': 'TVA 0%', 'rate': 0.0, 'description': 'Exports, opérations exonérées', 'is_default': False}
        ],
        'MA': [  # Maroc
            {'code': '20', 'name': 'TVA Normale', 'rate': 20.0, 'description': 'Taux normal applicable à la plupart des biens et services', 'is_default': True},
            {'code': '14', 'name': 'TVA Réduite', 'rate': 14.0, 'description': 'Certains produits et services spécifiques', 'is_default': False},
            {'code': '10', 'name': 'TVA Réduite Spéciale', 'rate': 10.0, 'description': 'Certains produits alimentaires et services', 'is_default': False},
            {'code': '0', 'name': 'TVA 0%', 'rate': 0.0, 'description': 'Exports, opérations exonérées', 'is_default': False}
        ],
        'BE': [  # Belgique
            {'code': '21', 'name': 'TVA Normale', 'rate': 21.0, 'description': 'Taux normal applicable à la plupart des biens et services', 'is_default': True},
            {'code': '12', 'name': 'TVA Intermédiaire', 'rate': 12.0, 'description': 'Margarine, produits d\'origine sociale', 'is_default': False},
            {'code': '6', 'name': 'TVA Réduite', 'rate': 6.0, 'description': 'Produits alimentaires, médicaments, livres', 'is_default': False},
            {'code': '0', 'name': 'TVA 0%', 'rate': 0.0, 'description': 'Exports, opérations exonérées', 'is_default': False}
        ],
        'ES': [  # Espagne
            {'code': '21', 'name': 'IVA General', 'rate': 21.0, 'description': 'Tipo general aplicable a la mayoría de bienes y servicios', 'is_default': True},
            {'code': '10', 'name': 'IVA Reducido', 'rate': 10.0, 'description': 'Transporte, hostelería, servicios culturales', 'is_default': False},
            {'code': '4', 'name': 'IVA Superreducido', 'rate': 4.0, 'description': 'Productos alimentarios básicos, medicamentos, libros', 'is_default': False},
            {'code': '0', 'name': 'IVA 0%', 'rate': 0.0, 'description': 'Exportaciones, operaciones exentas', 'is_default': False}
        ]
    }
    
    # Retourner les taux pour le pays ou les taux par défaut (Maroc)
    return vat_rates_by_country.get(country_code, vat_rates_by_country['MA'])

def create_initial_vat_rates(tenant, country_code: str) -> int:
    """
    Crée les taux de TVA initiaux pour un tenant basé sur le pays
    Retourne le nombre de taux créés
    """
    from .models import TenantVatRate
    
    vat_rates_data = get_vat_rates_for_country(country_code)
    created_count = 0
    
    for rate_data in vat_rates_data:
        try:
            vat_rate = TenantVatRate.objects.create(
                tenant=tenant,
                code=rate_data['code'],
                name=rate_data['name'],
                rate=rate_data['rate'],
                description=rate_data['description'],
                is_default=rate_data['is_default'],
                is_active=True
            )
            created_count += 1
            logger.info(f"Taux de TVA créé: {vat_rate.name} ({vat_rate.rate}%)")
        except Exception as e:
            logger.error(f"Erreur lors de la création du taux de TVA {rate_data['name']}: {e}")
    
    logger.info(f"Création terminée: {created_count} taux de TVA créés pour le pays {country_code}")
    return created_count

def create_tenant_schemas_async(tenant_id: str):
    """
    Crée tous les schémas de services de manière asynchrone
    """
    import threading
    import subprocess
    import os
    from django.utils import timezone
    from .models import Tenant
    
    def schema_creation_worker():
        try:
            logger.info(f"🚀 Début création asynchrone des schémas pour tenant {tenant_id}")
            
            # Récupérer le tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                logger.error(f"❌ Tenant {tenant_id} non trouvé")
                return
            
            # Marquer comme "en cours"
            tenant.schema_status = 'creating'
            tenant.update_schema_progress(0, 4, "Initialisation de la création des schémas...")
            
            # Configuration des services et leurs ports
            services_config = [
                {
                    'name': 'CRM',
                    'path': '../crm-service',
                    'port': 8003,
                    'command': 'migrate_tenant_schemas'
                },
                {
                    'name': 'Documents', 
                    'path': '../document-service',
                    'port': 8004,
                    'command': 'migrate_tenant_schemas'
                },
                {
                    'name': 'Library',
                    'path': '../library-service', 
                    'port': 8005,
                    'command': 'migrate_tenant_schemas'
                }
            ]
            
            current_step = 1
            
            for service_config in services_config:
                try:
                    service_name = service_config['name']
                    service_path = service_config['path']
                    
                    logger.info(f"📊 Création schéma pour service {service_name}")
                    tenant.update_schema_progress(
                        current_step, 
                        4, 
                        f"Configuration du service {service_name}...",
                        service_name.lower()
                    )
                    
                    # Construire le chemin absolu vers le service
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    service_dir = os.path.join(base_dir, service_path)
                    
                    if os.path.exists(service_dir):
                        # Exécuter la commande de migration pour ce service
                        cmd = [
                            'python', 'manage.py', 
                            service_config['command'],
                            '--verbosity=1'
                        ]
                        
                        result = subprocess.run(
                            cmd,
                            cwd=service_dir,
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes timeout par service
                        )
                        
                        if result.returncode == 0:
                            logger.info(f"✅ Schéma {service_name} créé avec succès")
                        else:
                            logger.error(f"❌ Erreur création schéma {service_name}: {result.stderr}")
                            raise Exception(f"Erreur {service_name}: {result.stderr}")
                    else:
                        logger.warning(f"⚠️ Service {service_name} non trouvé à {service_dir}")
                    
                    current_step += 1
                    
                except subprocess.TimeoutExpired:
                    error_msg = f"Timeout lors de la création du schéma {service_name}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
                except Exception as e:
                    error_msg = f"Erreur lors de la création du schéma {service_name}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
            
            # Finalisation
            logger.info(f"🎉 Tous les schémas créés avec succès pour tenant {tenant_id}")
            tenant.schema_status = 'ready'
            tenant.schema_created_at = timezone.now()
            tenant.update_schema_progress(4, 4, "Configuration terminée ! Tous vos services sont prêts.")
            
        except Exception as e:
            logger.error(f"❌ Erreur globale lors de la création des schémas pour tenant {tenant_id}: {e}")
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                tenant.schema_status = 'error'
                tenant.schema_error = str(e)
                tenant.update_schema_progress(
                    0, 4, 
                    f"Erreur lors de la configuration: {str(e)}", 
                    "error"
                )
            except:
                pass  # Éviter les erreurs en cascade
    
    # Lancer le worker en arrière-plan
    thread = threading.Thread(target=schema_creation_worker)
    thread.daemon = True
    thread.start()
    
    logger.info(f"🚀 Tâche de création de schémas lancée en arrière-plan pour tenant {tenant_id}")

def retry_schema_creation(tenant_id: str):
    """
    Relance la création des schémas pour un tenant en erreur
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        if tenant.schema_status in ['error', 'pending']:
            logger.info(f"🔄 Relance de la création des schémas pour tenant {tenant_id}")
            
            # Réinitialiser le statut
            tenant.schema_status = 'pending'
            tenant.schema_error = ''
            tenant.schema_progress = {}
            tenant.save()
            
            # Relancer la création
            create_tenant_schemas_async(tenant_id)
            
            return True
        else:
            logger.warning(f"⚠️ Tenant {tenant_id} n'est pas en erreur, relance ignorée")
            return False
            
    except Tenant.DoesNotExist:
        logger.error(f"❌ Tenant {tenant_id} non trouvé pour la relance")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur lors de la relance pour tenant {tenant_id}: {e}")
        return False