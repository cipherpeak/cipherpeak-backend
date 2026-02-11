from django.db import migrations

def backfill_base_quotas(apps, schema_editor):
    Client = apps.get_model('clientapp', 'Client')
    for client in Client.objects.all():
        if client.base_posters_per_month == 0:
            client.base_posters_per_month = client.posters_per_month
        if client.base_videos_per_month == 0:
            client.base_videos_per_month = client.videos_per_month
        client.save()

class Migration(migrations.Migration):
    dependencies = [
        ('clientapp', '0023_client_base_posters_per_month_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_base_quotas),
    ]
