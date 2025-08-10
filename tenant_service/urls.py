"""
URL configuration for tenant_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def service_info(request):
    """Endpoint d'information sur le service"""
    return JsonResponse({
        "service": "tenant-service",
        "version": "1.0.0",
        "description": "Service de gestion des tenants pour l'architecture SOA",
        "endpoints": {
            "api": "/api/",
            "admin": "/admin/",
            "health": "/health/"
        }
    })

def health_check(request):
    """Endpoint de santé au niveau racine pour compatibilité SOA"""
    return JsonResponse({
        "service": "tenant-service",
        "status": "healthy",
        "version": "2.0.0"
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name='health_check_root'),
    path("", service_info, name='service_info'),
    path("api/", include('tenants.urls')),
]
