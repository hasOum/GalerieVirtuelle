from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.db import transaction, models
from django.db.models import Q, Count
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .forms import RegisterForm, OeuvreForm, PaiementForm
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
    Notification,
    Utilisateur,
)


# ======================
# Helper: Créer une notification
# ======================
def creer_notification(utilisateur, titre, message, type_notif='information', exposition=None):
    """
    Crée une notification pour un utilisateur
    
    Args:
        utilisateur: L'utilisateur destinataire
        titre: Titre de la notification
        message: Contenu du message
        type_notif: Type de notification ('exposition', 'mise_a_jour', 'information', 'alerte')
        exposition: Exposition liée (optionnel)
    """
    return Notification.objects.create(
        utilisateur=utilisateur,
        titre=titre,
        message=message,
        type_notif=type_notif,
        exposition=exposition,
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
        # Clear any previous messages
        storage = messages.get_messages(request)
        storage.used = True

    return render(request, "galerie/auth/register.html", {"form": form})


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

    return render(request, "galerie/auth/login.html", {"form": form})


# ======================
# Profile Edit
# ======================
@login_required(login_url="galerie:login")
def profile_edit(request):
    """Édition du profil utilisateur"""
    if request.method == "POST":
        user = request.user
        
        # Récupérer les données POST
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        
        # Valider email unique
        from django.core.exceptions import ValidationError
        from django.contrib.auth.models import User
        
        if email and email != user.email:
            if User.objects.filter(email=email).exists():
                messages.error(request, "Cet email est déjà utilisé.")
                return render(request, "galerie/profile/profile_edit.html", {"user": user})
        
        # Mettre à jour
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        messages.success(request, "Profil mis à jour avec succès!")
        return redirect("galerie:profile_edit")
    
    return render(request, "galerie/profile/profile_edit.html")


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
    return render(request, "galerie/dashboard/client_dashboard.html")


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
        "galerie/dashboard/artiste_dashboard.html",
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
        .select_related("oeuvre", "commande", "commande__utilisateur")
        .order_by("-commande__date_commande")
    )

    # Calculer le total des ventes
    total_ventes = 0
    for vente in ventes:
        total_ventes += vente.sous_total

    # Compter les ventes par statut
    ventes_payees = ventes.filter(commande__statut="payee").count()
    ventes_en_cours = ventes.filter(commande__statut="en_cours").count()

    return render(
        request,
        "galerie/orders/artiste_sales.html",
        {
            "artiste": artiste,
            "ventes": ventes,
            "total_ventes": total_ventes,
            "ventes_payees": ventes_payees,
            "ventes_en_cours": ventes_en_cours,
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

    # Statistiques générales
    total_oeuvres = Oeuvre.objects.count()
    total_artistes = Artiste.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_commandes = Commande.objects.count()
    
    # Revenu total
    total_revenue = sum(cmd.montant_total for cmd in Commande.objects.all()) if Commande.objects.exists() else 0
    
    # Oeuvres en attente
    oeuvres_attente = (
        Oeuvre.objects.filter(statut=Oeuvre.Statut.EN_ATTENTE)
        .select_related("artiste")
        .order_by("-date_soumission")
    )
    oeuvres_attente_count = oeuvres_attente.count()
    
    # Top 5 artistes par nombre d'oeuvres
    top_artistes = (
        Artiste.objects.annotate(nb_oeuvres=models.Count('oeuvres'))
        .order_by('-nb_oeuvres')[:5]
    )
    
    # Top 5 oeuvres les plus vendues
    top_oeuvres = (
        Oeuvre.objects.annotate(nb_ventes=Count('lignes_commande'))
        .order_by('-nb_ventes')[:5]
    )
    
    # Statut des commandes
    commandes_en_cours = Commande.objects.filter(statut=Commande.Statut.EN_COURS).count()
    commandes_payees = Commande.objects.filter(statut=Commande.Statut.PAYEE).count()
    commandes_validees = Commande.objects.filter(statut=Commande.Statut.VALIDEE).count()
    
    # Dernières commandes
    dernieres_commandes = Commande.objects.order_by('-date_commande')[:5]
    
    # Statistiques utilisateurs
    new_users_count = Utilisateur.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    context = {
        "oeuvres_attente": oeuvres_attente,
        "total_oeuvres": total_oeuvres,
        "total_artistes": total_artistes,
        "total_utilisateurs": total_utilisateurs,
        "total_commandes": total_commandes,
        "total_revenue": total_revenue,
        "oeuvres_attente_count": oeuvres_attente_count,
        "top_artistes": top_artistes,
        "top_oeuvres": top_oeuvres,
        "commandes_en_cours": commandes_en_cours,
        "commandes_payees": commandes_payees,
        "commandes_validees": commandes_validees,
        "dernieres_commandes": dernieres_commandes,
        "new_users_count": new_users_count,
    }
    return render(request, "galerie/dashboard/admin_dashboard.html", context)


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
    return render(request, "galerie/orders/admin_validation_list.html", {"oeuvres_attente": oeuvres_attente})


# ======================
# Oeuvres (visiteur) - CBV
# ======================
class OeuvreListView(ListView):
    model = Oeuvre
    template_name = "galerie/shop/oeuvres_list.html"
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
    artiste_id = request.GET.get("artiste", "").strip()
    technique = request.GET.get("technique", "").strip()
    prix_min = request.GET.get("prix_min", "").strip()
    prix_max = request.GET.get("prix_max", "").strip()
    tri = request.GET.get("tri", "recent").strip()

    oeuvres = Oeuvre.objects.filter(statut=Oeuvre.Statut.VALIDE)

    if q:
        oeuvres = oeuvres.filter(
            Q(titre__icontains=q) |
            Q(description__icontains=q) |
            Q(artiste__nom__icontains=q)
        )

    if cat_id:
        oeuvres = oeuvres.filter(categorie_id=cat_id)

    if artiste_id:
        oeuvres = oeuvres.filter(artiste_id=artiste_id)

    if technique:
        oeuvres = oeuvres.filter(technique__icontains=technique)

    if prix_min:
        try:
            oeuvres = oeuvres.filter(prix__gte=float(prix_min))
        except ValueError:
            pass

    if prix_max:
        try:
            oeuvres = oeuvres.filter(prix__lte=float(prix_max))
        except ValueError:
            pass

    # Tri
    if tri == "prix_croissant":
        oeuvres = oeuvres.order_by("prix")
    elif tri == "prix_decroissant":
        oeuvres = oeuvres.order_by("-prix")
    elif tri == "titre_az":
        oeuvres = oeuvres.order_by("titre")
    elif tri == "titre_za":
        oeuvres = oeuvres.order_by("-titre")
    elif tri == "annee_croissant":
        oeuvres = oeuvres.order_by("annee_creation")
    elif tri == "annee_decroissant":
        oeuvres = oeuvres.order_by("-annee_creation")
    else:  # recent (défaut)
        oeuvres = oeuvres.order_by("-date_soumission")

    categories = Categorie.objects.all()
    artistes = Artiste.objects.all()
    techniques = Oeuvre.objects.filter(statut=Oeuvre.Statut.VALIDE).values_list("technique", flat=True).distinct()
    techniques = sorted(set(t for t in techniques if t))  # Remove duplicates and sort

    return render(
        request,
        "galerie/shop/oeuvres_list.html",
        {
            "oeuvres": oeuvres,
            "categories": categories,
            "artistes": artistes,
            "techniques": techniques,
            "q": q,
            "categorie_selected": cat_id,
            "artiste_selected": artiste_id,
            "technique": technique,
            "prix_min": prix_min,
            "prix_max": prix_max,
            "tri": tri,
        },
    )


def oeuvre_detail(request, pk):
    oeuvre = get_object_or_404(Oeuvre, pk=pk)
    return render(request, "galerie/shop/oeuvre_detail.html", {"oeuvre": oeuvre})


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

    return render(request, "galerie/shop/expositions_list.html", {"expositions": qs})


def exposition_detail(request, pk):
    """Affiche les détails d'une exposition"""
    exposition = get_object_or_404(Exposition, pk=pk)
    oeuvres = exposition.oeuvres.all()
    tickets = exposition.tickets.all() if hasattr(exposition, 'tickets') else []
    
    context = {
        "exposition": exposition,
        "oeuvres": oeuvres,
        "tickets": tickets,
    }
    return render(request, "galerie/shop/exposition_detail.html", context)


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
        "galerie/shop/oeuvre_form.html",
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
        "galerie/shop/oeuvre_form.html",
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


def cart_detail(request):
    """
    Vue pour afficher le panier de l'utilisateur stocké en base de données.
    Utilise le modèle Panier lié à l'utilisateur.
    """
    from decimal import Decimal
    
    if not request.user.is_authenticated:
        # Rediriger vers login si non authentifié
        return redirect("login")
    
    panier = get_or_create_panier(request.user)
    items = panier.items.all()
    
    # Calculer les totaux
    subtotal = sum(item.quantite * item.oeuvre.prix for item in items) or Decimal('0.00')
    shipping = Decimal('5.00') if subtotal > 0 else Decimal('0.00')
    tax = (subtotal + shipping) * Decimal('0.20')  # TVA 20%
    total = subtotal + shipping + tax
    
    context = {
        "panier": panier,
        "cart_items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
    
    return render(request, "galerie/cart/cart_detail.html", context)


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
@login_required
def cart_remove(request, oeuvre_id):
    panier = get_or_create_panier(request.user)
    item = get_object_or_404(PanierItem, panier=panier, oeuvre_id=oeuvre_id)
    item.delete()
    messages.info(request, "Article supprimé du panier.")
    return redirect("galerie:cart_detail")


@login_required
def cart_clear(request):
    """Vider tout le panier"""
    panier = get_or_create_panier(request.user)
    panier.items.all().delete()
    messages.success(request, "Panier vidé.")
    return redirect("galerie:cart_detail")


@login_required
@transaction.atomic
def checkout(request):
    """Créer une commande depuis le panier de la base de données"""
    from decimal import Decimal
    
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée.")
        return redirect("galerie:cart_detail")
    
    # Récupérer le panier de l'utilisateur
    panier = get_or_create_panier(request.user)
    items = panier.items.all()
    
    if not items.exists():
        messages.error(request, "Votre panier est vide.")
        return redirect("galerie:cart_detail")
    
    # Vérifier les stocks
    for item in items:
        if item.quantite > item.oeuvre.stock:
            error_msg = f"Stock insuffisant pour: {item.oeuvre.titre}"
            messages.error(request, error_msg)
            return redirect("galerie:cart_detail")
    
    # Calculer le total
    subtotal = sum(item.quantite * item.oeuvre.prix for item in items) or Decimal('0.00')
    shipping = Decimal('5.00') if subtotal > 0 else Decimal('0.00')
    tax = (subtotal + shipping) * Decimal('0.20')
    total = subtotal + shipping + tax
    
    # Créer la commande
    commande = Commande.objects.create(
        utilisateur=request.user,
        montant_total=total
    )
    
    # Créer les lignes de commande et mettre à jour le stock
    for item in items:
        LigneCommande.objects.create(
            commande=commande,
            oeuvre=item.oeuvre,
            quantite=item.quantite,
            prix_unitaire=item.oeuvre.prix,
        )
        item.oeuvre.stock -= item.quantite
        item.oeuvre.save(update_fields=["stock"])
    
    # Vider le panier
    panier.items.all().delete()
    
    messages.success(request, f"Commande #{commande.id} créée. Procédez au paiement.")
    return redirect("galerie:order_pay", order_id=commande.id)


@login_required
def orders_list(request):
    commandes = Commande.objects.filter(utilisateur=request.user).order_by("-date_commande")
    return render(request, "galerie/orders/orders_list.html", {"commandes": commandes})


@login_required
def order_pay(request, order_id):
    """Page de paiement avec formulaire de coordonnées bancaires"""
    
    commande = get_object_or_404(Commande, pk=order_id, utilisateur=request.user)

    if commande.statut != Commande.Statut.EN_COURS:
        messages.info(request, "Cette commande n'est pas payable.")
        return redirect("galerie:orders_list")

    if request.method == "POST":
        form = PaiementForm(request.POST)
        if form.is_valid():
            # Sauvegarder les détails du paiement
            try:
                Paiement.objects.update_or_create(
                    commande=commande,
                    defaults={
                        "methode": Paiement.Methode.CARTE_BANCAIRE,
                        "statut": Paiement.Statut.SUCCES,
                        "montant": commande.montant_total,
                        "reference": f"PAIEMENT-{commande.id}-{request.user.id}",
                    },
                )
                
                # Marquer la commande comme payée
                commande.statut = Commande.Statut.PAYEE
                commande.save(update_fields=["statut"])
                
                messages.success(request, "✅ Paiement accepté! Votre commande a été confirmée.")
                return redirect("galerie:payment_success", order_id=commande.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement du paiement: {str(e)}")
                return redirect("galerie:orders_list")
    else:
        form = PaiementForm()

    # Récupérer les articles de la commande
    lignes = LigneCommande.objects.filter(commande=commande).select_related("oeuvre")
    
    context = {
        "commande": commande,
        "form": form,
        "lignes": lignes,
    }
    return render(request, "galerie/payment/order_pay.html", context)


@login_required
def payment_success(request, order_id):
    """Page de succès après paiement"""
    commande = get_object_or_404(Commande, pk=order_id, utilisateur=request.user)
    
    # Mettre à jour le statut de la commande
    commande.statut = Commande.Statut.PAYEE
    commande.save(update_fields=["statut"])
    
    # Mettre à jour le statut du paiement
    paiement = Paiement.objects.filter(commande=commande).first()
    if paiement:
        paiement.statut = Paiement.Statut.SUCCES
        paiement.save(update_fields=["statut"])
    
    # Vider le panier
    if request.user.is_authenticated:
        panier = get_or_create_panier(request.user)
        panier.items.all().delete()
    
    messages.success(request, "✅ Paiement réussi! Votre commande a été confirmée.")
    return render(request, "galerie/payment/payment_success.html", {"commande": commande})


@login_required
def order_cancel(request, order_id):
    commande = get_object_or_404(Commande, pk=order_id, utilisateur=request.user)

    if commande.statut != Commande.Statut.EN_COURS:
        messages.error(request, "Annulation impossible (commande déjà payée/annulée).")
        return redirect("galerie:orders_list")

    commande.statut = Commande.Statut.ANNULEE
    commande.save(update_fields=["statut"])

    messages.success(request, "Commande annulée (en attente de règlement par admin).")
    return redirect("galerie:orders_list")


# ======================
# NOTIFICATIONS
# ======================
@login_required
def notifications_list(request):
    """Afficher les notifications de l'utilisateur"""
    notifications = Notification.objects.filter(
        utilisateur=request.user
    ).order_by("-date_creation")
    
    # Marquer les notifications comme lues en masse
    unread = notifications.filter(statut=Notification.Statut.NON_LUE)
    if request.GET.get("mark_read") == "1":
        unread.update(statut=Notification.Statut.LUE, date_lecture=timezone.now())
    
    unread_count = notifications.filter(statut=Notification.Statut.NON_LUE).count()
    
    return render(
        request,
        "galerie/notifications/notifications_list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        },
    )


@login_required
def notification_mark_read(request, pk):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, pk=pk, utilisateur=request.user)
    notification.marquer_comme_lue()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True})
    
    return redirect("galerie:notifications_list")


@login_required
def notification_delete(request, pk):
    """Supprimer une notification"""
    notification = get_object_or_404(Notification, pk=pk, utilisateur=request.user)
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True})
    
    messages.info(request, "Notification supprimée.")
    return redirect("galerie:notifications_list")


@login_required
def notification_send(request):
    """Page pour l'admin pour envoyer une notification"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Accès refusé : réservé aux administrateurs.")
        return redirect("galerie:home")
    
    if request.method == "POST":
        titre = request.POST.get("titre", "").strip()
        message = request.POST.get("message", "").strip()
        type_notif = request.POST.get("type_notif", "information").strip()
        destinataires = request.POST.getlist("destinataires")  # IDs des utilisateurs
        exposition_id = request.POST.get("exposition", None)
        
        if not titre or not message:
            messages.error(request, "Le titre et le message sont obligatoires.")
            return redirect("galerie:notification_send")
        
        if not destinataires:
            messages.error(request, "Vous devez sélectionner au moins un destinataire.")
            return redirect("galerie:notification_send")
        
        exposition = None
        if exposition_id:
            try:
                exposition = Exposition.objects.get(pk=exposition_id)
            except Exposition.DoesNotExist:
                messages.error(request, "L'exposition sélectionnée n'existe pas.")
                return redirect("galerie:notification_send")
        
        # Créer une notification pour chaque destinataire
        count = 0
        for user_id in destinataires:
            try:
                user = Utilisateur.objects.get(pk=user_id)
                creer_notification(
                    utilisateur=user,
                    titre=titre,
                    message=message,
                    type_notif=type_notif,
                    exposition=exposition,
                )
                count += 1
            except Utilisateur.DoesNotExist:
                continue
        
        messages.success(request, f"✅ {count} notification(s) envoyée(s).")
        return redirect("galerie:admin_dashboard")
    
    # GET request - afficher le formulaire
    all_users = Utilisateur.objects.all().order_by("username")
    expositions = Exposition.objects.all()
    
    context = {
        "all_users": all_users,
        "expositions": expositions,
    }
    return render(request, "galerie/notifications/notification_send.html", context)
