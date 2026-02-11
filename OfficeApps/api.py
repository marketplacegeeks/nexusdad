from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
import re

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
from .serializers import (
    CountrySerializer,
    BankMasterSerializer,
    ExporterSerializer,
    ConsigneeSerializer,
    BuyerSerializer,
    PreCarriageSerializer,
    PlaceOfReceiptSerializer,
    PaymentTermSerializer,
    IncotermSerializer,
    PortOfLoadingSerializer,
    PortOfDischargeSerializer,
    FinalDestinationSerializer,
    UOMSerializer,
    TermsAndConditionsTemplateSerializer,
    ProformaInvoiceSerializer,
    ProformaInvoiceLineItemSerializer,
    ProformaInvoiceAuditTrailSerializer,
    RegisteredAddressSerializer,
    PackingListSerializer,
    CommercialInvoiceSerializer,
    CommercialInvoiceLineItemSerializer,
    CommercialInvoiceAuditTrailSerializer,
)
from .permissions import IsCheckerOrAdminForWrite


class BaseSoftDeleteViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet:
    - List only active by default.
    - Prevent physical deletion.
    - Provide 'deactivate' custom action to soft delete.
    - Enforce role-based access permissions.
    """
    permission_classes = [IsAuthenticated, DjangoModelPermissions, IsCheckerOrAdminForWrite]

    def get_queryset(self):
        # List only active records
        return self.queryset.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):
        # Physical delete not allowed; use deactivate
        return Response({"detail": "Method \"DELETE\" not allowed. Use deactivate."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = False
        obj.deactivated_at = timezone.now()
        obj.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CountryViewSet(BaseSoftDeleteViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class BankMasterViewSet(BaseSoftDeleteViewSet):
    queryset = BankMaster.objects.all()
    serializer_class = BankMasterSerializer


class ExporterViewSet(BaseSoftDeleteViewSet):
    queryset = Exporter.objects.all()
    serializer_class = ExporterSerializer


class ConsigneeViewSet(BaseSoftDeleteViewSet):
    queryset = Consignee.objects.all()
    serializer_class = ConsigneeSerializer

    @action(detail=False, methods=["get"], url_path="with-approved-packing-lists")
    def with_approved_packing_lists(self, request):
        qs = Consignee.objects.filter(
            is_active=True,
            packing_lists__is_active=True,
            packing_lists__status=PackingList.STATUS_APPROVED,
        ).distinct().order_by("name")
        data = ConsigneeSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class BuyerViewSet(BaseSoftDeleteViewSet):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer


class PreCarriageViewSet(BaseSoftDeleteViewSet):
    queryset = PreCarriage.objects.all()
    serializer_class = PreCarriageSerializer


class PlaceOfReceiptViewSet(BaseSoftDeleteViewSet):
    queryset = PlaceOfReceipt.objects.all()
    serializer_class = PlaceOfReceiptSerializer


class PaymentTermViewSet(BaseSoftDeleteViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer

class UOMViewSet(BaseSoftDeleteViewSet):
    queryset = UOM.objects.all()
    serializer_class = UOMSerializer


class IncotermViewSet(BaseSoftDeleteViewSet):
    queryset = Incoterm.objects.all()
    serializer_class = IncotermSerializer


class PortOfLoadingViewSet(BaseSoftDeleteViewSet):
    queryset = PortOfLoading.objects.all()
    serializer_class = PortOfLoadingSerializer


class PortOfDischargeViewSet(BaseSoftDeleteViewSet):
    queryset = PortOfDischarge.objects.all()
    serializer_class = PortOfDischargeSerializer


class FinalDestinationViewSet(BaseSoftDeleteViewSet):
    queryset = FinalDestination.objects.all()
    serializer_class = FinalDestinationSerializer


class TermsAndConditionsTemplateViewSet(BaseSoftDeleteViewSet):
    queryset = TermsAndConditionsTemplate.objects.all()
    serializer_class = TermsAndConditionsTemplateSerializer
    permission_classes = [IsAuthenticated, IsCheckerOrAdminForWrite]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at", "updated_at"]


class RegisteredAddressViewSet(BaseSoftDeleteViewSet):
    queryset = RegisteredAddress.objects.all()
    serializer_class = RegisteredAddressSerializer
    permission_classes = [IsAuthenticated, IsCheckerOrAdminForWrite]


# =========================
# Proforma Invoice API
# =========================

class ProformaInvoicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def _is_maker(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name="Maker").exists())


def _is_checker(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name="Checker").exists())


def _is_admin(user):
    return user.is_authenticated and user.is_superuser


class ProformaInvoiceViewSet(BaseSoftDeleteViewSet):
    """
    ViewSet providing listing, CRUD, and workflow actions for Proforma Invoices.
    """
    queryset = ProformaInvoice.objects.all().select_related(
        "exporter", "consignee", "buyer", "payment_term", "incoterm"
    )
    serializer_class = ProformaInvoiceSerializer
    permission_classes = [IsAuthenticated]  # Use per-action role checks; do not restrict writes to Checker-only
    pagination_class = ProformaInvoicePagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["number", "consignee__name", "exporter__name"]
    ordering_fields = ["date", "number", "status", "total_amount_usd"]
    ordering = ["-date", "-created_at"]

    def get_queryset(self):
        # Active only
        return super().get_queryset().filter(is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to create."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save(maker=user, status=ProformaInvoice.STATUS_DRAFT)

    def update(self, request, *args, **kwargs):
        # Allow edit only:
        # Maker when status in {DRAFT, REWORK}
        # Checker when status == REWORK
        # Admin always
        instance = self.get_object()
        user = request.user
        if _is_admin(user):
            return super().update(request, *args, **kwargs)
        if _is_maker(user) and instance.status in {ProformaInvoice.STATUS_DRAFT, ProformaInvoice.STATUS_REWORK}:
            return super().update(request, *args, **kwargs)
        if _is_checker(user) and instance.status == ProformaInvoice.STATUS_REWORK:
            return super().update(request, *args, **kwargs)
        return Response({"detail": "Not allowed to edit in current status."}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        # Physical delete not allowed
        return Response({"detail": "Method \"DELETE\" not allowed. Use deactivate."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        # Maker can deactivate only if DRAFT; Admin can deactivate any
        invoice = self.get_object()
        user = request.user
        if _is_admin(user) or (_is_maker(user) and invoice.status == ProformaInvoice.STATUS_DRAFT):
            invoice.deactivate(commit=True)
            ProformaInvoiceAuditTrail.objects.create(
                invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_DEACTIVATED, actor=user
            )
            serializer = self.get_serializer(invoice)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Not allowed to deactivate."}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to submit."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status not in {ProformaInvoice.STATUS_DRAFT, ProformaInvoice.STATUS_REWORK}:
            return Response({"detail": "Only Draft/Rework can be submitted."}, status=status.HTTP_400_BAD_REQUEST)
        invoice.submit()
        invoice.save(update_fields=["status", "submitted_at", "updated_at"])
        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_SUBMITTED, actor=user
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to approve."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status not in {ProformaInvoice.STATUS_PENDING_APPROVAL, ProformaInvoice.STATUS_REWORK}:
            return Response({"detail": "Only Pending Approval/Rework can be approved."}, status=status.HTTP_400_BAD_REQUEST)
        invoice.approve(checker_user=user)
        invoice.save(update_fields=["status", "approved_at", "last_checker", "updated_at"])
        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_APPROVED, actor=user
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """
        Reject moves invoice to REWORK but logs 'REJECTED' in audit trail with optional notes.
        """
        invoice = self.get_object()
        user = request.user
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to reject."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status != ProformaInvoice.STATUS_PENDING_APPROVAL:
            return Response({"detail": "Only Pending Approval can be rejected."}, status=status.HTTP_400_BAD_REQUEST)
        notes = request.data.get("notes", "")
        invoice.reject_to_rework(checker_user=user)
        invoice.save(update_fields=["status", "reworked_at", "last_checker", "updated_at"])
        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_REJECTED, actor=user, notes=notes
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def audit(self, request, pk=None):
        invoice = self.get_object()
        qs = invoice.audit_trail.all().order_by("-timestamp")
        data = ProformaInvoiceAuditTrailSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        """
        Generate and return PDF only when status == APPROVED.
        """
        try:
            from OfficeApps.pdf.proforma_invoice_generator import generate_proforma_invoice_pdf_bytes
        except Exception:
            return Response({"detail": "PDF generation library not installed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice = self.get_object()
        user = request.user
        if invoice.status != ProformaInvoice.STATUS_APPROVED:
            return Response({"detail": "PDF available only for Approved invoices."}, status=status.HTTP_400_BAD_REQUEST)
        if not (_is_maker(user) or _is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to download PDF."}, status=status.HTTP_403_FORBIDDEN)

        from django.http import HttpResponse
        pdf_bytes = generate_proforma_invoice_pdf_bytes(invoice)

        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_PDF_DOWNLOADED, actor=user
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="PI_{invoice.number}.pdf"'
        return response

    def _can_edit(self, user, invoice):
        if _is_admin(user):
            return True
        if _is_maker(user) and invoice.status in {ProformaInvoice.STATUS_DRAFT, ProformaInvoice.STATUS_REWORK}:
            return True
        if _is_checker(user) and invoice.status == ProformaInvoice.STATUS_REWORK:
            return True
        return False

    @action(detail=True, methods=["get", "post"], url_path="line-items")
    def line_items(self, request, pk=None):
        """
        GET: List active line items for the invoice.
        POST: Create a new line item for the invoice (requires edit permission).
        """
        invoice = self.get_object()
        if request.method == "GET":
            qs = invoice.line_items.filter(is_active=True).order_by("created_at")
            data = ProformaInvoiceLineItemSerializer(qs, many=True).data
            return Response(data, status=status.HTTP_200_OK)

        # POST
        user = request.user
        if not self._can_edit(user, invoice):
            return Response({"detail": "Not allowed to add line items."}, status=status.HTTP_403_FORBIDDEN)

        payload = request.data.copy()
        payload["invoice"] = invoice.id
        serializer = ProformaInvoiceLineItemSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_EDITED, actor=user, notes="Line item added"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="line-items/(?P<item_id>[^/.]+)")
    def update_line_item(self, request, pk=None, item_id=None):
        """
        PATCH: Update an existing line item (requires edit permission).
        """
        invoice = self.get_object()
        user = request.user
        if not self._can_edit(user, invoice):
            return Response({"detail": "Not allowed to edit line items."}, status=status.HTTP_403_FORBIDDEN)
        try:
            item = invoice.line_items.get(pk=item_id, is_active=True)
        except ProformaInvoiceLineItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProformaInvoiceLineItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_EDITED, actor=user, notes="Line item updated"
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="line-items/(?P<item_id>[^/.]+)/deactivate")
    def deactivate_line_item(self, request, pk=None, item_id=None):
        """
        POST: Soft-delete (deactivate) a line item (requires edit permission).
        """
        invoice = self.get_object()
        user = request.user
        if not self._can_edit(user, invoice):
            return Response({"detail": "Not allowed to delete line items."}, status=status.HTTP_403_FORBIDDEN)
        try:
            item = invoice.line_items.get(pk=item_id, is_active=True)
        except ProformaInvoiceLineItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        item.deactivate(commit=True)
        ProformaInvoiceAuditTrail.objects.create(
            invoice=invoice, action=ProformaInvoiceAuditTrail.ACTION_EDITED, actor=user, notes="Line item deleted"
        )
        return Response(ProformaInvoiceLineItemSerializer(item).data, status=status.HTTP_200_OK)


# =========================
# Commercial Invoice API
# =========================

class CommercialInvoiceViewSet(BaseSoftDeleteViewSet):
    """
    ViewSet providing listing, CRUD, and workflow actions for Commercial Invoices.
    """
    queryset = CommercialInvoice.objects.all().select_related(
        "exporter", "consignee", "buyer", "payment_term", "incoterm", "bank"
    )
    serializer_class = CommercialInvoiceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ProformaInvoicePagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["number", "consignee__name", "exporter__name"]
    ordering_fields = ["date", "number", "status", "total_amount_usd", "amount"]
    ordering = ["-date", "-created_at"]

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    @action(detail=False, methods=["get"], url_path="approved-for-consignee")
    def approved_for_consignee(self, request):
        consignee_id = request.query_params.get("consignee_id")
        if not consignee_id:
            return Response({"detail": "consignee_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        qs = PackingList.objects.filter(
            is_active=True,
            status=PackingList.STATUS_APPROVED,
            consignee_id=consignee_id,
        ).order_by("-date", "-created_at")
        data = PackingListSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        user = self.request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to create."}, status=status.HTTP_403_FORBIDDEN)
        instance = serializer.save(maker=user, status=CommercialInvoice.STATUS_DRAFT)
        CommercialInvoiceAuditTrail.objects.create(
            invoice=instance, action=CommercialInvoiceAuditTrail.ACTION_CREATED, actor=user
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if instance.status in {CommercialInvoice.STATUS_APPROVED, CommercialInvoice.STATUS_DISABLED}:
            return Response({"detail": "Approved/Disabled invoices are read-only."}, status=status.HTTP_403_FORBIDDEN)

        if _is_admin(user):
            resp = super().update(request, *args, **kwargs)
            CommercialInvoiceAuditTrail.objects.create(
                invoice=instance, action=CommercialInvoiceAuditTrail.ACTION_EDITED, actor=user
            )
            return resp

        if _is_maker(user) and instance.status in {CommercialInvoice.STATUS_DRAFT, CommercialInvoice.STATUS_REJECTED}:
            resp = super().update(request, *args, **kwargs)
            CommercialInvoiceAuditTrail.objects.create(
                invoice=instance, action=CommercialInvoiceAuditTrail.ACTION_EDITED, actor=user
            )
            return resp

        if _is_checker(user) and instance.status == CommercialInvoice.STATUS_REJECTED:
            resp = super().update(request, *args, **kwargs)
            CommercialInvoiceAuditTrail.objects.create(
                invoice=instance, action=CommercialInvoiceAuditTrail.ACTION_EDITED, actor=user
            )
            return resp

        return Response({"detail": "Not allowed to edit in current status."}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Method \"DELETE\" not allowed. Use deactivate."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if invoice.status == CommercialInvoice.STATUS_DISABLED:
            return Response({"detail": "Disabled invoices cannot be deactivated."}, status=status.HTTP_400_BAD_REQUEST)
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to deactivate."}, status=status.HTTP_403_FORBIDDEN)

        invoice.deactivate(commit=True)
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_DISABLED, actor=user, notes="Record deactivated"
        )
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to submit."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status not in {CommercialInvoice.STATUS_DRAFT, CommercialInvoice.STATUS_REJECTED}:
            return Response({"detail": "Only Draft/Rejected can be submitted."}, status=status.HTTP_400_BAD_REQUEST)
        invoice.submit()
        invoice.save(update_fields=["status", "submitted_at", "updated_at"])
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_SUBMITTED, actor=user
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to approve."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status not in {CommercialInvoice.STATUS_PENDING_APPROVAL, CommercialInvoice.STATUS_REJECTED}:
            return Response({"detail": "Only Pending Approval/Rejected can be approved."}, status=status.HTTP_400_BAD_REQUEST)

        invoice.approve(checker_user=user)
        invoice.save(update_fields=["status", "approved_at", "last_checker", "updated_at"])
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_APPROVED, actor=user
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        invoice = self.get_object()
        user = request.user
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to reject."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status != CommercialInvoice.STATUS_PENDING_APPROVAL:
            return Response({"detail": "Only Pending Approval can be rejected."}, status=status.HTTP_400_BAD_REQUEST)

        notes = request.data.get("notes", "").strip()
        if not notes:
            return Response({"detail": "Rejection requires comments for rework."}, status=status.HTTP_400_BAD_REQUEST)

        invoice.reject(checker_user=user)
        invoice.save(update_fields=["status", "rejected_at", "last_checker", "updated_at"])
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_REJECTED, actor=user, notes=notes
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        invoice = self.get_object()
        user = self.request.user
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to disable."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status != CommercialInvoice.STATUS_APPROVED:
            return Response({"detail": "Only Approved invoices can be disabled."}, status=status.HTTP_400_BAD_REQUEST)

        invoice.disable()
        invoice.save(update_fields=["status", "disabled_at", "updated_at"])
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_DISABLED, actor=user
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def pdf_draft(self, request, pk=None):
        try:
            from OfficeApps.pdf.commercial_invoice_generator import generate_commercial_invoice_pdf_bytes
        except Exception:
            return Response({"detail": "PDF generation library not installed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice = self.get_object()
        user = request.user

        if invoice.status == CommercialInvoice.STATUS_APPROVED:
            return Response({"detail": "Draft PDF available only before approval."}, status=status.HTTP_400_BAD_REQUEST)
        if not (_is_admin(user) or (invoice.maker_id == user.id and _is_maker(user))):
            return Response({"detail": "Not allowed to download Draft PDF."}, status=status.HTTP_403_FORBIDDEN)

        from django.http import HttpResponse
        pdf_bytes = generate_commercial_invoice_pdf_bytes(invoice, draft=True)

        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_PDF_DRAFT_DOWNLOADED, actor=user
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="CI_{invoice.number}_DRAFT.pdf"'
        return response

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        try:
            from OfficeApps.pdf.commercial_invoice_generator import generate_commercial_invoice_pdf_bytes
        except Exception:
            return Response({"detail": "PDF generation library not installed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        invoice = self.get_object()
        user = request.user
        if invoice.status != CommercialInvoice.STATUS_APPROVED:
            return Response({"detail": "PDF available only for Approved invoices."}, status=status.HTTP_400_BAD_REQUEST)
        if not (_is_maker(user) or _is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to download PDF."}, status=status.HTTP_403_FORBIDDEN)

        from django.http import HttpResponse
        pdf_bytes = generate_commercial_invoice_pdf_bytes(invoice, draft=False)

        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_PDF_DOWNLOADED, actor=user
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="CI_{invoice.number}.pdf"'
        return response

    @action(detail=True, methods=["get"])
    def audit(self, request, pk=None):
        """
        Return audit trail entries for this Commercial Invoice (latest first).
        """
        invoice = self.get_object()
        qs = invoice.audit_trail.all().order_by("-timestamp")
        data = CommercialInvoiceAuditTrailSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def _can_edit(self, user, invoice):
        if _is_admin(user):
            return True
        if _is_maker(user) and invoice.status in {CommercialInvoice.STATUS_DRAFT, CommercialInvoice.STATUS_REJECTED}:
            return True
        if _is_checker(user) and invoice.status == CommercialInvoice.STATUS_REJECTED:
            return True
        return False

    @action(detail=True, methods=["get", "post"], url_path="line-items")
    def line_items(self, request, pk=None):
        invoice = self.get_object()
        if request.method == "GET":
            qs = invoice.line_items.filter(is_active=True).order_by("created_at")
            data = CommercialInvoiceLineItemSerializer(qs, many=True).data
            return Response(data, status=status.HTTP_200_OK)

        user = request.user
        if not self._can_edit(user, invoice):
            return Response({"detail": "Not allowed to add line items."}, status=status.HTTP_403_FORBIDDEN)

        payload = request.data.copy()
        payload["invoice"] = invoice.id
        serializer = CommercialInvoiceLineItemSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_EDITED, actor=user, notes="Line item added"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="line-items/(?P<item_id>[^/.]+)")
    def update_line_item(self, request, pk=None, item_id=None):
        invoice = self.get_object()
        user = request.user
        if not self._can_edit(user, invoice):
            return Response({"detail": "Not allowed to edit line items."}, status=status.HTTP_403_FORBIDDEN)
        try:
            item = invoice.line_items.get(pk=item_id, is_active=True)
        except CommercialInvoiceLineItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommercialInvoiceLineItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_EDITED, actor=user, notes="Line item updated"
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="line-items/(?P<item_id>[^/.]+)/deactivate")
    def deactivate_line_item(self, request, pk=None, item_id=None):
        invoice = self.get_object()
        user = request.user
        if not self._can_edit(user, invoice):
            return Response({"detail": "Not allowed to delete line items."}, status=status.HTTP_403_FORBIDDEN)
        try:
            item = invoice.line_items.get(pk=item_id, is_active=True)
        except CommercialInvoiceLineItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        item.deactivate(commit=True)
        CommercialInvoiceAuditTrail.objects.create(
            invoice=invoice, action=CommercialInvoiceAuditTrail.ACTION_EDITED, actor=user, notes="Line item deleted"
        )
        return Response(CommercialInvoiceLineItemSerializer(item).data, status=status.HTTP_200_OK)

# =========================
# Packing List API
# =========================

class PackingListViewSet(BaseSoftDeleteViewSet):
    """
    ViewSet for Packing Lists.
    """
    queryset = PackingList.objects.all().select_related("proforma_invoice__consignee", "proforma_invoice__exporter")
    serializer_class = PackingListSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(maker=request.user, status=PackingList.STATUS_DRAFT)
            try:
                print(f"[PackingListViewSet.create] Created PL id={instance.id} number={getattr(instance, 'number', '')}")
            except Exception:
                pass
            data = self.get_serializer(instance).data
            headers = self.get_success_headers(data)
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)
        except (TypeError, ValueError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    permission_classes = [IsAuthenticated]
    pagination_class = ProformaInvoicePagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["number", "proforma_invoice__number", "proforma_invoice__consignee__name"]
    ordering_fields = ["date", "number", "status"]
    ordering = ["-date", "-created_at"]

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    @action(detail=False, methods=["get"], url_path="aggregate-from-packing-list")
    def aggregate_from_packing_list(self, request):
        pl_id = request.query_params.get("packing_list_id")
        if not pl_id:
            return Response({"detail": "packing_list_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pl = PackingList.objects.select_related("exporter", "consignee", "payment_term", "incoterm").get(
                pk=pl_id, is_active=True
            )
        except PackingList.DoesNotExist:
            return Response({"detail": "Packing List not found."}, status=status.HTTP_404_NOT_FOUND)
        if pl.status != PackingList.STATUS_APPROVED:
            return Response({"detail": "Packing List must be Approved."}, status=status.HTTP_400_BAD_REQUEST)

        groups = {}
        # Aggregate items by (item_code, uom_id)
        for container in pl.containers.filter(is_active=True).prefetch_related("items__uom"):
            for it in container.items.filter(is_active=True):
                key = (it.item_code or "", it.uom_id or 0)
                g = groups.get(key)
                if not g:
                    groups[key] = {
                        "hs_code": it.hsn_code or "",
                        "item_code": it.item_code or "",
                        "description": it.description_of_goods or "",
                        "packages_number_and_kind": it.packages_number_and_kind or "",
                        "quantity": it.quantity or 0,
                        "unit_id": it.uom_id,
                        "unit": it.uom.uom if it.uom_id else "",
                        "container_ids": set([container.id]),
                    }
                else:
                    groups[key]["quantity"] += it.quantity or 0
                    groups[key]["container_ids"].add(container.id)

        if not groups:
            return Response({"detail": "No items found to aggregate for this Packing List."}, status=status.HTTP_400_BAD_REQUEST)

        line_items = []
        for _, g in groups.items():
            desc = g["description"]
            if len(g["container_ids"]) > 1:
                if "In every container" not in desc:
                    desc = f"{desc} In every container".strip()
            line_items.append({
                "hs_code": g["hs_code"],
                "item_code": g["item_code"],
                "description": desc,
                "packages_number_and_kind": g["packages_number_and_kind"],
                "quantity": g["quantity"],
                "unit": g["unit"],
                "unit_id": g["unit_id"],
                "rate_label": f"Rate per {g['unit']}" if g["unit"] else "Rate per UOM",
                "unit_price_usd": None,
                "amount_usd": None,
            })

        payload = {
            "packing_list": {
                "id": pl.id,
                "number": pl.number,
                "exporter": pl.exporter_id,
                "consignee": pl.consignee_id,
                "payment_term": pl.payment_term_id,
                "incoterm": pl.incoterm_id,
            },
            "line_items": line_items,
        }
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="create-from-packing-list")
    def create_from_packing_list(self, request):
        user = request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to create."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data or {}
        pl_id = data.get("packing_list_id")
        bank_id = data.get("bank_id")
        line_items_input = data.get("line_items", [])
        # New optional fields for Commercial Invoice creation
        fob_rate = data.get("fob_rate")
        freight = data.get("freight")
        insurance = data.get("insurance")
        lc_details = data.get("lc_details", "")

        if not pl_id:
            return Response({"detail": "packing_list_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not bank_id:
            return Response({"detail": "bank_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pl = PackingList.objects.select_related("exporter", "consignee", "payment_term", "incoterm").get(
                pk=pl_id, is_active=True
            )
        except PackingList.DoesNotExist:
            return Response({"detail": "Packing List not found."}, status=status.HTTP_404_NOT_FOUND)
        if pl.status != PackingList.STATUS_APPROVED:
            return Response({"detail": "Packing List must be Approved."}, status=status.HTTP_400_BAD_REQUEST)

        # Re-aggregate to guarantee integrity
        groups = {}
        for container in pl.containers.filter(is_active=True).prefetch_related("items__uom"):
            for it in container.items.filter(is_active=True):
                key = (it.item_code or "", it.uom_id or 0)
                g = groups.get(key)
                if not g:
                    groups[key] = {
                        "hs_code": it.hsn_code or "",
                        "item_code": it.item_code or "",
                        "description": it.description_of_goods or "",
                        "packages_number_and_kind": it.packages_number_and_kind or "",
                        "quantity": it.quantity or 0,
                        "unit_id": it.uom_id,
                        "unit": it.uom.uom if it.uom_id else "",
                        "container_ids": set([container.id]),
                    }
                else:
                    g["quantity"] += it.quantity or 0
                    g["container_ids"].add(container.id)

        if not groups:
            return Response({"detail": "No items found to generate Commercial Invoice."}, status=status.HTTP_400_BAD_REQUEST)

        # Map provided rates by (item_code, unit_id)
        from decimal import Decimal
        rates_map = {}
        for li in line_items_input:
            key = (li.get("item_code") or "", li.get("unit_id") or 0)
            rate = li.get("unit_price_usd")
            try:
                rates_map[key] = Decimal(str(rate))
            except Exception:
                return Response({"detail": f"Invalid rate for item_code={key[0]}."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate rates and quantities
        for key, g in groups.items():
            if key not in rates_map or rates_map[key] is None or rates_map[key] <= 0:
                return Response({"detail": f"Rate per {g['unit'] or 'UOM'} must be entered for item {g['item_code']} and be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)
            if g["quantity"] is None or g["quantity"] <= 0:
                return Response({"detail": f"Quantity must be greater than zero for item {g['item_code']}."}, status=status.HTTP_400_BAD_REQUEST)

        from django.db import transaction
        with transaction.atomic():
            ci = CommercialInvoice.objects.create(
                exporter_id=pl.exporter_id,
                consignee_id=pl.consignee_id,
                buyer_id=pl.buyer_id,
                payment_term_id=pl.payment_term_id,
                incoterm_id=pl.incoterm_id,
                bank_id=bank_id,
                packing_list_id=pl.id,
                maker=user,
                status=CommercialInvoice.STATUS_DRAFT,
                # New charges and L/C
                fob_rate=Decimal(str(fob_rate)) if fob_rate is not None else Decimal("0"),
                freight=Decimal(str(freight)) if freight is not None else Decimal("0"),
                insurance=Decimal(str(insurance)) if insurance is not None else Decimal("0"),
                lc_details=lc_details or "",
            )
            for key, g in groups.items():
                desc = g["description"]
                if len(g["container_ids"]) > 1:
                    if "In every container" not in desc:
                        desc = f"{desc} In every container".strip()
                CommercialInvoiceLineItem.objects.create(
                    invoice=ci,
                    description=desc,
                    hs_code=g["hs_code"],
                    item_code=g["item_code"],
                    quantity=g["quantity"],
                    unit=g["unit"] or "",
                    unit_price_usd=rates_map[key],
                )
            ci.recalc_total(commit=True)
            CommercialInvoiceAuditTrail.objects.create(
                invoice=ci,
                action=CommercialInvoiceAuditTrail.ACTION_CREATED,
                actor=user,
                notes="Created from Packing List",
            )
        return Response(CommercialInvoiceSerializer(ci).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to create."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save(maker=user, status=PackingList.STATUS_DRAFT)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if instance.status == PackingList.STATUS_APPROVED:
            return Response({"detail": "Approved packing lists cannot be edited."}, status=status.HTTP_403_FORBIDDEN)

        if _is_admin(user):
            return super().update(request, *args, **kwargs)
        if _is_maker(user) and instance.status in {PackingList.STATUS_DRAFT, PackingList.STATUS_REWORK}:
            return super().update(request, *args, **kwargs)
        if _is_checker(user) and instance.status == PackingList.STATUS_REWORK:
            return super().update(request, *args, **kwargs)
        
        return Response({"detail": "Not allowed to edit in current status."}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        packing_list = self.get_object()
        user = request.user
        if not (_is_maker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to submit."}, status=status.HTTP_403_FORBIDDEN)
        if packing_list.status not in {PackingList.STATUS_DRAFT, PackingList.STATUS_REWORK}:
            return Response({"detail": "Only Draft/Rework can be submitted."}, status=status.HTTP_400_BAD_REQUEST)
        
        packing_list.status = PackingList.STATUS_PENDING_APPROVAL
        packing_list.submitted_at = timezone.now()
        packing_list.save()
        return Response(self.get_serializer(packing_list).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        packing_list = self.get_object()
        user = request.user
        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to approve."}, status=status.HTTP_403_FORBIDDEN)
        if packing_list.status != PackingList.STATUS_PENDING_APPROVAL:
            return Response({"detail": "Only Pending Approval can be approved."}, status=status.HTTP_400_BAD_REQUEST)

        packing_list.status = PackingList.STATUS_APPROVED
        packing_list.approved_at = timezone.now()
        packing_list.last_checker = user
        packing_list.save()
        return Response(self.get_serializer(packing_list).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        """
        Generate and return PDF only when status == APPROVED.
        """
        try:
            from OfficeApps.pdf.packing_list_generator import generate_packing_list_pdf_bytes
        except Exception:
            return Response({"detail": "PDF generation library not installed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        packing_list = self.get_object()
        user = request.user
        if packing_list.status != PackingList.STATUS_APPROVED:
            return Response({"detail": "PDF available only for Approved packing lists."}, status=status.HTTP_400_BAD_REQUEST)
        if not (_is_maker(user) or _is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to download PDF."}, status=status.HTTP_403_FORBIDDEN)

        from django.http import HttpResponse
        pdf_bytes = generate_packing_list_pdf_bytes(packing_list)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="PL_{packing_list.number}.pdf"'
        return response

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        packing_list = self.get_object()
        user = request.user
        notes = request.data.get("notes", "")

        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to reject."}, status=status.HTTP_403_FORBIDDEN)
        
        if not notes:
            return Response({"detail": "Rejection requires comments for rework."}, status=status.HTTP_400_BAD_REQUEST)

        if packing_list.status != PackingList.STATUS_PENDING_APPROVAL:
            return Response({"detail": "Only Pending Approval can be rejected."}, status=status.HTTP_400_BAD_REQUEST)

        packing_list.status = PackingList.STATUS_REWORK
        packing_list.reworked_at = timezone.now()
        packing_list.last_checker = user
        packing_list.save()
        
        # NOTE: Audit trail for packing list not implemented yet.
        return Response(self.get_serializer(packing_list).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["post"])
    def permanently_reject(self, request, pk=None):
        packing_list = self.get_object()
        user = request.user

        if not (_is_checker(user) or _is_admin(user)):
            return Response({"detail": "Not allowed to permanently reject."}, status=status.HTTP_403_FORBIDDEN)

        packing_list.status = PackingList.STATUS_PERMANENTLY_REJECTED
        packing_list.permanently_rejected_at = timezone.now()
        packing_list.last_checker = user
        packing_list.save()
        return Response(self.get_serializer(packing_list).data, status=status.HTTP_200_OK)
