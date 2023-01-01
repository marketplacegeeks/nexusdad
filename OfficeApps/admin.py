from django.contrib import admin
from .models import (
    Country,
    BankMaster,
    Exporter,
    Consignee,
    PreCarriage,
    PlaceOfReceipt,
    PaymentTerm,
    Incoterm,
    PortOfLoading,
    PortOfDischarge,
    FinalDestination,
    TermsAndConditionsTemplate,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "iso_code", "is_active", "created_at", "updated_at")
    search_fields = ("name", "iso_code")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(BankMaster)
class BankMasterAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "beneficiary_name", "account_number", "swift_code", "is_active", "created_at", "updated_at")
    search_fields = ("bank_name", "beneficiary_name", "account_number", "swift_code")
    list_filter = ("is_active",)
    ordering = ("bank_name",)


@admin.register(Exporter)
class ExporterAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "contact_person", "phone_no", "email_id", "is_active", "created_at", "updated_at")
    search_fields = ("name", "contact_person", "phone_no", "email_id")
    list_filter = ("is_active", "country")
    ordering = ("name",)


@admin.register(Consignee)
class ConsigneeAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "contact_person", "phone_no", "email_id", "is_active", "created_at", "updated_at")
    search_fields = ("name", "contact_person", "phone_no", "email_id")
    list_filter = ("is_active", "country")
    ordering = ("name",)


@admin.register(PreCarriage)
class PreCarriageAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(PlaceOfReceipt)
class PlaceOfReceiptAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Incoterm)
class IncotermAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "is_active", "created_at", "updated_at")
    search_fields = ("code", "description")
    list_filter = ("is_active",)
    ordering = ("code",)


@admin.register(PortOfLoading)
class PortOfLoadingAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active", "created_at", "updated_at")
    search_fields = ("name", "country__name", "country__iso_code")
    list_filter = ("is_active", "country")
    ordering = ("name",)


@admin.register(PortOfDischarge)
class PortOfDischargeAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active", "created_at", "updated_at")
    search_fields = ("name", "country__name", "country__iso_code")
    list_filter = ("is_active", "country")
    ordering = ("name",)


@admin.register(FinalDestination)
class FinalDestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active", "created_at", "updated_at")
    search_fields = ("name", "country__name", "country__iso_code")
    list_filter = ("is_active", "country")
    ordering = ("name",)


@admin.register(TermsAndConditionsTemplate)
class TermsAndConditionsTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("name",)
