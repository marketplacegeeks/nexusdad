from django.db import migrations


def seed_master_data(apps, schema_editor):
    Country = apps.get_model("OfficeApps", "Country")
    PaymentTerm = apps.get_model("OfficeApps", "PaymentTerm")
    Incoterm = apps.get_model("OfficeApps", "Incoterm")
    PortOfLoading = apps.get_model("OfficeApps", "PortOfLoading")
    PortOfDischarge = apps.get_model("OfficeApps", "PortOfDischarge")
    PreCarriage = apps.get_model("OfficeApps", "PreCarriage")
    # Optional tables without explicit seeds in requirements
    # PlaceOfReceipt = apps.get_model("OfficeApps", "PlaceOfReceipt")
    # FinalDestination = apps.get_model("OfficeApps", "FinalDestination")

    # Countries
    countries = {
        "AE": "United Arab Emirates",
        "IN": "India",
        "SA": "Saudi Arabia",
        "US": "United States",
        "DE": "Germany",
    }
    iso_to_country = {}
    for iso, name in countries.items():
        country_obj, _ = Country.objects.get_or_create(iso_code=iso, defaults={"name": name})
        if country_obj.name != name:
            country_obj.name = name
            country_obj.save(update_fields=["name", "updated_at"])
        iso_to_country[iso] = country_obj

    # Payment Terms
    for name in ["Advance", "LC at Sight", "30 Days Credit", "60 Days Credit"]:
        PaymentTerm.objects.get_or_create(name=name)

    # Incoterms
    incoterms = [
        ("EXW", "Ex Works"),
        ("FOB", "Free on Board"),
        ("CIF", "Cost Insurance Freight"),
        ("DAP", "Delivered at Place"),
    ]
    for code, desc in incoterms:
        obj, created = Incoterm.objects.get_or_create(code=code, defaults={"description": desc})
        if not created and obj.description != desc:
            obj.description = desc
            obj.save(update_fields=["description", "updated_at"])

    # Ports of Loading
    ports_loading = [
        ("Jebel Ali", "AE"),
        ("Mundra", "IN"),
        ("Nhava Sheva", "IN"),
    ]
    for name, iso in ports_loading:
        country = iso_to_country.get(iso)
        if country:
            PortOfLoading.objects.get_or_create(name=name, country=country)

    # Ports of Discharge
    ports_discharge = [
        ("Dammam", "SA"),
        ("Hamburg", "DE"),
        ("New York", "US"),
    ]
    for name, iso in ports_discharge:
        country = iso_to_country.get(iso)
        if country:
            PortOfDischarge.objects.get_or_create(name=name, country=country)

    # Pre-Carriage
    for name in ["By Road", "By Rail", "By Sea"]:
        PreCarriage.objects.get_or_create(name=name)


def setup_groups_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    maker_group, _ = Group.objects.get_or_create(name="Maker")
    checker_group, _ = Group.objects.get_or_create(name="Checker")

    model_names = [
        "country",
        "bankmaster",
        "exporter",
        "consignee",
        "precarriage",
        "placeofreceipt",
        "paymentterm",
        "incoterm",
        "portofloading",
        "portofdischarge",
        "finaldestination",
    ]

    for model in model_names:
        try:
            ct = ContentType.objects.get(app_label="OfficeApps", model=model)
        except ContentType.DoesNotExist:
            # In case content type missing (shouldn't happen post 0001_initial)
            continue

        # Assign view perms to Makers
        view_codename = f"view_{model}"
        view_perm = Permission.objects.filter(content_type=ct, codename=view_codename).first()
        if view_perm:
            maker_group.permissions.add(view_perm)

        # Assign add/change/view perms to Checkers
        for codename in (f"add_{model}", f"change_{model}", f"view_{model}"):
            perm = Permission.objects.filter(content_type=ct, codename=codename).first()
            if perm:
                checker_group.permissions.add(perm)


def forwards(apps, schema_editor):
    seed_master_data(apps, schema_editor)
    setup_groups_permissions(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ("OfficeApps", "0001_initial"),
        # Rely on builtin apps being present; no explicit dependency needed for auth/contenttypes
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]