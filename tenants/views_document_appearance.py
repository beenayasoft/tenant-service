"""
Views pour la gestion de l'apparence des documents
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Tenant, TenantDocumentAppearance
from .serializers import TenantDocumentAppearanceSerializer

logger = logging.getLogger(__name__)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([AllowAny])
def tenant_document_appearance(request):
    """
    Endpoint pour gérer l'apparence des documents d'un tenant
    GET: Récupérer les paramètres d'apparence
    PUT/PATCH: Mettre à jour les paramètres d'apparence
    """
    logger.info(f"Appel à tenant_document_appearance - Méthode: {request.method}")
    
    tenant_id = request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"detail": "X-Tenant-ID header is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Nettoyer et valider le tenant ID
    import re
    
    # Supprimer les caractères invisibles et prendre le premier UUID en cas de duplication
    cleaned_tenant_id = re.sub(r'[\xa0\s\u00A0\u2000-\u200B\uFEFF]', '', tenant_id)
    if ',' in cleaned_tenant_id:
        cleaned_tenant_id = cleaned_tenant_id.split(',')[0]
    
    # Valider le format UUID
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, cleaned_tenant_id, re.IGNORECASE):
        logger.error(f"Tenant ID invalide reçu: '{tenant_id}' -> nettoyé: '{cleaned_tenant_id}'")
        return Response(
            {"detail": f"Format UUID invalide pour X-Tenant-ID: {cleaned_tenant_id}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    tenant_id = cleaned_tenant_id
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        # Récupérer ou créer la configuration d'apparence
        document_appearance, created = TenantDocumentAppearance.objects.get_or_create(
            tenant=tenant
        )
        
        if created:
            logger.info(f"Configuration d'apparence créée pour tenant {tenant_id}")
        
        # GET: Récupérer les paramètres
        if request.method == 'GET':
            serializer = TenantDocumentAppearanceSerializer(document_appearance)
            return Response(serializer.data)
        
        # PUT/PATCH: Mettre à jour les paramètres
        elif request.method in ['PUT', 'PATCH']:
            is_partial = request.method == 'PATCH'
            
            # Log détaillé des données reçues
            logger.info(f"🔄 PATCH/PUT request data for tenant {tenant_id}:")
            logger.info(f"🔄 Raw request.data: {request.data}")
            logger.info(f"🔄 Request headers: {dict(request.headers)}")
            
            serializer = TenantDocumentAppearanceSerializer(
                document_appearance, 
                data=request.data, 
                partial=is_partial
            )
            
            if serializer.is_valid():
                # Log des données avant sauvegarde
                logger.info(f"🔄 Serializer validated_data: {serializer.validated_data}")
                logger.info(f"🔄 Current object before save - show_client_address: {document_appearance.show_client_address}, show_project_info: {document_appearance.show_project_info}")
                
                saved_instance = serializer.save()
                
                # Log après sauvegarde
                logger.info(f"✅ Configuration d'apparence mise à jour pour tenant {tenant_id}")
                logger.info(f"✅ After save - show_client_address: {saved_instance.show_client_address}, show_project_info: {saved_instance.show_project_info}")
                
                return Response(serializer.data)
            else:
                logger.error(f"❌ Erreurs de validation: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Tenant.DoesNotExist:
        return Response(
            {"detail": f"Tenant with id {tenant_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Erreur lors de la gestion de l'apparence: {str(e)}")
        return Response(
            {"detail": f"Une erreur est survenue: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def document_appearance_defaults(request):
    """
    Endpoint pour récupérer les valeurs par défaut des paramètres d'apparence
    Utile pour initialiser le formulaire frontend
    """
    defaults = {
        'document_template': 'modern',
        'primary_color': '#1B333F',
        'show_logo': True,
        'logo_data': '',
        'logo_size': 100,
        'logo_position_type': 'left',
        'logo_center_in_header': False,
        'show_company_name': True,
        'show_company_address': True,
        'show_company_email': True,
        'show_company_phone': True,
        'show_company_website': True,
        'show_company_siret': True,
        'show_company_ice': True,
        'show_client_address': True,
        'show_project_info': True,
        'show_notes': True,
        'show_payment_terms': True,
        'show_bank_details': True,
        'show_signature_area': True,
        'logo_position': 'left',  # Maintenu pour compatibilité
        'font_family': 'Arial',
        'font_size': 11,
        'line_spacing': 1.5,
        'margin_top': 25,
        'margin_right': 20,
        'margin_bottom': 25,
        'margin_left': 20,
        'show_payment_details': True,
        'show_legal_mentions': True,
        'table_header_color': '#f8f9fa',
        'table_alternate_color': '#f2f2f2',
        # Nouveaux champs pour les styles de tableaux
        'table_border_style': 'straight',
        'table_border_horizontal': True,
        'table_border_vertical': True,
        'table_border_width': 1,
        'table_border_color': '#dee2e6',
        'section_contrast': False,
        'section_contrast_color': '#f8f9fa',
        'show_section_subtotals': True,
        'table_row_padding': 8,
        'table_column_spacing': 12,
        # Nouveaux champs pour les moyens de paiement
        'show_payment_methods': True,
        'payment_methods_title': 'Moyens de paiement',
        'payment_methods_layout': 'horizontal',
        'payment_methods_style': 'modern',
        'header_text': '',
        'footer_text': '',
        'legal_mentions': ''
    }
    
    return Response(defaults)


@api_view(['GET'])
@permission_classes([AllowAny])
def document_template_presets(request):
    """
    Endpoint pour récupérer les modèles prédéfinis complets
    Chaque modèle contient toute la configuration d'apparence
    """
    presets = {
        'modern': {
            'name': 'Moderne',
            'description': 'Design moderne avec couleurs vives et espacement généreux',
            'config': {
                'document_template': 'modern',
                'primaryColor': '#1B333F',
                'table_header_color': '#f8f9fa',
                'table_alternate_color': '#f2f2f2',
                'show_logo': True,
                'show_company_name': True,
                'show_company_address': True,
                'show_company_email': True,
                'show_company_phone': True,
                'show_company_website': True,
                'show_company_siret': True,
                'show_company_ice': True,
                'show_client_address': True,
                'show_project_info': True,
                'show_notes': True,
                'show_payment_terms': True,
                'show_bank_details': True,
                'show_signature_area': True,
                'logo_position': 'left',
                'font_family': 'Arial',
                'font_size': 11,
                'line_spacing': 1.5,
                'margin_top': 25,
                'margin_right': 20,
                'margin_bottom': 25,
                'margin_left': 20,
                'show_payment_details': True,
                'show_legal_mentions': True,
            }
        },
        'classic': {
            'name': 'Classique',
            'description': 'Style traditionnel sobre et professionnel',
            'config': {
                'document_template': 'classic',
                'primaryColor': '#2C3E50',
                'table_header_color': '#ecf0f1',
                'table_alternate_color': '#f8f9fa',
                'show_logo': True,
                'show_company_name': True,
                'show_company_address': True,
                'show_company_email': True,
                'show_company_phone': True,
                'show_company_website': True,
                'show_company_siret': True,
                'show_company_ice': True,
                'show_client_address': True,
                'show_project_info': True,
                'show_notes': True,
                'show_payment_terms': True,
                'show_bank_details': True,
                'show_signature_area': True,
                'logo_position': 'left',
                'font_family': 'Times New Roman',
                'font_size': 10,
                'line_spacing': 1.2,
                'margin_top': 30,
                'margin_right': 25,
                'margin_bottom': 30,
                'margin_left': 25,
                'show_payment_details': True,
                'show_legal_mentions': True,
            }
        },
        'minimal': {
            'name': 'Minimal',
            'description': 'Design épuré et minimaliste',
            'config': {
                'document_template': 'minimal',
                'primaryColor': '#34495E',
                'table_header_color': '#ffffff',
                'table_alternate_color': '#f9f9f9',
                'show_logo': False,
                'show_client_address': True,
                'show_project_info': False,
                'show_notes': False,
                'show_payment_terms': True,
                'show_bank_details': False,
                'show_signature_area': True,
                'logo_position': 'center',
                'font_family': 'Helvetica',
                'font_size': 9,
                'line_spacing': 1.1,
                'margin_top': 20,
                'margin_right': 15,
                'margin_bottom': 20,
                'margin_left': 15,
                'show_payment_details': False,
                'show_legal_mentions': False,
            }
        },
        'elegant': {
            'name': 'Élégant',
            'description': 'Design élégant avec des accents colorés',
            'config': {
                'document_template': 'elegant',
                'primaryColor': '#8E44AD',
                'table_header_color': '#f4f2f7',
                'table_alternate_color': '#faf9fc',
                'show_logo': True,
                'show_company_name': True,
                'show_company_address': True,
                'show_company_email': True,
                'show_company_phone': True,
                'show_company_website': True,
                'show_company_siret': True,
                'show_company_ice': True,
                'show_client_address': True,
                'show_project_info': True,
                'show_notes': True,
                'show_payment_terms': True,
                'show_bank_details': True,
                'show_signature_area': True,
                'logo_position': 'right',
                'font_family': 'Georgia',
                'font_size': 11,
                'line_spacing': 1.4,
                'margin_top': 28,
                'margin_right': 22,
                'margin_bottom': 28,
                'margin_left': 22,
                'show_payment_details': True,
                'show_legal_mentions': True,
            }
        },
        'corporate': {
            'name': 'Corporate',
            'description': 'Style professionnel pour les grandes entreprises',
            'config': {
                'document_template': 'corporate',
                'primaryColor': '#1ABC9C',
                'table_header_color': '#e8f6f3',
                'table_alternate_color': '#f4fdf9',
                'show_logo': True,
                'show_company_name': True,
                'show_company_address': True,
                'show_company_email': True,
                'show_company_phone': True,
                'show_company_website': True,
                'show_company_siret': True,
                'show_company_ice': True,
                'show_client_address': True,
                'show_project_info': True,
                'show_notes': True,
                'show_payment_terms': True,
                'show_bank_details': True,
                'show_signature_area': True,
                'logo_position': 'left',
                'font_family': 'Calibri',
                'font_size': 10,
                'line_spacing': 1.3,
                'margin_top': 35,
                'margin_right': 30,
                'margin_bottom': 35,
                'margin_left': 30,
                'show_payment_details': True,
                'show_legal_mentions': True,
            }
        }
    }
    
    return Response(presets)


@api_view(['GET'])
@permission_classes([AllowAny])
def document_template_choices(request):
    """
    Endpoint pour récupérer les choix de templates disponibles
    """
    templates = [
        {'value': 'modern', 'label': 'Moderne'},
        {'value': 'classic', 'label': 'Classique'},
        {'value': 'minimal', 'label': 'Minimal'},
    ]
    
    return Response(templates)


@api_view(['GET'])
@permission_classes([AllowAny])
def color_presets(request):
    """
    Endpoint pour récupérer les couleurs prédéfinies
    """
    presets = [
        {'name': 'Bleu Beenaya', 'value': '#1B333F'},
        {'name': 'Bleu Roi', 'value': '#1E40AF'},
        {'name': 'Vert Émeraude', 'value': '#047857'},
        {'name': 'Rouge Rubis', 'value': '#B91C1C'},
        {'name': 'Violet Améthyste', 'value': '#7E22CE'},
        {'name': 'Orange Mandarine', 'value': '#C2410C'},
    ]
    
    return Response(presets)


@api_view(['GET'])
@permission_classes([AllowAny])
def logo_position_choices(request):
    """
    Endpoint pour récupérer les choix de position du logo
    """
    positions = [
        {
            'value': 'left',
            'label': 'À gauche',
            'description': 'Le logo sera affiché à gauche, les informations d\'entreprise à côté'
        },
        {
            'value': 'top',
            'label': 'En haut',
            'description': 'Le logo sera affiché en haut, les informations d\'entreprise en dessous'
        },
        {
            'value': 'header',
            'label': 'Dans l\'en-tête',
            'description': 'Le logo sera intégré dans l\'en-tête du document'
        }
    ]
    
    return Response(positions)


@api_view(['GET'])
@permission_classes([AllowAny])
def table_style_choices(request):
    """
    Endpoint pour récupérer les choix de styles de tableaux
    """
    styles = {
        'border_styles': [
            {
                'value': 'straight',
                'label': 'Bordures droites',
                'description': 'Bordures classiques avec angles droits'
            },
            {
                'value': 'rounded',
                'label': 'Bordures arrondies',
                'description': 'Bordures avec angles arrondis pour un aspect moderne'
            }
        ],
        'predefined_styles': {
            'modern': {
                'name': 'Style moderne',
                'description': 'Bordures arrondies, sections contrastées',
                'config': {
                    'table_border_style': 'rounded',
                    'table_border_horizontal': True,
                    'table_border_vertical': False,
                    'table_border_width': 1,
                    'section_contrast': True,
                    'table_row_padding': 12,
                    'table_column_spacing': 16
                }
            },
            'classic': {
                'name': 'Style classique',
                'description': 'Bordures droites, tableau complet',
                'config': {
                    'table_border_style': 'straight',
                    'table_border_horizontal': True,
                    'table_border_vertical': True,
                    'table_border_width': 1,
                    'section_contrast': False,
                    'table_row_padding': 8,
                    'table_column_spacing': 12
                }
            },
            'minimal': {
                'name': 'Style minimal',
                'description': 'Bordures horizontales uniquement',
                'config': {
                    'table_border_style': 'straight',
                    'table_border_horizontal': True,
                    'table_border_vertical': False,
                    'table_border_width': 1,
                    'section_contrast': False,
                    'table_row_padding': 6,
                    'table_column_spacing': 8
                }
            }
        }
    }
    
    return Response(styles)