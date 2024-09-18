# Generated by Django 5.1.1 on 2024-09-18 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserBook',
            fields=[
                ('book_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('author', models.CharField(max_length=100)),
                ('publisher', models.CharField(max_length=100)),
                ('category', models.CharField(max_length=100)),
                ('available', models.BooleanField(default=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('return_date', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
