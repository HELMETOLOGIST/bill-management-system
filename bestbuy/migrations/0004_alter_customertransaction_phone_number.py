# Generated by Django 4.2.14 on 2024-08-27 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bestbuy', '0003_customertransaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customertransaction',
            name='phone_number',
            field=models.BigIntegerField(),
        ),
    ]
