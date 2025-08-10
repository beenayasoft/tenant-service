

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0006_granular_company_info_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tenantsettings",
            name="currency",
            field=models.CharField(default="MAD", max_length=3, verbose_name="Devise"),
        ),
    ]
