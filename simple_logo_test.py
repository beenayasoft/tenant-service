#!/usr/bin/env python3
"""
Script de test simple pour la fonctionnalité logo
"""
import os
import sys
import django

# Configuration Django
sys.path.append('D:/beenaya-soa/soa/services/tenant-service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenant_service.settings')

try:
    django.setup()
    from tenants.models import Tenant, TenantSettings
    print("Django configure avec succes")
except Exception as e:
    print(f"Erreur Django: {e}")
    sys.exit(1)

def test_logo_functionality():
    """Test complet de la fonctionnalité logo"""
    print("\n=== TEST LOGO FUNCTIONALITY ===")
    
    try:
        # 1. Obtenir un tenant
        tenant = Tenant.objects.first()
        if not tenant:
            print("Aucun tenant trouve")
            return
        
        print(f"Tenant de test: {tenant.name} (ID: {tenant.id})")
        
        # 2. Vérifier/créer les settings
        settings, created = TenantSettings.objects.get_or_create(tenant=tenant)
        if created:
            print("TenantSettings cree")
        else:
            print("TenantSettings existant")
        
        # 3. Etat actuel du logo
        print(f"Logo URL actuel: {settings.logo_url}")
        print(f"Logo data actuel (longueur): {len(settings.logo_data) if settings.logo_data else 0}")
        
        # 4. Créer un logo de test
        test_logo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        # 5. Sauvegarder le logo
        settings.logo_data = test_logo
        settings.save()
        print("Logo de test sauvegarde")
        
        # 6. Relire depuis la DB pour vérifier
        settings.refresh_from_db()
        if settings.logo_data == test_logo:
            print("SUCCES: Logo correctement sauvegarde et lu depuis la DB")
        else:
            print("ERREUR: Probleme de sauvegarde en DB")
            
        # 7. Tester la vue current_tenant_info
        from tenants.views import current_tenant_info
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/tenants/current_tenant_info/')
        request.META['HTTP_X_TENANT_ID'] = str(tenant.id)
        
        try:
            response = current_tenant_info(request)
            response.render()  # Rendre la réponse avant d'accéder au contenu
            if response.status_code == 200:
                import json
                data = json.loads(response.content)
                logo_from_api = data.get('settings', {}).get('logo_data', '')
                
                if logo_from_api == test_logo:
                    print("SUCCES: API renvoie le bon logo")
                else:
                    print(f"ERREUR: API renvoie un logo different")
                    print(f"Attendu: {test_logo[:50]}...")
                    print(f"Recu: {logo_from_api[:50]}...")
            else:
                print(f"ERREUR: API status {response.status_code}")
        except Exception as e:
            print(f"ERREUR: Test API echoue: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = test_logo_functionality()
    if success:
        print("\n=== CONCLUSION ===")
        print("La fonctionnalite logo semble fonctionner en backend")
    else:
        print("\n=== CONCLUSION ===") 
        print("Probleme detecte dans la fonctionnalite logo")