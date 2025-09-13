#!/usr/bin/env python
"""
Script de test pour le service de géolocalisation et détection de devise
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_service.settings')
django.setup()

from tenants.services.geolocation import GeolocationService
from tenants.models import Tenant, TenantSettings


def test_geolocation_detection():
    """Test de détection géolocalisation"""
    print("Test de détection de géolocalisation")
    print("=" * 50)
    
    # IPs de test (vous pouvez utiliser vos propres IPs ou des IPs publiques connues)
    test_ips = [
        "8.8.8.8",         # Google DNS (US)
        "1.1.1.1",         # Cloudflare (US)
        "46.105.14.1",     # OVH France
        "105.235.196.20",  # IP Maroc (exemple)
        "127.0.0.1"        # Localhost (fallback)
    ]
    
    for ip in test_ips:
        print(f"\n[TEST] IP: {ip}")
        try:
            location = GeolocationService.detect_location_from_ip(ip)
            if location:
                print(f"  [OK] Pays: {location['country_name']} ({location['country_code']})")
                print(f"  [OK] Devise: {location['currency']} ({location['currency_symbol']})")
                print(f"  [OK] Locale: {location['locale']}")
                print(f"  [OK] Timezone: {location['timezone']}")
                print(f"  [OK] Service: {location['detection_service']}")
                print(f"  [OK] Confiance: {location['confidence']}")
            else:
                print(f"  [ERROR] Aucune données détectées")
        except Exception as e:
            print(f"  [ERROR] Erreur: {str(e)}")


def test_country_currency_mapping():
    """Test du mapping pays -> devise"""
    print("\n\n💱 Test du mapping pays -> devise")
    print("=" * 50)
    
    supported_countries = GeolocationService.get_supported_countries()
    
    print(f"📊 Nombre de pays supportés: {len(supported_countries)}")
    print("\nListe des pays et devises:")
    
    for country in supported_countries:
        print(f"  {country['code']} - {country['name']}: "
              f"{country['currency']} ({country['currency_symbol']})")


def test_tenant_configuration():
    """Test de configuration automatique d'un tenant"""
    print("\n\n🏢 Test de configuration automatique tenant")
    print("=" * 50)
    
    # Simuler des données de géolocalisation
    mock_location_data = {
        'country_code': 'FR',
        'country_name': 'France',
        'city': 'Paris',
        'currency': 'EUR',
        'currency_symbol': '€',
        'currency_position': 'after',
        'locale': 'fr-FR',
        'timezone': 'Europe/Paris',
        'language': 'fr',
        'detection_service': 'mock',
        'confidence': 'high'
    }
    
    # Créer un tenant de test
    try:
        # Supprimer le tenant de test s'il existe déjà
        Tenant.objects.filter(name="Test Geolocation").delete()
        
        tenant = Tenant.objects.create(
            name="Test Geolocation",
            email="test@geolocation.com"
        )
        print(f"✅ Tenant créé: {tenant.name}")
        
        # Appliquer la configuration géolocalisation
        success, message = GeolocationService.apply_location_to_tenant(tenant, mock_location_data)
        
        if success:
            print(f"✅ Configuration appliquée: {message}")
            
            # Vérifier les settings
            settings = tenant.settings
            print(f"  💰 Devise configurée: {settings.currency} ({settings.currency_symbol})")
            print(f"  🌐 Locale: {settings.locale}")
            print(f"  ⏰ Timezone: {settings.timezone}")
            print(f"  🗣️ Langue: {settings.language}")
            print(f"  🤖 Auto-détectée: {settings.currency_auto_detected}")
            
        else:
            print(f"❌ Erreur de configuration: {message}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")


def test_currency_formatting():
    """Test des différents formats de devise"""
    print("\n\n💰 Test des formats de devise")
    print("=" * 50)
    
    test_amount = 1234.56
    currencies = ['MAD', 'EUR', 'USD', 'GBP', 'CHF']
    
    for currency_code in currencies:
        # Trouver la configuration de cette devise
        supported_countries = GeolocationService.get_supported_countries()
        currency_info = None
        
        for country in supported_countries:
            if country['currency'] == currency_code:
                currency_info = country
                break
        
        if currency_info:
            symbol = currency_info['currency_symbol']
            position = currency_info['currency_position']
            
            if position == 'before':
                formatted = f"{symbol}{test_amount:,.2f}"
            else:
                formatted = f"{test_amount:,.2f} {symbol}"
            
            print(f"  {currency_code}: {formatted}")


if __name__ == "__main__":
    print("🚀 Tests du système de géolocalisation et devise Beenaya SOA")
    print("=" * 60)
    
    # Exécuter tous les tests
    test_geolocation_detection()
    test_country_currency_mapping()
    test_tenant_configuration()
    test_currency_formatting()
    
    print("\n\n✅ Tests terminés !")
    print("=" * 60)