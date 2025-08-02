#!/usr/bin/env python3
"""
Script de test pour vérifier la fonctionnalité logo
"""
import os
import sys
import django
import requests
import json
import base64

# Configuration Django
sys.path.append('/mnt/d/beenaya-soa/soa/services/tenant-service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_service.settings')

try:
    django.setup()
    from tenants.models import Tenant, TenantSettings
    print("✅ Django configuré avec succès")
except Exception as e:
    print(f"❌ Erreur Django: {e}")
    sys.exit(1)

def test_logo_in_database():
    """Tester si des logos existent en base"""
    print("\n=== TEST: Logos en base de données ===")
    
    try:
        # Compter les tenants avec logo
        tenants_with_logo = TenantSettings.objects.exclude(logo_data='').count()
        total_tenants = TenantSettings.objects.count()
        
        print(f"📊 Total tenants: {total_tenants}")
        print(f"📸 Tenants avec logo: {tenants_with_logo}")
        
        # Afficher quelques exemples
        settings_with_logos = TenantSettings.objects.exclude(logo_data='')[:3]
        for i, setting in enumerate(settings_with_logos, 1):
            logo_size = len(setting.logo_data) if setting.logo_data else 0
            print(f"  {i}. Tenant {setting.tenant.name}: {logo_size} caractères de logo_data")
            
            # Vérifier si c'est un base64 valide
            if setting.logo_data.startswith('data:image/'):
                print(f"    ✅ Format base64 valide détecté")
            else:
                print(f"    ⚠️ Format inhabituel: {setting.logo_data[:50]}...")
                
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")

def test_api_endpoint():
    """Tester l'endpoint API"""
    print("\n=== TEST: Endpoint API ===")
    
    # Obtenir un tenant de test
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            print("❌ Aucun tenant trouvé")
            return
            
        print(f"🎯 Test avec tenant: {tenant.name} (ID: {tenant.id})")
        
        # Test GET
        url = "http://localhost:8001/tenants/current_tenant_info/"
        headers = {'X-Tenant-ID': str(tenant.id)}
        
        print(f"📡 GET {url}")
        print(f"📋 Headers: {headers}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logo_data = data.get('settings', {}).get('logo_data', '')
            logo_url = data.get('settings', {}).get('logo_url', '')
            
            print(f"🖼️ Logo URL: {logo_url}")
            print(f"📸 Logo data length: {len(logo_data)}")
            
            if logo_data:
                if logo_data.startswith('data:image/'):
                    print("✅ Logo data format valide (data:image/...)")
                else:
                    print(f"⚠️ Logo data format: {logo_data[:100]}...")
            else:
                print("📝 Aucune donnée logo trouvée")
        else:
            print(f"❌ Erreur API: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au service tenant (port 8001)")
    except Exception as e:
        print(f"❌ Erreur API: {e}")

def create_test_logo():
    """Créer un logo de test"""
    print("\n=== TEST: Création logo de test ===")
    
    try:
        tenant = Tenant.objects.first()
        if not tenant:
            print("❌ Aucun tenant trouvé")
            return
            
        # Créer un logo de test simple (pixel rouge en base64)
        test_logo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        # Obtenir ou créer les settings
        settings, created = TenantSettings.objects.get_or_create(tenant=tenant)
        settings.logo_data = test_logo
        settings.save()
        
        print(f"✅ Logo de test créé pour {tenant.name}")
        print(f"📸 Logo data: {test_logo[:50]}...")
        
        return tenant.id
        
    except Exception as e:
        print(f"❌ Erreur création logo: {e}")
        return None

if __name__ == "__main__":
    print("🧪 TESTS DE LA FONCTIONNALITÉ LOGO")
    print("=" * 50)
    
    # Test 1: Base de données
    test_logo_in_database()
    
    # Test 2: Créer un logo de test
    tenant_id = create_test_logo()
    
    # Test 3: API
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("🏁 Tests terminés")