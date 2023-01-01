from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import Http404, HttpResponseForbidden


@login_required
def proforma_invoice(request):
    """
    Proforma Invoice listing page (searchable, paginated).
    Pass role flags for gating Create and row actions.
    """
    user = request.user
    is_admin = user.is_superuser
    is_maker = is_admin or user.groups.filter(name="Maker").exists()
    is_checker = is_admin or user.groups.filter(name="Checker").exists()
    can_create = is_maker or is_admin
    return render(
        request,
        "OfficeApps/proforma_invoice.html",
        {
            "is_admin": is_admin,
            "is_maker": is_maker,
            "is_checker": is_checker,
            "can_create": can_create,
        },
    )

@login_required
def proforma_invoice_create(request):
    """
    Proforma Invoice create/edit page (full form).
    Accessible to Admin and Maker.
    """
    user = request.user
    is_admin = user.is_superuser
    is_maker = is_admin or user.groups.filter(name="Maker").exists()
    is_checker = is_admin or user.groups.filter(name="Checker").exists()

    if not (is_admin or is_maker):
        return HttpResponseForbidden("Not allowed to create Proforma Invoice.")

    return render(
        request,
        "OfficeApps/proforma_invoice_create.html",
        {
            "is_admin": is_admin,
            "is_maker": is_maker,
            "is_checker": is_checker,
        },
    )


@login_required
def proforma_invoice_detail(request, pk: int):
    """
    Proforma Invoice detail page.
    Shows full invoice data, line items, totals, T&C, status and audit trail.
    """
    # Only pass role flags; data will be fetched client-side via API.
    user = request.user
    is_admin = user.is_superuser
    is_maker = is_admin or user.groups.filter(name="Maker").exists()
    is_checker = is_admin or user.groups.filter(name="Checker").exists()
    return render(
        request,
        "OfficeApps/proforma_invoice_detail.html",
        {
            "invoice_id": pk,
            "is_admin": is_admin,
            "is_maker": is_maker,
            "is_checker": is_checker,
        },
    )


@login_required
def master_data(request):
    """
    Master Data page.
    """
    can_edit = False
    if request.user.is_authenticated:
        can_edit = request.user.is_superuser or request.user.groups.filter(name="Checker").exists()
    return render(request, "OfficeApps/master_data.html", {"can_edit": can_edit})

def logout_view(request):
    """
    Log out the user and redirect to login page. Allows GET for convenience.
    """
    logout(request)
    return redirect("OfficeApps:login")


def home_redirect(request):
    """
    Public entry point:
    - If authenticated, send to app home (proforma invoice).
    - If not authenticated, send to login.
    """
    if request.user.is_authenticated:
        return redirect("OfficeApps:proforma_invoice")
    return redirect("OfficeApps:login")
