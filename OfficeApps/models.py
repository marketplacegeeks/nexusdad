from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from django.conf import settings


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

    class Meta:
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
    date = models.DateField(default=timezone.now)

    exporter = models.ForeignKey(Exporter, on_delete=models.PROTECT, related_name="proforma_invoices")
    consignee = models.ForeignKey(Consignee, on_delete=models.PROTECT, related_name="proforma_invoices")

    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.PROTECT, related_name="proforma_invoices")
    incoterm = models.ForeignKey(Incoterm, on_delete=models.PROTECT, related_name="proforma_invoices")

    pre_carriage = models.ForeignKey(PreCarriage, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    place_of_receipt = models.ForeignKey(PlaceOfReceipt, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    port_loading = models.ForeignKey(PortOfLoading, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    port_discharge = models.ForeignKey(PortOfDischarge, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")
    final_destination = models.ForeignKey(FinalDestination, on_delete=models.PROTECT, null=True, blank=True, related_name="proforma_invoices")

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
