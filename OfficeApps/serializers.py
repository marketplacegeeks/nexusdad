from rest_framework import serializers
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
    ProformaInvoice,
    ProformaInvoiceLineItem,
    ProformaInvoiceAuditTrail,
)


class BaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "deactivated_at")


class CountrySerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Country


class BankMasterSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = BankMaster


class ExporterSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Exporter


class ConsigneeSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Consignee


class PreCarriageSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = PreCarriage


class PlaceOfReceiptSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = PlaceOfReceipt


class PaymentTermSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = PaymentTerm


class TermsAndConditionsTemplateSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = TermsAndConditionsTemplate


class IncotermSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Incoterm


class PortOfLoadingSerializer(BaseModelSerializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

    class Meta(BaseModelSerializer.Meta):
        model = PortOfLoading


class PortOfDischargeSerializer(BaseModelSerializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

    class Meta(BaseModelSerializer.Meta):
        model = PortOfDischarge


class FinalDestinationSerializer(BaseModelSerializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

    class Meta(BaseModelSerializer.Meta):
        model = FinalDestination


# Proforma Invoice Serializers

class ProformaInvoiceLineItemSerializer(BaseModelSerializer):
    # amount_usd is computed in model, keep it read-only in API
    amount_usd = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ProformaInvoiceLineItem


class ProformaInvoiceAuditTrailSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = ProformaInvoiceAuditTrail
        fields = ["id", "invoice", "action", "actor", "actor_username", "timestamp", "notes"]


class ProformaInvoiceSerializer(BaseModelSerializer):
    line_items = ProformaInvoiceLineItemSerializer(many=True, read_only=True)
    consignee_name = serializers.CharField(source="consignee.name", read_only=True)
    exporter_name = serializers.CharField(source="exporter.name", read_only=True)
    payment_term_name = serializers.CharField(source="payment_term.name", read_only=True)
    incoterm_code = serializers.CharField(source="incoterm.code", read_only=True)
    incoterm_description = serializers.CharField(source="incoterm.description", read_only=True)
    incoterm_display = serializers.SerializerMethodField(read_only=True)

    def get_incoterm_display(self, obj):
        if obj.incoterm:
            return obj.incoterm.code + ((" - " + obj.incoterm.description) if obj.incoterm.description else "")
        return ""

    class Meta(BaseModelSerializer.Meta):
        model = ProformaInvoice
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            "number",
            "maker",
            "status",
            "total_amount_usd",
            "submitted_at",
            "approved_at",
            "reworked_at",
            "last_checker",
        )
        extra_kwargs = {
            "number": {"read_only": True},
            "maker": {"read_only": True},
            "status": {"read_only": True},
            "total_amount_usd": {"read_only": True},
            "submitted_at": {"read_only": True},
            "approved_at": {"read_only": True},
            "reworked_at": {"read_only": True},
            "last_checker": {"read_only": True},
        }
