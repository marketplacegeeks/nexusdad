from django.db import migrations

def seed_dummy_data(apps, schema_editor):
    Consignee = apps.get_model("OfficeApps", "Consignee")
    Exporter = apps.get_model("OfficeApps", "Exporter")
    BankMaster = apps.get_model("OfficeApps", "BankMaster")
    FinalDestination = apps.get_model("OfficeApps", "FinalDestination")
    PlaceOfReceipt = apps.get_model("OfficeApps", "PlaceOfReceipt")
    Country = apps.get_model("OfficeApps", "Country")

    # Create dummy countries if they don't exist
    country_codes = ["US", "DE", "IN", "CN", "GB"]
    countries = {}
    for code in country_codes:
        country, _ = Country.objects.get_or_create(iso_code=code, defaults={'name': f'Country {code}'})
        countries[code] = country

    # Dummy data for Consignee
    for i in range(1, 6):
        Consignee.objects.get_or_create(
            name=f"Consignee {i}",
            defaults={
                "address": f"Consignee Address {i}",
                "country": countries[country_codes[i-1]],
                "contact_person": f"Person {i}",
                "phone_no": f"+1000000{i:03d}",
                "email_id": f"consignee{i}@example.com",
                "tax_number": f"TAX{i:03d}",
            }
        )

    # Dummy data for Exporter
    for i in range(1, 6):
        Exporter.objects.get_or_create(
            name=f"Exporter {i}",
            defaults={
                "address": f"Exporter Address {i}",
                "country": countries[country_codes[i-1]],
                "contact_person": f"Export Manager {i}",
                "phone_no": f"+2000000{i:03d}",
                "email_id": f"exporter{i}@example.com",
                "iec_code": f"IEC{i:04d}",
            }
        )

    # Dummy data for BankMaster
    for i in range(1, 6):
        BankMaster.objects.get_or_create(
            account_number=f"ACC{i:04d}",
            defaults={
                "beneficiary_name": f"Beneficiary {i}",
                "bank_name": f"Bank {i}",
                "branch_name": f"Branch {i}",
                "branch_address": f"Branch Address {i}",
                "swift_code": f"SWIFT{i:04d}",
            }
        )

    # Dummy data for FinalDestination
    for i in range(1, 6):
        FinalDestination.objects.get_or_create(
            name=f"Destination {i}",
            country=countries[country_codes[i-1]],
            defaults={}
        )

    # Dummy data for PlaceOfReceipt
    for i in range(1, 6):
        PlaceOfReceipt.objects.get_or_create(name=f"Receipt Place {i}")

class Migration(migrations.Migration):

    dependencies = [
        ('OfficeApps', '0027_commercialinvoice_fob_rate_commercialinvoice_freight_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_dummy_data),
    ]