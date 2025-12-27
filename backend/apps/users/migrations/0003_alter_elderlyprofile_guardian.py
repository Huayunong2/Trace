# Generated manually to allow guardian to be null
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_elderlyprofile_user_alter_user_role'),
    ]

    operations = [
        # 修改guardian字段，允许null，并将on_delete改为SET_NULL
        migrations.AlterField(
            model_name='elderlyprofile',
            name='guardian',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='elderly_profiles',
                to='users.user',
                verbose_name='监护人',
                null=True,
                blank=True
            ),
        ),
    ]

