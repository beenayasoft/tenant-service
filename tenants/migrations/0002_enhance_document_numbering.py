# Generated migration for enhanced document numbering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        # Ajouter les nouveaux champs
        migrations.AddField(
            model_name='tenantdocumentnumbering',
            name='include_day',
            field=models.BooleanField(default=False, verbose_name='Inclure le jour'),
        ),
        migrations.AddField(
            model_name='tenantdocumentnumbering',
            name='date_format',
            field=models.CharField(
                choices=[
                    ('YYYY-MM-DD', '2024-07-23'),
                    ('YYYY-MM', '2024-07'),
                    ('YYYY', '2024'),
                    ('DD-MM-YYYY', '23-07-2024'),
                    ('MM-DD-YYYY', '07-23-2024')
                ],
                default='YYYY-MM-DD',
                help_text="Format d'affichage de la date",
                max_length=20,
                verbose_name='Format de date'
            ),
        ),
        migrations.AddField(
            model_name='tenantdocumentnumbering',
            name='separator',
            field=models.CharField(
                default='-',
                help_text='Caractère de séparation entre les parties',
                max_length=3,
                verbose_name='Séparateur'
            ),
        ),
        migrations.AddField(
            model_name='tenantdocumentnumbering',
            name='custom_format',
            field=models.CharField(
                blank=True,
                help_text='Format libre : {prefix}-{year}-{month}-{day}-{number}',
                max_length=100,
                verbose_name='Format personnalisé'
            ),
        ),
        
        # Modifier les champs existants
        migrations.AlterField(
            model_name='tenantdocumentnumbering',
            name='prefix',
            field=models.CharField(
                blank=True,
                help_text='Préfixe du numéro (ex: MEAK, CONSTRUCTION)',
                max_length=20,
                verbose_name='Préfixe'
            ),
        ),
        migrations.AlterField(
            model_name='tenantdocumentnumbering',
            name='suffix',
            field=models.CharField(
                blank=True,
                help_text='Suffixe optionnel',
                max_length=10,
                verbose_name='Suffixe'
            ),
        ),
        migrations.AlterField(
            model_name='tenantdocumentnumbering',
            name='padding',
            field=models.IntegerField(
                default=3,
                help_text='Nombre de chiffres pour le numéro (ex: 3 pour 001)',
                verbose_name='Nombre de chiffres'
            ),
        ),
    ]