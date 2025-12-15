from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("CarParking", "0004_contactinfo"),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='vehicle_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('sedan', 'Sedan'),
                    ('suv', 'SUV'),
                    ('pickup', 'Pickup'),
                    ('motorcycle', 'Motorcycle'),
                ],
                max_length=20,
                null=True,
                verbose_name='Vehicle Type'
            ),
        ),
    ]
