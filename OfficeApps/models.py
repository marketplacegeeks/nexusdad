from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from django.conf import settings
from decimal import Decimal


class BaseModel(models.Model):
    """
    Abstract base model providing soft-delete and audit fields.
    """
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    def deactivate(self, commit: bool = True):
        """
        Soft delete: mark inactive and set deactivated_at timestamp.
        """
        self.is_active = False
        self.deactivated_at = timezone.now()
        if commit:
            self.save(update_fields=["is_active", "deactivated_at", "updated_at"])

    class Meta:
        abstract = True


class Country(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    iso_code = models.CharField(
        max_length=2,
        unique=True,
        validators=[RegexValidator(regex=r"^[A-Za-z]{2}$", message="ISO code must be 2 letters")],
        help_text="ISO 3166-1 alpha-2 code (e.g., IN, AE)"
    )

    class Meta:
        indexes = [
            models.Index(fields=["iso_code"]),
            models.Index(fields=["name"]),
        ]

    def save(self, *args, **kwargs):
        if self.iso_code:
            self.iso_code = self.iso_code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.iso_code})"


class BankMaster(BaseModel):
    beneficiary_name = models.CharField(max_length=150)
    bank_name = models.CharField(max_length=150)
    branch_name = models.CharField(max_length=150, blank=True)
    branch_address = models.TextField(blank=True)
    account_number = models.CharField(max_length=64, unique=True)
    swift_code = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        indexes = [
            models.Index(fields=["account_number"]),
            models.Index(fields=["swift_code"]),
        ]

    def __str__(self):
        return f"{self.bank_name} - {self.beneficiary_name}"


class Exporter(BaseModel):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="exporters")
    contact_person = models.CharField(max_length=150, blank=True)
    phone_no = models.CharField(max_length=50, blank=True)
    email_id = models.EmailField(blank=True, validators=[EmailValidator()])
    iec_code = models.CharField(max_length=50, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["iec_code"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class RegisteredAddress(BaseModel):
    name = models.CharField(max_length=150)
    address = models.TextField()
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="registered_addresses")
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    exporter = models.OneToOneField(
        Exporter,
        on_delete=models.CASCADE,
        related_name="registered_address_details"
    )

    class Meta:
        verbose_name = "Registered Address"
        verbose_name_plural = "Registered Addresses"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class Consignee(BaseModel):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="consignees")
    contact_person = models.CharField(max_length=150, blank=True)
    phone_no = models.CharField(max_length=50, blank=True)
    email_id = models.EmailField(blank=True, validators=[EmailValidator()])
    tax_number = models.CharField(max_length=50, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class Buyer(BaseModel):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="buyers")
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    tax_number = models.CharField(max_length=50, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class PreCarriage(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Pre-Carriage"
        verbose_name_plural = "Pre-Carriage"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class PlaceOfReceipt(BaseModel):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Place of Receipt"
        verbose_name_plural = "Places of Receipt"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class PaymentTerm(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Payment Term"
        verbose_name_plural = "Payment Terms"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Incoterm(BaseModel):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Incoterm"
        verbose_name_plural = "Incoterms"
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.code if not self.description else f"{self.code} - {self.description}"


class PortOfLoading(BaseModel):
    name = models.CharField(max_length=150)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="ports_of_loading")

    class Meta:
        verbose_name = "Port of Loading"
        verbose_name_plural = "Ports of Loading"
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_loading_port_per_country")
        ]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.country.iso_code}"


class PortOfDischarge(BaseModel):
    name = models.CharField(max_length=150)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="ports_of_discharge")

    class Meta:
        verbose_name = "Port of Discharge"
        verbose_name_plural = "Ports of Discharge"
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_discharge_port_per_country")
        ]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.country.iso_code}"


class FinalDestination(BaseModel):
    name = models.CharField(max_length=150)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="final_destinations")

    class Meta:
        verbose_name = "Final Destination"
        verbose_name_plural = "Final Destinations"
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_final_destination_per_country")
        ]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.country.iso_code}"


class UOM(BaseModel):
    uom = models.CharField(max_length=50, unique=True)
    rate_per_uom = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.uom


# =========================
# Terms & Conditions Templates
# =========================

class TermsAndConditionsTemplate(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    content_html = models.TextField(blank=True)

    class Meta:
        verbose_name = "Terms & Conditions Template"
        verbose_name_plural = "Terms & Conditions Templates"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

# =========================
# Proforma Invoice Models
# =========================

class ProformaInvoice(BaseModel):
    """
    Proforma Invoice header.
    Status workflow:
      - DRAFT
      - PENDING_APPROVAL
      - APPROVED
      - REWORK
    Note: Rejection moves invoice directly to REWORK; audit trail records the rejection.
    """
    STATUS_DRAFT = "DRAFT"
    STATUS_PENDING_APPROVAL = "PENDING_APPROVAL"
    STATUS_APPROVED = "APPROVED"
    STATUS_REWORK = "REWORK"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING_APPROVAL, "Pending Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REWORK, "Rework"),
    ]

    number = models.CharField(max_length=32, unique=True)
    invoice_number = models.CharField(max_length=64, blank=True)
    date = models.DateField(default=timezone.now)

    exporter = models.ForeignKey(Exporter, on_delete=models.PROTECT, related_name="proforma_invoices")
    consignee = models.ForeignKey(Consignee, on_delete=models.PROTECT, related_name="proforma_invoices")
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name="proforma_invoices", null=True, blank=True)

    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.PROTECT, related_name="proforma_invoices")
    incoterm = models.ForeignKey(Incoterm, on_delete=models.PROTECT, related_name="proforma_invoices")

    pre_carriage = models.ForeignKey(PreCarriage, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    place_of_receipt = models.ForeignKey(PlaceOfReceipt, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    port_loading = models.ForeignKey(PortOfLoading, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    port_discharge = models.ForeignKey(PortOfDischarge, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    final_destination = models.ForeignKey(FinalDestination, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    
    origin_country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True, blank=True, related_name="origin_invoices")
    final_destination_country = models.ForeignKey(Country, on_delete=models.PROTECT, null=True, blank=True, related_name="destination_invoices")

    terms_and_conditions = models.TextField(blank=True)
    # Additional header and commercial terms fields
    buyer_order_no = models.CharField(max_length=64, blank=True)
    buyer_order_date = models.DateField(null=True, blank=True)
    other_references = models.TextField(blank=True)
    place_of_receipt_by_pre_carrier = models.ForeignKey(PlaceOfReceipt, on_delete=models.PROTECT, null=True, blank=True, related_name="pre_carrier_receipts")
    vessel_flight_no = models.CharField(max_length=64, blank=True)
    marks_and_nos = models.TextField(blank=True)
    container_no = models.CharField(max_length=64, blank=True)
    kind_of_packages = models.CharField(max_length=128, blank=True)
    validity_for_acceptance = models.DateField(null=True, blank=True)
    validity_for_shipment = models.DateField(null=True, blank=True)
    partial_shipment = models.BooleanField(default=False)
    bank_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transshipment = models.BooleanField(default=False)
    terms_and_conditions_template = models.ForeignKey(TermsAndConditionsTemplate, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")

    bank = models.ForeignKey(BankMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    total_amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    maker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_proforma_invoices")
    last_checker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="checked_proforma_invoices")

    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    reworked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["number"]),
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["consignee"]),
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.number} - {self.consignee.name}"

    def generate_number(self):
        """
        Generate sequential number like: PI-YYYY-0001
        """
        if self.number:
            return
        year = timezone.now().year
        prefix = f"PI-{year}-"
        seq = ProformaInvoice.objects.filter(number__startswith=prefix).count() + 1
        self.number = f"{prefix}{seq:04d}"

    def recalc_total(self, commit: bool = True):
        total = sum(item.amount_usd for item in self.line_items.filter(is_active=True))
        self.total_amount_usd = total
        if commit:
            self.save(update_fields=["total_amount_usd", "updated_at"])

    # Transition helpers (audit trail should be handled in service or viewset)
    def submit(self):
        self.status = self.STATUS_PENDING_APPROVAL
        self.submitted_at = timezone.now()

    def approve(self, checker_user=None):
        self.status = self.STATUS_APPROVED
        self.approved_at = timezone.now()
        if checker_user:
            self.last_checker = checker_user

    def reject_to_rework(self, checker_user=None):
        """
        Logically a rejection, but status transitions to REWORK.
        Caller should create an audit trail entry with action='REJECTED' and notes.
        """
        self.status = self.STATUS_REWORK
        self.reworked_at = timezone.now()
        if checker_user:
            self.last_checker = checker_user

    def save(self, *args, **kwargs):
        # Autogenerate number on first save
        if not self.pk and not self.number:
            self.generate_number()
        super().save(*args, **kwargs)


class ProformaInvoiceLineItem(BaseModel):
    """
    Line items for Proforma Invoice.
    """
    invoice = models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE, related_name="line_items", db_index=True)
    description = models.CharField(max_length=255)
    hs_code = models.CharField(max_length=50, blank=True)
    item_code = models.CharField(max_length=50, blank=True)
    packaging_details = models.CharField(max_length=255, blank=True)
    marks_and_numbers = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit = models.CharField(max_length=32, default="MT")
    unit_price_usd = models.DecimalField(max_digits=14, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.description} ({self.quantity} {self.unit} @ {self.unit_price_usd} USD)"

    def save(self, *args, **kwargs):
        # Compute amount on save
        if self.quantity is not None and self.unit_price_usd is not None:
            try:
                self.amount_usd = (self.quantity * self.unit_price_usd).quantize(self.unit_price_usd.as_tuple())
            except Exception:
                # Fallback simple multiplication
                self.amount_usd = self.quantity * self.unit_price_usd
        super().save(*args, **kwargs)
        # Recalc total on parent invoice
        if self.invoice_id:
            try:
                self.invoice.recalc_total(commit=True)
            except Exception:
                pass


class ProformaInvoiceAuditTrail(models.Model):
    """
    Audit trail for Proforma Invoice actions.
    """
    ACTION_CREATED = "CREATED"
    ACTION_EDITED = "EDITED"
    ACTION_SUBMITTED = "SUBMITTED"
    ACTION_APPROVED = "APPROVED"
    ACTION_REJECTED = "REJECTED"  # leads to REWORK status
    ACTION_REWORKED = "REWORKED"
    ACTION_DEACTIVATED = "DEACTIVATED"
    ACTION_PDF_DOWNLOADED = "PDF_DOWNLOADED"

    ACTION_CHOICES = [
        (ACTION_CREATED, "Created"),
        (ACTION_EDITED, "Edited"),
        (ACTION_SUBMITTED, "Submitted"),
        (ACTION_APPROVED, "Approved"),
        (ACTION_REJECTED, "Rejected"),
        (ACTION_REWORKED, "Reworked"),
        (ACTION_DEACTIVATED, "Deactivated"),
        (ACTION_PDF_DOWNLOADED, "PDF Downloaded"),
    ]

    invoice = models.ForeignKey(ProformaInvoice, on_delete=models.CASCADE, related_name="audit_trail", db_index=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="proforma_invoice_actions")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["invoice"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.invoice.number} - {self.action} by {self.actor}"


# =========================
# Packing List Models
# =========================

class PackingList(BaseModel):
    """
    Packing List header.
    Status workflow:
      - DRAFT
      - PENDING_APPROVAL
      - APPROVED
      - REWORK
    """
    STATUS_DRAFT = "DRAFT"
    STATUS_PENDING_APPROVAL = "PENDING_APPROVAL"
    STATUS_APPROVED = "APPROVED"
    STATUS_REWORK = "REWORK"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING_APPROVAL, "Pending Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REWORK, "Rework"),
    ]

    number = models.CharField(max_length=32, unique=True)
    invoice_number = models.CharField(max_length=64, blank=True)
    date = models.DateField(default=timezone.now)

    # Header details
    exporter = models.ForeignKey(Exporter, on_delete=models.PROTECT, related_name="packing_lists")
    consignee = models.ForeignKey(Consignee, on_delete=models.PROTECT, related_name="packing_lists")
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name="packing_lists", null=True, blank=True)
    notify_party = models.TextField(blank=True, help_text="Can be a dropdown or free text")

    # Order References
    po_number = models.CharField(max_length=64, blank=True)
    po_date = models.DateField(null=True, blank=True)
    lc_number = models.CharField(max_length=64, blank=True)
    lc_date = models.DateField(null=True, blank=True)
    bl_number = models.CharField(max_length=64, blank=True)
    bl_date = models.DateField(null=True, blank=True)
    so_number = models.CharField(max_length=64, blank=True)
    so_date = models.DateField(null=True, blank=True)
    other_ref = models.CharField(max_length=64, blank=True)
    other_ref_date = models.DateField(null=True, blank=True)

    # Shipping & Logistics (Header-level, selectable from master data)
    pre_carriage = models.ForeignKey(
        PreCarriage, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_pre_carriage"
    )
    place_of_receipt = models.ForeignKey(
        PlaceOfReceipt, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_place_of_receipt"
    )
    place_of_receipt_by_pre_carrier = models.ForeignKey(
        PlaceOfReceipt, on_delete=models.PROTECT, null=True, blank=True, related_name="pl_pre_carrier_receipts"
    )
    vessel_flight_no = models.CharField(max_length=64, blank=True)
    port_loading = models.ForeignKey(
        PortOfLoading, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_port_loading"
    )
    port_discharge = models.ForeignKey(
        PortOfDischarge, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_port_discharge"
    )
    final_destination = models.ForeignKey(
        FinalDestination, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_final_destination"
    )

    # Commercial terms
    payment_term = models.ForeignKey(
        PaymentTerm, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_payment_term"
    )
    incoterm = models.ForeignKey(
        Incoterm, on_delete=models.PROTECT, null=True, blank=True, related_name="packing_lists_incoterm"
    )

    # Countries
    origin_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, blank=True, related_name="origin_packing_lists"
    )
    final_destination_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, blank=True, related_name="destination_packing_lists"
    )

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)

    maker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_packing_lists")
    last_checker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="checked_packing_lists")

    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    reworked_at = models.DateTimeField(null=True, blank=True)

    # Link to ProformaInvoice (optional)
    proforma_invoice = models.OneToOneField(
        ProformaInvoice,
        on_delete=models.SET_NULL,
        related_name="packing_list",
        null=True, blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["number"]),
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["consignee"]),
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.number} - {self.consignee.name}"

    def generate_number(self):
        if self.number:
            return
        year = timezone.now().year
        prefix = f"PL-{year}-"
        seq = PackingList.objects.filter(number__startswith=prefix).count() + 1
        self.number = f"{prefix}{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.number:
            self.generate_number()
        super().save(*args, **kwargs)


class PackingListContainer(BaseModel):
    packing_list = models.ForeignKey(PackingList, on_delete=models.CASCADE, related_name="containers")
    container_reference = models.CharField(max_length=128, blank=True)
    marks_and_numbers = models.TextField(blank=True)
    net_weight = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    tare_weight = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    gross_weight = models.DecimalField(max_digits=14, decimal_places=3, default=0, editable=False)

    def __str__(self):
        return f"Container {self.container_reference} for PL {self.packing_list.number}"

    def save(self, *args, **kwargs):
        # Auto-calculate gross weight = net + tare
        try:
            net = self.net_weight or Decimal("0")
            tare = self.tare_weight or Decimal("0")
            self.gross_weight = net + tare
        except Exception:
            try:
                self.gross_weight = (self.net_weight or 0) + (self.tare_weight or 0)
            except Exception:
                pass
        super().save(*args, **kwargs)


class PackingListContainerItem(BaseModel):
    container = models.ForeignKey(PackingListContainer, on_delete=models.CASCADE, related_name="items")
    hsn_code = models.CharField(max_length=50, blank=True)
    item_code = models.CharField(max_length=50, blank=True)
    packages_number_and_kind = models.CharField(max_length=128)
    description_of_goods = models.TextField()
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    uom = models.ForeignKey(UOM, on_delete=models.PROTECT, null=True, blank=True)
    batch_details = models.CharField(max_length=128, blank=True)


    def __str__(self):
        return f"Item {self.item_code} in {self.container.container_reference}"


# =========================
# Commercial Invoice Models
# =========================

class CommercialInvoice(BaseModel):
    """
    Commercial Invoice header.
    Status workflow:
      - DRAFT
      - PENDING_APPROVAL
      - APPROVED
      - REJECTED
      - DISABLED (read-only terminal status; still viewable)
    """
    STATUS_DRAFT = "DRAFT"
    STATUS_PENDING_APPROVAL = "PENDING_APPROVAL"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_DISABLED = "DISABLED"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING_APPROVAL, "Pending Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_DISABLED, "Disabled"),
    ]

    number = models.CharField(max_length=32, unique=True)
    invoice_number = models.CharField(max_length=64, blank=True)
    date = models.DateField(default=timezone.now)

    exporter = models.ForeignKey(Exporter, on_delete=models.PROTECT, related_name="commercial_invoices")
    consignee = models.ForeignKey(Consignee, on_delete=models.PROTECT, related_name="commercial_invoices")
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT, related_name="commercial_invoices", null=True, blank=True)

    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.PROTECT, related_name="commercial_invoices")
    incoterm = models.ForeignKey(Incoterm, on_delete=models.PROTECT, related_name="commercial_invoices")
    bank = models.ForeignKey(BankMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="commercial_invoices")
    packing_list = models.ForeignKey(PackingList, on_delete=models.PROTECT, null=True, blank=True, related_name="commercial_invoices")

    # Totals
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Charges and L/C details
    fob_rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    freight = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    insurance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    lc_details = models.TextField(blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)

    maker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_commercial_invoices")
    last_checker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="checked_commercial_invoices")

    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["number"]),
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["consignee"]),
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.number} - {self.consignee.name}"

    def generate_number(self):
        """
        Generate sequential number like: CI-YYYY-0001
        """
        if self.number:
            return
        year = timezone.now().year
        prefix = f"CI-{year}-"
        seq = CommercialInvoice.objects.filter(number__startswith=prefix).count() + 1
        self.number = f"{prefix}{seq:04d}"

    def recalc_total(self, commit: bool = True):
        total_usd = sum(item.amount_usd for item in self.line_items.filter(is_active=True))
        self.total_amount_usd = total_usd
        # If local amount is tracked separately, keep as is; else mirror USD
        if self.amount is None or self.amount == 0:
            self.amount = total_usd
        if commit:
            self.save(update_fields=["amount", "total_amount_usd", "updated_at"])

    # Workflow transitions
    def submit(self):
        if self.status in {self.STATUS_DRAFT, self.STATUS_REJECTED}:
            self.status = self.STATUS_PENDING_APPROVAL
            self.submitted_at = timezone.now()

    def approve(self, checker_user=None):
        if self.status in {self.STATUS_PENDING_APPROVAL, self.STATUS_REJECTED}:
            self.status = self.STATUS_APPROVED
            self.approved_at = timezone.now()
            if checker_user:
                self.last_checker = checker_user

    def reject(self, checker_user=None):
        if self.status == self.STATUS_PENDING_APPROVAL:
            self.status = self.STATUS_REJECTED
            self.rejected_at = timezone.now()
            if checker_user:
                self.last_checker = checker_user

    def disable(self):
        """
        Move to DISABLED (terminal read-only status). Keep is_active=True for visibility.
        """
        if self.status == self.STATUS_APPROVED:
            self.status = self.STATUS_DISABLED
            self.disabled_at = timezone.now()

    def save(self, *args, **kwargs):
        # Autogenerate number on first save
        if not self.pk and not self.number:
            self.generate_number()
        super().save(*args, **kwargs)


class CommercialInvoiceLineItem(BaseModel):
    """
    Line items for Commercial Invoice.
    """
    invoice = models.ForeignKey(CommercialInvoice, on_delete=models.CASCADE, related_name="line_items", db_index=True)
    description = models.CharField(max_length=255)
    hs_code = models.CharField(max_length=50, blank=True)
    item_code = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit = models.CharField(max_length=32, default="MT")
    unit_price_usd = models.DecimalField(max_digits=14, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.description} ({self.quantity} {self.unit} @ {self.unit_price_usd} USD)"

    def save(self, *args, **kwargs):
        # Compute amount on save
        if self.quantity is not None and self.unit_price_usd is not None:
            try:
                self.amount_usd = (self.quantity * self.unit_price_usd).quantize(self.unit_price_usd.as_tuple())
            except Exception:
                self.amount_usd = self.quantity * self.unit_price_usd
        super().save(*args, **kwargs)
        # Recalc total on parent invoice
        if self.invoice_id:
            try:
                self.invoice.recalc_total(commit=True)
            except Exception:
                pass


class CommercialInvoiceAuditTrail(models.Model):
    """
    Audit trail for Commercial Invoice actions.
    """
    ACTION_CREATED = "CREATED"
    ACTION_EDITED = "EDITED"
    ACTION_SUBMITTED = "SUBMITTED"
    ACTION_APPROVED = "APPROVED"
    ACTION_REJECTED = "REJECTED"
    ACTION_DISABLED = "DISABLED"
    ACTION_PDF_DRAFT_DOWNLOADED = "PDF_DRAFT_DOWNLOADED"
    ACTION_PDF_DOWNLOADED = "PDF_DOWNLOADED"

    ACTION_CHOICES = [
        (ACTION_CREATED, "Created"),
        (ACTION_EDITED, "Edited"),
        (ACTION_SUBMITTED, "Submitted"),
        (ACTION_APPROVED, "Approved"),
        (ACTION_REJECTED, "Rejected"),
        (ACTION_DISABLED, "Disabled"),
        (ACTION_PDF_DRAFT_DOWNLOADED, "Draft PDF Downloaded"),
        (ACTION_PDF_DOWNLOADED, "PDF Downloaded"),
    ]

    invoice = models.ForeignKey(CommercialInvoice, on_delete=models.CASCADE, related_name="audit_trail", db_index=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="commercial_invoice_actions")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["invoice"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.invoice.number} - {self.action} by {self.actor}"
