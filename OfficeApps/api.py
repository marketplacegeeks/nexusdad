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
from .serializers import (
    CountrySerializer,
    BankMasterSerializer,
    ExporterSerializer,
    ConsigneeSerializer,
    PreCarriageSerializer,
    PlaceOfReceiptSerializer,
    PaymentTermSerializer,
    IncotermSerializer,
    PortOfLoadingSerializer,
    PortOfDischargeSerializer,
    FinalDestinationSerializer,
    TermsAndConditionsTemplateSerializer,
    ProformaInvoiceSerializer,
    ProformaInvoiceLineItemSerializer,
    ProformaInvoiceAuditTrailSerializer,
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


class PreCarriageViewSet(BaseSoftDeleteViewSet):
    queryset = PreCarriage.objects.all()
    serializer_class = PreCarriageSerializer


class PlaceOfReceiptViewSet(BaseSoftDeleteViewSet):
    queryset = PlaceOfReceipt.objects.all()
    serializer_class = PlaceOfReceiptSerializer


class PaymentTermViewSet(BaseSoftDeleteViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer


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
        "exporter", "consignee", "payment_term", "incoterm"
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
