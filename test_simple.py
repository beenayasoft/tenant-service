#!/usr/bin/env python
"""
Script de test simple pour le service de géolocalisation
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_service.settings')
django.setup()

from tenants.services.geolocation import GeolocationService

def test_simple():
    print("Test simple du service de géolocalisation")
    print("=" * 40)
    
    # Test avec une IP française connue
    test_ip = "46.105.14.1"  # OVH France
    
    print(f"Test avec IP: {test_ip}")
    
    try:
        location = GeolocationService.detect_location_from_ip(test_ip)
        
        if location:
            print("RESULTAT DETECTION:")
            print(f"  Pays: {location['country_name']}")
            print(f"  Code: {location['country_code']}")
            print(f"  Devise: {location['currency']}")
            print(f"  Symbole: {location['currency_symbol']}")
            print(f"  Service: {location['detection_service']}")
        else:
            print("Aucune donnée détectée")
            
    except Exception as e:
        print(f"Erreur: {str(e)}")
    
    print("\nTest mapping pays supportés:")
    countries = GeolocationService.get_supported_countries()
    print(f"Nombre de pays: {len(countries)}")
    
    for i, country in enumerate(countries[:5]):  # Afficher seulement les 5 premiers
        print(f"  {country['code']}: {country['currency']}")
    
    print("Test terminé!")

if __name__ == "__main__":
    test_simple()