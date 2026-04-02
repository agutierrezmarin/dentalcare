from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0001_initial'),
        ('clinico', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cita',
            name='tratamiento',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='citas',
                to='clinico.tratamiento',
            ),
        ),
    ]
