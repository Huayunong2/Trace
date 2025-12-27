# Generated manually to fix elderly field - allow null
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        # 修改elderly字段，允许null，并将on_delete改为SET_NULL
        migrations.AlterField(
            model_name='device',
            name='elderly',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='device',
                to='users.elderlyprofile',
                verbose_name='关联老人',
                null=True,
                blank=True
            ),
        ),
    ]

