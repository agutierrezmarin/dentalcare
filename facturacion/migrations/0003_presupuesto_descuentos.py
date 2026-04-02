from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0002_ticket_itemticket'),
    ]

    operations = [
        migrations.AddField(
            model_name='presupuesto',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='presupuesto',
            name='descuento_global',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='presupuesto',
            name='descuento_monto',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
