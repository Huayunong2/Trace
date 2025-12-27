# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_elderlyprofile_guardian'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscribeMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_id', models.CharField(max_length=100, verbose_name='模板ID')),
                ('subscribe_status', models.BooleanField(default=True, verbose_name='订阅状态')),
                ('subscribed_at', models.DateTimeField(auto_now_add=True, verbose_name='订阅时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribe_messages', to='users.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': '订阅消息',
                'verbose_name_plural': '订阅消息',
                'db_table': 'subscribe_messages',
                'ordering': ['-subscribed_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='subscribemessage',
            constraint=models.UniqueConstraint(fields=('user', 'template_id'), name='unique_user_template'),
        ),
    ]
