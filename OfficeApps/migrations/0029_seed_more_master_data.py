from django.db import migrations


def seed_more_master_data(apps, schema_editor):
    Country = apps.get_model("OfficeApps", "Country")
    PaymentTerm = apps.get_model("OfficeApps", "PaymentTerm")
    Incoterm = apps.get_model("OfficeApps", "Incoterm")
    PortOfLoading = apps.get_model("OfficeApps", "PortOfLoading")
    PortOfDischarge = apps.get_model("OfficeApps", "PortOfDischarge")
    PreCarriage = apps.get_model("OfficeApps", "PreCarriage")
    UOM = apps.get_model("OfficeApps", "UOM")
    Buyer = apps.get_model("OfficeApps", "Buyer")
    TermsAndConditionsTemplate = apps.get_model("OfficeApps", "TermsAndConditionsTemplate")

    # Ensure a broad set of countries exist
    country_defs = [
        ("AE", "United Arab Emirates"),
        ("IN", "India"),
        ("US", "United States"),
        ("DE", "Germany"),
        ("SA", "Saudi Arabia"),
        ("CN", "China"),
        ("GB", "United Kingdom"),
    ]
    countries = {}
    for code, name in country_defs:
        c, _ = Country.objects.get_or_create(iso_code=code, defaults={"name": name})
        if c.name != name:
            c.name = name
            c.save(update_fields=["name", "updated_at"])
        countries[code] = c

    # Payment Terms - ensure at least 5+
    for term in ["Advance", "LC at Sight", "30 Days Credit", "60 Days Credit", "90 Days Credit", "Cash Against Documents"]:
        PaymentTerm.objects.get_or_create(name=term)

    # Incoterms - ensure at least 5+
    incos = [
        ("EXW", "Ex Works"),
        ("FOB", "Free on Board"),
        ("CIF", "Cost Insurance Freight"),
        ("DAP", "Delivered At Place"),
        ("CIP", "Carriage and Insurance Paid To"),
        ("DDP", "Delivered Duty Paid"),
    ]
    for code, desc in incos:
        obj, created = Incoterm.objects.get_or_create(code=code, defaults={"description": desc})
        if not created and obj.description != desc:
            obj.description = desc
            obj.save(update_fields=["description", "updated_at"])

    # Ports of Loading - ensure 5+
    pols = [
        ("Jebel Ali", "AE"),
        ("Mundra", "IN"),
        ("Nhava Sheva", "IN"),
        ("Kandla", "IN"),
        ("Shanghai", "CN"),
    ]
    for name, iso in pols:
        country = countries.get(iso)
        if country:
            PortOfLoading.objects.get_or_create(name=name, country=country)

    # Ports of Discharge - ensure 5+
    pods = [
        ("Dammam", "SA"),
        ("Hamburg", "DE"),
        ("New York", "US"),
        ("Jeddah", "SA"),
        ("Felixstowe", "GB"),
    ]
    for name, iso in pods:
        country = countries.get(iso)
        if country:
            PortOfDischarge.objects.get_or_create(name=name, country=country)

    # Pre-Carriage - ensure 5+
    for name in ["By Road", "By Rail", "By Sea", "By Air", "By Truck"]:
        PreCarriage.objects.get_or_create(name=name)

    # UOM - ensure 5+
    for u, rate in [("KG", ""), ("MT", ""), ("PCS", ""), ("LTR", ""), ("BOX", "")]:
        UOM.objects.get_or_create(uom=u, defaults={"rate_per_uom": rate})

    # Buyers - add 5
    buyer_defs = [
        ("Buyer 1", "US"),
        ("Buyer 2", "DE"),
        ("Buyer 3", "IN"),
        ("Buyer 4", "CN"),
        ("Buyer 5", "GB"),
    ]
    for i, (name, iso) in enumerate(buyer_defs, start=1):
        Buyer.objects.get_or_create(
            name=name,
            defaults={
                "address": f"Buyer Address {i}",
                "country": countries[iso],
                "contact_person": f"Buyer Contact {i}",
                "phone": f"+3000000{i:03d}",
                "email": f"buyer{i}@example.com",
                "tax_number": f"BTAX{i:03d}",
            },
        )

    # Terms & Conditions Templates - add 5
    for i in range(1, 6):
        t_name = f"Standard T&C {i}"
        content = f"<p>Standard terms and conditions set {i}. This is dummy content for testing.</p>"
        TermsAndConditionsTemplate.objects.get_or_create(name=t_name, defaults={"content_html": content})


def forwards(apps, schema_editor):
    seed_more_master_data(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ("OfficeApps", "0028_seed_dummy_data"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]