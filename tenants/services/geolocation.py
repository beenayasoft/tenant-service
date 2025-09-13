"""
Service de géolocalisation et détection automatique de devise
Détecte le pays et la devise basés sur l'adresse IP du client
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)


class GeolocationService:
    """
    Service pour détecter la localisation géographique et configurer automatiquement
    la devise et les paramètres régionaux du tenant
    """
    
    # Mapping complet pays → devise avec informations de formatage
    COUNTRY_CURRENCY_MAP = {
        # Afrique
        'MA': {
            'currency': 'MAD',
            'currency_symbol': 'DH',
            'currency_position': 'after',
            'locale': 'ar-MA',
            'timezone': 'Africa/Casablanca',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },
        'DZ': {
            'currency': 'DZD',
            'currency_symbol': 'DA',
            'currency_position': 'after',
            'locale': 'ar-DZ',
            'timezone': 'Africa/Algiers',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },
        'TN': {
            'currency': 'TND',
            'currency_symbol': 'DT',
            'currency_position': 'after',
            'locale': 'ar-TN',
            'timezone': 'Africa/Tunis',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },
        'EG': {
            'currency': 'EGP',
            'currency_symbol': 'E£',
            'currency_position': 'before',
            'locale': 'ar-EG',
            'timezone': 'Africa/Cairo',
            'date_format': 'DD/MM/YYYY',
            'language': 'ar'
        },
        'SN': {
            'currency': 'XOF',
            'currency_symbol': 'CFA',
            'currency_position': 'after',
            'locale': 'fr-SN',
            'timezone': 'Africa/Dakar',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },
        'CI': {
            'currency': 'XOF',
            'currency_symbol': 'CFA',
            'currency_position': 'after',
            'locale': 'fr-CI',
            'timezone': 'Africa/Abidjan',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },

        # Europe
        'FR': {
            'currency': 'EUR',
            'currency_symbol': '€',
            'currency_position': 'after',
            'locale': 'fr-FR',
            'timezone': 'Europe/Paris',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },
        'DE': {
            'currency': 'EUR',
            'currency_symbol': '€',
            'currency_position': 'after',
            'locale': 'de-DE',
            'timezone': 'Europe/Berlin',
            'date_format': 'DD.MM.YYYY',
            'language': 'de'
        },
        'IT': {
            'currency': 'EUR',
            'currency_symbol': '€',
            'currency_position': 'after',
            'locale': 'it-IT',
            'timezone': 'Europe/Rome',
            'date_format': 'DD/MM/YYYY',
            'language': 'it'
        },
        'ES': {
            'currency': 'EUR',
            'currency_symbol': '€',
            'currency_position': 'after',
            'locale': 'es-ES',
            'timezone': 'Europe/Madrid',
            'date_format': 'DD/MM/YYYY',
            'language': 'es'
        },
        'CH': {
            'currency': 'CHF',
            'currency_symbol': 'CHF',
            'currency_position': 'after',
            'locale': 'fr-CH',
            'timezone': 'Europe/Zurich',
            'date_format': 'DD.MM.YYYY',
            'language': 'fr'
        },
        'BE': {
            'currency': 'EUR',
            'currency_symbol': '€',
            'currency_position': 'after',
            'locale': 'fr-BE',
            'timezone': 'Europe/Brussels',
            'date_format': 'DD/MM/YYYY',
            'language': 'fr'
        },
        'GB': {
            'currency': 'GBP',
            'currency_symbol': '£',
            'currency_position': 'before',
            'locale': 'en-GB',
            'timezone': 'Europe/London',
            'date_format': 'DD/MM/YYYY',
            'language': 'en'
        },

        # Amérique du Nord
        'US': {
            'currency': 'USD',
            'currency_symbol': '$',
            'currency_position': 'before',
            'locale': 'en-US',
            'timezone': 'America/New_York',
            'date_format': 'MM/DD/YYYY',
            'language': 'en'
        },
        'CA': {
            'currency': 'CAD',
            'currency_symbol': 'CAD',
            'currency_position': 'before',
            'locale': 'en-CA',
            'timezone': 'America/Toronto',
            'date_format': 'DD/MM/YYYY',
            'language': 'en'
        },

        # Moyen-Orient
        'AE': {
            'currency': 'AED',
            'currency_symbol': 'AED',
            'currency_position': 'after',
            'locale': 'ar-AE',
            'timezone': 'Asia/Dubai',
            'date_format': 'DD/MM/YYYY',
            'language': 'ar'
        },
        'SA': {
            'currency': 'SAR',
            'currency_symbol': 'ر.س',
            'currency_position': 'after',
            'locale': 'ar-SA',
            'timezone': 'Asia/Riyadh',
            'date_format': 'DD/MM/YYYY',
            'language': 'ar'
        }
    }

    @classmethod
    def detect_location_from_ip(cls, ip_address: str) -> Optional[Dict]:
        """
        Détecte la localisation géographique basée sur l'adresse IP
        
        Args:
            ip_address: Adresse IP du client
            
        Returns:
            Dict avec informations de localisation ou None si échec
        """
        if not ip_address or ip_address == '127.0.0.1':
            logger.warning("IP locale détectée, utilisation des valeurs par défaut")
            return cls._get_default_location()
        
        # Essayer plusieurs services de géolocalisation
        services = [
            cls._detect_with_ipapi,
            cls._detect_with_ipinfo,
            cls._detect_with_ipgeolocation
        ]
        
        for service in services:
            try:
                result = service(ip_address)
                if result:
                    logger.info(f"Géolocalisation réussie avec {service.__name__}")
                    return result
            except Exception as e:
                logger.error(f"Erreur avec {service.__name__}: {str(e)}")
                continue
        
        logger.warning("Tous les services de géolocalisation ont échoué")
        return cls._get_default_location()

    @classmethod
    def _detect_with_ipapi(cls, ip_address: str) -> Optional[Dict]:
        """Détection avec ipapi.co (service gratuit)"""
        try:
            response = requests.get(
                f'https://ipapi.co/{ip_address}/json/',
                timeout=5,
                headers={'User-Agent': 'BeenayaSOA/1.0'}
            )
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Erreur ipapi.co: {data['error']}")
                return None
            
            return cls._format_location_data({
                'country_code': data.get('country_code'),
                'country_name': data.get('country_name'),
                'city': data.get('city'),
                'region': data.get('region'),
                'currency': data.get('currency'),
                'timezone': data.get('timezone'),
                'languages': data.get('languages', '').split(','),
                'ip': ip_address,
                'service': 'ipapi.co'
            })
            
        except Exception as e:
            logger.error(f"Erreur ipapi.co: {str(e)}")
            return None

    @classmethod
    def _detect_with_ipinfo(cls, ip_address: str) -> Optional[Dict]:
        """Détection avec ipinfo.io (service gratuit avec limite)"""
        try:
            response = requests.get(
                f'https://ipinfo.io/{ip_address}/json',
                timeout=5,
                headers={'User-Agent': 'BeenayaSOA/1.0'}
            )
            response.raise_for_status()
            data = response.json()
            
            return cls._format_location_data({
                'country_code': data.get('country'),
                'country_name': cls._get_country_name_from_code(data.get('country')),
                'city': data.get('city'),
                'region': data.get('region'),
                'timezone': data.get('timezone'),
                'ip': ip_address,
                'service': 'ipinfo.io'
            })
            
        except Exception as e:
            logger.error(f"Erreur ipinfo.io: {str(e)}")
            return None

    @classmethod
    def _detect_with_ipgeolocation(cls, ip_address: str) -> Optional[Dict]:
        """Détection avec ipgeolocation.io (nécessite clé API)"""
        api_key = getattr(settings, 'IPGEOLOCATION_API_KEY', None)
        if not api_key:
            return None
            
        try:
            response = requests.get(
                f'https://api.ipgeolocation.io/ipgeo',
                params={'apiKey': api_key, 'ip': ip_address},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            return cls._format_location_data({
                'country_code': data.get('country_code2'),
                'country_name': data.get('country_name'),
                'city': data.get('city'),
                'region': data.get('state_prov'),
                'currency': data.get('currency', {}).get('code'),
                'timezone': data.get('time_zone', {}).get('name'),
                'languages': data.get('languages', '').split(','),
                'ip': ip_address,
                'service': 'ipgeolocation.io'
            })
            
        except Exception as e:
            logger.error(f"Erreur ipgeolocation.io: {str(e)}")
            return None

    @classmethod
    def _format_location_data(cls, raw_data: Dict) -> Dict:
        """
        Formate et enrichit les données de localisation avec les informations de devise
        """
        country_code = raw_data.get('country_code', '').upper()
        
        # Obtenir la configuration de devise pour ce pays
        currency_config = cls.COUNTRY_CURRENCY_MAP.get(country_code, cls.COUNTRY_CURRENCY_MAP['MA'])
        
        return {
            'country_code': country_code,
            'country_name': raw_data.get('country_name', ''),
            'city': raw_data.get('city', ''),
            'region': raw_data.get('region', ''),
            'currency': currency_config['currency'],
            'currency_symbol': currency_config['currency_symbol'],
            'currency_position': currency_config['currency_position'],
            'locale': currency_config['locale'],
            'timezone': currency_config['timezone'],
            'date_format': currency_config['date_format'],
            'language': currency_config['language'],
            'ip_address': raw_data.get('ip'),
            'detection_service': raw_data.get('service'),
            'detected_at': timezone.now().isoformat(),
            'confidence': 'high' if country_code in cls.COUNTRY_CURRENCY_MAP else 'low'
        }

    @classmethod
    def _get_default_location(cls) -> Dict:
        """Retourne la configuration par défaut (Maroc)"""
        return cls._format_location_data({
            'country_code': 'MA',
            'country_name': 'Maroc',
            'city': 'Casablanca',
            'region': 'Grand Casablanca',
            'ip': '127.0.0.1',
            'service': 'default'
        })

    @classmethod
    def _get_country_name_from_code(cls, country_code: str) -> str:
        """Convertit code pays vers nom de pays"""
        mapping = {
            'MA': 'Maroc',
            'FR': 'France',
            'DE': 'Allemagne',
            'IT': 'Italie',
            'ES': 'Espagne',
            'CH': 'Suisse',
            'BE': 'Belgique',
            'GB': 'Royaume-Uni',
            'US': 'États-Unis',
            'CA': 'Canada',
            'DZ': 'Algérie',
            'TN': 'Tunisie',
            'EG': 'Égypte',
            'SN': 'Sénégal',
            'CI': 'Côte d\'Ivoire',
            'AE': 'Émirats Arabes Unis',
            'SA': 'Arabie Saoudite'
        }
        return mapping.get(country_code.upper(), country_code)

    @classmethod
    def get_client_ip(cls, request) -> str:
        """
        Extrait l'adresse IP réelle du client depuis la requête
        """
        # Headers possibles pour l'IP réelle (derrière proxy/load balancer)
        headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_CF_CONNECTING_IP',  # Cloudflare
            'HTTP_X_FORWARDED',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED',
            'REMOTE_ADDR'
        ]
        
        for header in headers:
            ip = request.META.get(header)
            if ip:
                # X-Forwarded-For peut contenir plusieurs IPs séparées par des virgules
                ip = ip.split(',')[0].strip()
                if ip and ip != 'unknown':
                    return ip
        
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    @classmethod
    def apply_location_to_tenant(cls, tenant, location_data: Dict) -> Tuple[bool, str]:
        """
        Applique les données de géolocalisation au tenant et ses settings
        
        Args:
            tenant: Instance du modèle Tenant
            location_data: Données de localisation détectées
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            # Mettre à jour les informations de géolocalisation du tenant
            tenant.detected_location = location_data
            tenant.location_detection_date = timezone.now()
            
            # Mettre à jour le pays si non défini ou si auto-détection activée
            if not tenant.country or tenant.country == 'France':  # Valeur par défaut
                tenant.country = location_data.get('country_name', 'Maroc')
                tenant.country_code = location_data.get('country_code', 'MA')
            
            # Mettre à jour la ville si non définie
            if not tenant.city:
                tenant.city = location_data.get('city', '')
            
            tenant.save()
            
            # Mettre à jour ou créer les settings du tenant
            settings, created = tenant.settings if hasattr(tenant, 'settings') else None, False
            if not settings:
                from tenants.models import TenantSettings
                settings, created = TenantSettings.objects.get_or_create(tenant=tenant)
            
            # Appliquer la configuration de devise automatiquement
            settings.currency = location_data.get('currency', 'MAD')
            settings.currency_symbol = location_data.get('currency_symbol', 'DH')
            settings.currency_position = location_data.get('currency_position', 'after')
            settings.locale = location_data.get('locale', 'fr-MA')
            settings.timezone = location_data.get('timezone', 'Africa/Casablanca')
            settings.date_format = location_data.get('date_format', 'DD/MM/YYYY')
            settings.language = location_data.get('language', 'fr')
            settings.currency_auto_detected = True
            settings.currency_detection_date = timezone.now()
            
            settings.save()
            
            logger.info(f"Configuration automatique appliquée au tenant {tenant.name}: "
                       f"Pays={tenant.country}, Devise={settings.currency}")
            
            return True, "Configuration automatique réussie"
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la géolocalisation: {str(e)}")
            return False, f"Erreur: {str(e)}"

    @classmethod
    def get_supported_countries(cls) -> list:
        """Retourne la liste des pays supportés avec leurs informations"""
        return [
            {
                'code': code,
                'name': cls._get_country_name_from_code(code),
                **config
            }
            for code, config in cls.COUNTRY_CURRENCY_MAP.items()
        ]