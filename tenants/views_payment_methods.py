"""
Views pour la gestion des moyens de paiement
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Tenant, TenantPaymentMethod
from .serializers import TenantPaymentMethodSerializer

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def tenant_payment_methods(request):
    """
    Endpoint pour gérer les moyens de paiement d'un tenant
    GET: Récupérer tous les moyens de paiement actifs
    POST: Créer un nouveau moyen de paiement
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        if request.method == 'GET':
            # Récupérer tous les moyens de paiement actifs
            payment_methods = TenantPaymentMethod.objects.filter(
                tenant=tenant,
                is_active=True
            ).order_by('display_order', 'created_at')
            
            serializer = TenantPaymentMethodSerializer(payment_methods, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Créer un nouveau moyen de paiement
            serializer = TenantPaymentMethodSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(tenant=tenant)
                logger.info(f"Nouveau moyen de paiement créé pour tenant {tenant_id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant with id {tenant_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la gestion des moyens de paiement: {str(e)}")
        return Response(
            {"detail": f"Une erreur est survenue: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def tenant_payment_method_detail(request, payment_method_id):
    """
    Endpoint pour gérer un moyen de paiement spécifique
    GET: Récupérer les détails
    PUT: Mettre à jour
    DELETE: Supprimer
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        payment_method = TenantPaymentMethod.objects.get(
            id=payment_method_id,
            tenant=tenant
        )
        
        if request.method == 'GET':
            serializer = TenantPaymentMethodSerializer(payment_method)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = TenantPaymentMethodSerializer(
                payment_method, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Moyen de paiement {payment_method_id} mis à jour pour tenant {tenant_id}")
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            payment_method.delete()
            logger.info(f"Moyen de paiement {payment_method_id} supprimé pour tenant {tenant_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant with id {tenant_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except TenantPaymentMethod.DoesNotExist:
        return Response(
            {"detail": f"Payment method with id {payment_method_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la gestion du moyen de paiement: {str(e)}")
        return Response(
            {"detail": f"Une erreur est survenue: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_method_types(request):
    """
    Endpoint pour récupérer les types de moyens de paiement disponibles
    """
    types = [
        {
            'value': 'bank_transfer',
            'label': 'Virement bancaire',
            'description': 'Paiement par virement bancaire (IBAN, BIC)',
            'icon': 'building-bank',
            'default_style': {
                'background_color': '#e3f2fd',
                'text_color': '#1565c0',
                'border_color': '#90caf9'
            }
        },
        {
            'value': 'check',
            'label': 'Chèque',
            'description': 'Paiement par chèque bancaire',
            'icon': 'receipt',
            'default_style': {
                'background_color': '#f3e5f5',
                'text_color': '#7b1fa2',
                'border_color': '#ce93d8'
            }
        },
        {
            'value': 'cash',
            'label': 'Espèces',
            'description': 'Paiement en espèces',
            'icon': 'banknotes',
            'default_style': {
                'background_color': '#e8f5e8',
                'text_color': '#2e7d32',
                'border_color': '#a5d6a7'
            }
        },
        {
            'value': 'card',
            'label': 'Carte bancaire',
            'description': 'Paiement par carte bancaire',
            'icon': 'credit-card',
            'default_style': {
                'background_color': '#fff3e0',
                'text_color': '#ef6c00',
                'border_color': '#ffcc02'
            }
        }
    ]
    
    return Response(types)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_default_payment_methods(request):
    """
    Endpoint pour créer les moyens de paiement par défaut (Virement + Chèque)
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        # Vérifier si des moyens de paiement existent déjà
        existing_count = TenantPaymentMethod.objects.filter(tenant=tenant).count()
        if existing_count > 0:
            return Response(
                {"detail": "Des moyens de paiement existent déjà"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer le virement bancaire par défaut
        bank_transfer = TenantPaymentMethod.objects.create(
            tenant=tenant,
            method_type='bank_transfer',
            label='Virement bancaire',
            description='Effectuez votre paiement par virement bancaire',
            details={
                'iban': '',
                'bic': '',
                'bank_name': '',
                'account_holder': tenant.name
            },
            display_order=0,
            icon_name='building-bank',
            background_color='#e3f2fd',
            text_color='#1565c0',
            border_color='#90caf9'
        )
        
        # Créer le chèque par défaut
        check = TenantPaymentMethod.objects.create(
            tenant=tenant,
            method_type='check',
            label='Chèque',
            description='Envoyez votre chèque à l\'adresse suivante',
            details={
                'payable_to': tenant.name,
                'address': tenant.full_address,
                'instructions': 'Chèque à l\'ordre de ' + tenant.name
            },
            display_order=1,
            icon_name='receipt',
            background_color='#f3e5f5',
            text_color='#7b1fa2',
            border_color='#ce93d8'
        )
        
        # Sérialiser les résultats
        serializer = TenantPaymentMethodSerializer([bank_transfer, check], many=True)
        
        logger.info(f"Moyens de paiement par défaut créés pour tenant {tenant_id}")
        return Response(
            {
                "message": "Moyens de paiement par défaut créés avec succès",
                "payment_methods": serializer.data
            },
            status=status.HTTP_201_CREATED
        )
        
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant with id {tenant_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la création des moyens de paiement par défaut: {str(e)}")
        return Response(
            {"detail": f"Une erreur est survenue: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )