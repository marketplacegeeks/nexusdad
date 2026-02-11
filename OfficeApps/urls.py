from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView
from rest_framework.routers import DefaultRouter
from .api import (
    CountryViewSet,
    BankMasterViewSet,
    ExporterViewSet,
    ConsigneeViewSet,
    BuyerViewSet,
    PreCarriageViewSet,
    PlaceOfReceiptViewSet,
    PaymentTermViewSet,
    IncotermViewSet,
    PortOfLoadingViewSet,
    PortOfDischargeViewSet,
    FinalDestinationViewSet,
    TermsAndConditionsTemplateViewSet,
    ProformaInvoiceViewSet,
    RegisteredAddressViewSet,
    PackingListViewSet,
    UOMViewSet,
    CommercialInvoiceViewSet,
)

app_name = "OfficeApps"

# DRF API router for master data
router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="countries")
router.register(r"banks", BankMasterViewSet, basename="banks")
router.register(r"exporters", ExporterViewSet, basename="exporters")
router.register(r"consignees", ConsigneeViewSet, basename="consignees")
router.register(r"buyers", BuyerViewSet, basename="buyers")
router.register(r"pre-carriage", PreCarriageViewSet, basename="pre-carriage")
router.register(r"place-of-receipt", PlaceOfReceiptViewSet, basename="place-of-receipt")
router.register(r"payment-terms", PaymentTermViewSet, basename="payment-terms")
router.register(r"uom", UOMViewSet, basename="uom")
router.register(r"incoterms", IncotermViewSet, basename="incoterms")
router.register(r"ports-loading", PortOfLoadingViewSet, basename="ports-loading")
router.register(r"ports-discharge", PortOfDischargeViewSet, basename="ports-discharge")
router.register(r"final-destinations", FinalDestinationViewSet, basename="final-destinations")
router.register(r"terms-conditions", TermsAndConditionsTemplateViewSet, basename="terms-conditions")
router.register(r"proforma-invoices", ProformaInvoiceViewSet, basename="proforma-invoices")
router.register(r"registered-addresses", RegisteredAddressViewSet, basename="registered-addresses")
router.register(r"packing-lists", PackingListViewSet, basename="packing-lists")
router.register(r"commercial-invoices", CommercialInvoiceViewSet, basename="commercial-invoices")

urlpatterns = [
    # Public auth endpoints
    path("", views.home_redirect, name="home_redirect"),
    path("login/", LoginView.as_view(template_name="OfficeApps/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Private application pages (require login via view decorators)
    path("app/proforma-invoice/", views.proforma_invoice, name="proforma_invoice"),
    path("app/proforma-invoice/create/", views.proforma_invoice_create, name="proforma_invoice_create"),
    path("app/proforma-invoice/<int:pk>/", views.proforma_invoice_detail, name="proforma_invoice_detail"),
    path("app/master-data/", views.master_data, name="master_data"),
    path("app/packing-list/", views.packing_list, name="packing_list"),
    path("app/packing-list/create/", views.packing_list_create, name="packing_list_create"),
    path("app/commercial-invoice/", views.commercial_invoice, name="commercial_invoice"),
    path("app/commercial-invoice/create/", views.commercial_invoice_create, name="commercial_invoice_create"),

    # APIs (protected via DRF permissions)
    path("api/master/", include(router.urls)),
]
