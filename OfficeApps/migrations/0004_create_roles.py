from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ['Maker', 'Checker']:
        Group.objects.get_or_create(name=name)


def delete_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ['Maker', 'Checker']:
        try:
            Group.objects.get(name=name).delete()
        except Group.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('OfficeApps', '0003_alter_bankmaster_id_alter_consignee_id_and_more'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]