from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from .forms import RegisterForm, OeuvreForm
from .models import (
    Oeuvre,
    Exposition,
    Categorie,
    Artiste,
    Panier,
    PanierItem,
    Commande,
    LigneCommande,
    Paiement,
)

# ======================
# Home page
# ======================
def home(request):
    return render(request, "galerie/home.html")


# ======================
# Register
# ======================
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Si artiste, profil créé par RegisterForm.save() (selon ton forms.py)
            login(request, user)
            messages.success(request, "Compte créé avec succès !")
            return redirect("galerie:home")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


# ======================
# Login (custom)
# ======================
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # 1) Respecter "next" (priorité)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url:
                return redirect(next_url)

            # 2) Sinon redirection selon type
            if user.is_staff or user.is_superuser:
                return redirect("galerie:admin_dashboard")

            try:
                user.artiste  # profil artiste ?
                return redirect("galerie:artiste_dashboard")
            except ObjectDoesNotExist:
                return redirect("galerie:client_dashboard")

        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})


# ======================
# Logout
# ======================
def logout_view(request):
    logout(request)
    return redirect("galerie:home")


# ======================
# Client Dashboard
# ======================
@login_required
def client_dashboard(request):
    return render(request, "galerie/client_dashboard.html")


# ======================
# ARTISTE : Dashboard
# ======================
@login_required
def artiste_dashboard(request):
    try:
        artiste = request.user.artiste
        oeuvres = artiste.oeuvres.all().order_by("-date_soumission")
    except Artiste.DoesNotExist:
        messages.warning(request, "Vous n'êtes pas enregistré comme artiste.")
        return redirect("galerie:home")

    return render(
        request,
        "galerie/artiste_dashboard.html",
        {"artiste": artiste, "oeuvres": oeuvres},
    )


@login_required
def artiste_sales(request):
    """Vue pour voir les ventes d'un artiste"""
    try:
        artiste = request.user.artiste
    except Artiste.DoesNotExist:
        messages.warning(request, "Vous n'êtes pas enregistré comme artiste.")
        return redirect("galerie:home")

    # Récupérer les lignes de commande pour les œuvres de cet artiste
    ventes = (
        LigneCommande.objects
        .filter(oeuvre__artiste=artiste)
        .select_related("oeuvre", "commande")
        .order_by("-commande__date_commande")
    )

    total_ventes = sum(vente.prix_unitaire * vente.quantite for vente in ventes)

    return render(
        request,
        "galerie/artiste_sales.html",
        {
            "artiste": artiste,
            "ventes": ventes,
            "total_ventes": total_ventes,
        },
    )


# ======================
# ADMIN : Dashboard
# ======================
@login_required
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès refusé : réservé aux administrateurs.")
        return redirect("galerie:home")

    oeuvres_attente = (
        Oeuvre.objects.filter(statut=Oeuvre.Statut.EN_ATTENTE)
        .select_related("artiste")
        .order_by("-date_soumission")
    )
    return render(request, "galerie/admin_dashboard.html", {"oeuvres_attente": oeuvres_attente})


def admin_validation_list(request):
    """Liste des œuvres en attente de validation pour les admins"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès refusé : réservé aux administrateurs.")
        return redirect("galerie:home")

    oeuvres_attente = (
        Oeuvre.objects.filter(statut=Oeuvre.Statut.EN_ATTENTE)
        .select_related("artiste")
        .order_by("-date_soumission")
    )
    return render(request, "galerie/admin_validation_list.html", {"oeuvres_attente": oeuvres_attente})


# ======================
# Oeuvres (visiteur) - CBV
# ======================
class OeuvreListView(ListView):
    model = Oeuvre
    template_name = "galerie/oeuvres_list.html"
    context_object_name = "oeuvres"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Oeuvre.objects.filter(statut=Oeuvre.Statut.VALIDE)
            .select_related("categorie", "artiste")
        )
        q = self.request.GET.get("q")
        cat = self.request.GET.get("categorie")

        if q:
            qs = qs.filter(titre__icontains=q)
        if cat:
            qs = qs.filter(categorie_id=cat)

        return qs.order_by("-date_soumission")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Categorie.objects.all()
        context["q"] = self.request.GET.get("q", "")
        context["categorie_selected"] = self.request.GET.get("categorie", "")
        return context


class OeuvreDetailView(DetailView):
    model = Oeuvre
    template_name = "galerie/oeuvre_detail.html"
    context_object_name = "oeuvre"


# ======================
# Oeuvres (visiteur) - FBV (si tu préfères)
# ======================
def oeuvres_list(request):
    q = request.GET.get("q", "").strip()
    cat_id = request.GET.get("categorie", "").strip()

    oeuvres = Oeuvre.objects.filter(statut=Oeuvre.Statut.VALIDE)

    if q:
        oeuvres = oeuvres.filter(
            Q(titre__icontains=q) |
            Q(description__icontains=q) |
            Q(artiste__nom__icontains=q)
        )

    if cat_id:
        oeuvres = oeuvres.filter(categorie_id=cat_id)

    categories = Categorie.objects.all()

    return render(
        request,
        "galerie/oeuvres_list.html",
        {"oeuvres": oeuvres, "categories": categories, "q": q, "categorie_selected": cat_id},
    )


def oeuvre_detail(request, pk):
    oeuvre = get_object_or_404(Oeuvre, pk=pk)
    return render(request, "galerie/oeuvre_detail.html", {"oeuvre": oeuvre})


# ======================
# Expositions
# ======================
class ExpositionListView(ListView):
    model = Exposition
    template_name = "galerie/expositions_list.html"
    context_object_name = "expositions"
    paginate_by = 10
    ordering = ["-date_debut"]


def expositions_list(request):
    qs = Exposition.objects.all()
    q = request.GET.get("q", "").strip()
    lieu = request.GET.get("lieu", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        qs = qs.filter(Q(nom_exposition__icontains=q) | Q(description__icontains=q))
    if lieu:
        qs = qs.filter(lieu__icontains=lieu)
    if date_from:
        qs = qs.filter(date_debut__gte=date_from)
    if date_to:
        qs = qs.filter(date_fin__lte=date_to)

    return render(request, "galerie/expositions_list.html", {"expositions": qs})


# ======================
# ARTISTE : Créer oeuvre
# ======================
@login_required
def oeuvre_create(request):
    try:
        artiste = request.user.artiste
    except Artiste.DoesNotExist:
        messages.error(request, "Vous devez être artiste pour soumettre une œuvre.")
        return redirect("galerie:home")

    if request.method == "POST":
        form = OeuvreForm(request.POST, request.FILES)
        if form.is_valid():
            oeuvre = form.save(commit=False)
            oeuvre.artiste = artiste
            oeuvre.save()
            messages.success(request, "Œuvre soumise avec succès ! En attente de validation.")
            return redirect("galerie:artiste_dashboard")
    else:
        form = OeuvreForm()

    return render(
        request,
        "galerie/oeuvre_form.html",
        {"form": form, "categories": Categorie.objects.all()},
    )


# ======================
# ARTISTE : Modifier oeuvre
# ======================
@login_required
def oeuvre_update(request, pk):
    oeuvre = get_object_or_404(Oeuvre, pk=pk, artiste__user=request.user)

    if oeuvre.statut != Oeuvre.Statut.EN_ATTENTE:
        messages.error(request, "Impossible de modifier une œuvre déjà validée/refusée.")
        return redirect("galerie:artiste_dashboard")

    if request.method == "POST":
        form = OeuvreForm(request.POST, request.FILES, instance=oeuvre)
        if form.is_valid():
            form.save()
            messages.success(request, "Œuvre modifiée avec succès.")
            return redirect("galerie:artiste_dashboard")
    else:
        form = OeuvreForm(instance=oeuvre)

    return render(
        request,
        "galerie/oeuvre_form.html",
        {"form": form, "categories": Categorie.objects.all()},
    )


# ======================
# ADMIN : Valider / Refuser
# ======================
@login_required
def oeuvre_valider(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès refusé.")
        return redirect("galerie:home")

    oeuvre = get_object_or_404(Oeuvre, pk=pk)
    oeuvre.valider()
    messages.success(request, f"Œuvre '{oeuvre.titre}' validée avec succès.")
    return redirect("galerie:admin_dashboard")


@login_required
def oeuvre_refuser(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès refusé.")
        return redirect("galerie:home")

    oeuvre = get_object_or_404(Oeuvre, pk=pk)
    oeuvre.refuser()
    messages.warning(request, f"Œuvre '{oeuvre.titre}' refusée.")
    return redirect("galerie:admin_dashboard")


# ======================
# PANIER / COMMANDES
# ======================
def get_or_create_panier(user):
    panier, _ = Panier.objects.get_or_create(client=user)
    return panier


@login_required
def cart_detail(request):
    panier = get_or_create_panier(request.user)
    return render(request, "galerie/cart_detail.html", {"panier": panier})


@login_required
def cart_add(request, oeuvre_id):
    oeuvre = get_object_or_404(Oeuvre, pk=oeuvre_id)

    if oeuvre.stock <= 0:
        messages.error(request, "Stock insuffisant pour cette œuvre.")
        return redirect("galerie:oeuvre_detail", pk=oeuvre.id)

    panier = get_or_create_panier(request.user)
    item, created = PanierItem.objects.get_or_create(panier=panier, oeuvre=oeuvre)

    if not created:
        if item.quantite + 1 > oeuvre.stock:
            messages.error(request, "Quantité demandée > stock disponible.")
            return redirect("galerie:cart_detail")
        item.quantite += 1
        item.save(update_fields=["quantite"])

    messages.success(request, "Ajouté au panier.")
    return redirect("galerie:cart_detail")


@login_required
def cart_remove(request, oeuvre_id):
    panier = get_or_create_panier(request.user)
    item = get_object_or_404(PanierItem, panier=panier, oeuvre_id=oeuvre_id)
    item.delete()
    messages.info(request, "Article supprimé du panier.")
    return redirect("galerie:cart_detail")


@login_required
@transaction.atomic
def checkout(request):
    panier = get_or_create_panier(request.user)
    items = list(panier.items.select_related("oeuvre"))

    if not items:
        messages.error(request, "Votre panier est vide.")
        return redirect("galerie:cart_detail")

    for it in items:
        if it.quantite > it.oeuvre.stock:
            messages.error(request, f"Stock insuffisant pour: {it.oeuvre.titre}")
            return redirect("galerie:cart_detail")

    commande = Commande.objects.create(client=request.user)

    for it in items:
        LigneCommande.objects.create(
            commande=commande,
            oeuvre=it.oeuvre,
            quantite=it.quantite,
            prix_unitaire=it.oeuvre.prix,
        )
        it.oeuvre.stock -= it.quantite
        it.oeuvre.save(update_fields=["stock"])

    commande.recalculer_total()
    panier.items.all().delete()

    messages.success(request, f"Commande #{commande.id} créée. Procédez au paiement.")
    return redirect("galerie:order_pay", order_id=commande.id)


@login_required
def orders_list(request):
    commandes = Commande.objects.filter(client=request.user).order_by("-date_creation")
    return render(request, "galerie/orders_list.html", {"commandes": commandes})


@login_required
def order_pay(request, order_id):
    commande = get_object_or_404(Commande, pk=order_id, client=request.user)

    if commande.statut != Commande.Statut.EN_ATTENTE:
        messages.info(request, "Cette commande n'est pas payable.")
        return redirect("galerie:orders_list")

    if request.method == "POST":
        methode = request.POST.get("methode")

        Paiement.objects.update_or_create(
            commande=commande,
            defaults={
                "methode": methode,
                "statut": Paiement.Statut.SUCCES,
                "reference": f"REF-{commande.id}",
            },
        )

        commande.statut = Commande.Statut.PAYEE
        commande.save(update_fields=["statut"])

        messages.success(request, "Paiement effectué.")
        return redirect("galerie:orders_list")

    return render(request, "galerie/order_pay.html", {"commande": commande})


@login_required
def order_cancel(request, order_id):
    commande = get_object_or_404(Commande, pk=order_id, client=request.user)

    if commande.statut != Commande.Statut.EN_ATTENTE:
        messages.error(request, "Annulation impossible (commande déjà payée/annulée).")
        return redirect("galerie:orders_list")

    commande.statut = Commande.Statut.ANNULEE
    commande.save(update_fields=["statut"])

    messages.success(request, "Commande annulée (en attente de règlement par admin).")
    return redirect("galerie:orders_list")
