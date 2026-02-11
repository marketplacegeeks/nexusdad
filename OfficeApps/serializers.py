from django.db import transaction
from rest_framework import serializers
from .models import (
    Country,
    BankMaster,
    Exporter,
    Consignee,
    Buyer,
    PreCarriage,
    PlaceOfReceipt,
    PaymentTerm,
    Incoterm,
    PortOfLoading,
    PortOfDischarge,
    FinalDestination,
    UOM,
    TermsAndConditionsTemplate,
    ProformaInvoice,
    ProformaInvoiceLineItem,
    ProformaInvoiceAuditTrail,
    RegisteredAddress,
    PackingList,
    PackingListContainer,
    PackingListContainerItem,
    CommercialInvoice,
    CommercialInvoiceLineItem,
    CommercialInvoiceAuditTrail,
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


class RegisteredAddressSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = RegisteredAddress


class ExporterSerializer(BaseModelSerializer):
    registered_address_details = RegisteredAddressSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Exporter


class ConsigneeSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Consignee


class BuyerSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Buyer


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


class UOMSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = UOM

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
    buyer_name = serializers.CharField(source="buyer.name", read_only=True, allow_null=True)
    exporter_name = serializers.CharField(source="exporter.name", read_only=True)
    payment_term_name = serializers.CharField(source="payment_term.name", read_only=True)
    incoterm_code = serializers.CharField(source="incoterm.code", read_only=True)
    incoterm_description = serializers.CharField(source="incoterm.description", read_only=True)

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


# Commercial Invoice Serializers

class CommercialInvoiceLineItemSerializer(BaseModelSerializer):
    amount_usd = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = CommercialInvoiceLineItem


class CommercialInvoiceAuditTrailSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = CommercialInvoiceAuditTrail
        fields = ["id", "invoice", "action", "actor", "actor_username", "timestamp", "notes"]


class CommercialInvoiceSerializer(BaseModelSerializer):
    line_items = CommercialInvoiceLineItemSerializer(many=True, read_only=True)
    consignee_name = serializers.CharField(source="consignee.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.name", read_only=True, allow_null=True)
    exporter_name = serializers.CharField(source="exporter.name", read_only=True)
    payment_term_name = serializers.CharField(source="payment_term.name", read_only=True)
    incoterm_code = serializers.CharField(source="incoterm.code", read_only=True)
    incoterm_description = serializers.CharField(source="incoterm.description", read_only=True)
    maker_username = serializers.CharField(source="maker.username", read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = CommercialInvoice
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + (
            "number",
            "maker",
            "status",
            "amount",
            "total_amount_usd",
            "submitted_at",
            "approved_at",
            "rejected_at",
            "disabled_at",
            "last_checker",
        )
        extra_kwargs = {
            "number": {"read_only": True},
            "maker": {"read_only": True},
            "status": {"read_only": True},
            "amount": {"read_only": True},
            "total_amount_usd": {"read_only": True},
            "submitted_at": {"read_only": True},
            "approved_at": {"read_only": True},
            "rejected_at": {"read_only": True},
            "disabled_at": {"read_only": True},
            "last_checker": {"read_only": True},
        }

# Packing List Serializers

class PackingListContainerItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PackingListContainerItem
        fields = [
            "id", "hsn_code", "item_code", "packages_number_and_kind",
            "description_of_goods", "quantity", "uom", "batch_details"
        ]


class PackingListContainerSerializer(serializers.ModelSerializer):
    items = PackingListContainerItemSerializer(many=True)
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PackingListContainer
        fields = ["id", "container_reference", "marks_and_numbers", "net_weight", "tare_weight", "gross_weight", "items"]


class PackingListSerializer(serializers.ModelSerializer):
    containers = PackingListContainerSerializer(many=True)
    exporter_name = serializers.CharField(source="exporter.name", read_only=True)
    consignee_name = serializers.CharField(source="consignee.name", read_only=True)
    buyer_name = serializers.CharField(source="buyer.name", read_only=True, allow_null=True)
    maker = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    maker_username = serializers.CharField(source="maker.username", read_only=True)

    class Meta:
        model = PackingList
        fields = [
            "id", "number", "invoice_number", "date", "created_at", "exporter", "consignee", "buyer",
            "notify_party", "po_number", "po_date", "lc_number", "lc_date",
            "bl_number", "bl_date", "so_number", "so_date", "other_ref",
            "other_ref_date",
            # Shipping & Logistics
            "pre_carriage", "place_of_receipt", "place_of_receipt_by_pre_carrier", "vessel_flight_no",
            "port_loading", "port_discharge", "final_destination",
            # Commercial terms
            "payment_term", "incoterm",
            # Countries
            "origin_country", "final_destination_country",
            # Workflow and audit
            "status", "maker", "maker_username", "last_checker",
            "submitted_at", "approved_at", "reworked_at",
            # Links and nested
            "proforma_invoice", "containers", "exporter_name",
            "consignee_name", "buyer_name"
        ]
        read_only_fields = ("number",)

    @transaction.atomic
    def create(self, validated_data):
        containers_data = validated_data.pop("containers", [])
        packing_list = PackingList.objects.create(**validated_data)
        for container_data in containers_data:
            items_data = container_data.pop("items", [])
            container = PackingListContainer.objects.create(packing_list=packing_list, **container_data)
            for item_data in items_data:
                uom_val = item_data.pop("uom", None)
                if isinstance(uom_val, UOM):
                    item_data["uom_id"] = uom_val.id
                else:
                    try:
                        item_data["uom_id"] = int(uom_val) if uom_val else None
                    except (TypeError, ValueError):
                        item_data["uom_id"] = None
                PackingListContainerItem.objects.create(container=container, **item_data)
        return packing_list

    @transaction.atomic
    def update(self, instance, validated_data):
        # Pop the nested data
        containers_data = validated_data.pop('containers', [])

        # Update the parent instance (PackingList)
        instance = super().update(instance, validated_data)

        # Get a map of existing containers by ID
        existing_containers = {container.id: container for container in instance.containers.all()}
        
        # Keep track of which container IDs from the payload we've processed
        processed_container_ids = set()

        for container_data in containers_data:
            container_id = container_data.get('id')
            items_data = container_data.pop('items', [])
            
            container = None
            if container_id:
                processed_container_ids.add(container_id)
                # This is an existing container, update it
                if container_id in existing_containers:
                    container = existing_containers[container_id]
                    # Update container fields from payload
                    for attr, value in container_data.items():
                        setattr(container, attr, value)
                    container.save()
            else:
                # This is a new container, create it
                container = PackingListContainer.objects.create(packing_list=instance, **container_data)

            if container:
                # Now, process the items for this container
                existing_items = {item.id: item for item in container.items.all()}
                processed_item_ids = set()

                for item_data in items_data:
                    item_id = item_data.get('id')
                    
                    if item_id:
                        processed_item_ids.add(item_id)
                        # This is an existing item, update it
                        if item_id in existing_items:
                            item = existing_items[item_id]
                            # Update item fields from payload
                            for attr, value in item_data.items():
                                if attr == "uom":
                                    if isinstance(value, UOM):
                                        item.uom = value
                                    elif value:
                                        try:
                                            item.uom_id = int(value)
                                        except (TypeError, ValueError):
                                            item.uom = None
                                    else:
                                        item.uom = None
                                else:
                                    setattr(item, attr, value)
                            item.save()
                    else:
                        # This is a new item, create it
                        uom_val = item_data.pop("uom", None)
                        if isinstance(uom_val, UOM):
                            item_data["uom_id"] = uom_val.id
                        else:
                            try:
                                item_data["uom_id"] = int(uom_val) if uom_val else None
                            except (TypeError, ValueError):
                                item_data["uom_id"] = None
                        PackingListContainerItem.objects.create(container=container, **item_data)
                
                # Delete items that were removed from this container
                item_ids_to_delete = set(existing_items.keys()) - processed_item_ids
                if item_ids_to_delete:
                    PackingListContainerItem.objects.filter(id__in=item_ids_to_delete).delete()

        # Delete containers that were removed from the packing list
        container_ids_to_delete = set(existing_containers.keys()) - processed_container_ids
        if container_ids_to_delete:
            PackingListContainer.objects.filter(id__in=container_ids_to_delete).delete()

        return instance
