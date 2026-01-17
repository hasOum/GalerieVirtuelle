from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse

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
                return render(request, "galerie/profile_edit.html", {"user": user})
        
        # Mettre à jour
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        messages.success(request, "Profil mis à jour avec succès!")
        return redirect("galerie:profile_edit")
    
    return render(request, "galerie/profile_edit.html")


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
        .select_related("oeuvre", "commande", "commande__utilisateur")
        .order_by("-commande__date_commande")
    )

    # Ajouter le sous-total calculé à chaque vente
    total_ventes = 0
    for vente in ventes:
        sous_total = float(vente.prix_unitaire) * vente.quantite
        vente.sous_total = sous_total
        total_ventes += sous_total

    # Compter les ventes par statut
    ventes_payees = ventes.filter(commande__statut="payee").count()
    ventes_en_cours = ventes.filter(commande__statut="en_cours").count()

    return render(
        request,
        "galerie/artiste_sales.html",
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
    techniques = [t for t in techniques if t]

    return render(
        request,
        "galerie/oeuvres_list.html",
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


def cart_detail(request):
    """
    Vue pour afficher le panier stocké en localStorage.
    Parse les données JSON du localStorage depuis le template.
    """
    # Contexte par défaut (panier vide)
    context = {
        "cart_items": [],
        "subtotal": 0.00,
        "shipping": 5.00,
        "tax": 0.00,
        "total": 5.00,
    }
    
    return render(request, "galerie/cart_detail.html", context)


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
@login_required
@transaction.atomic
def checkout(request):
    """Créer une commande depuis le panier localStorage"""
    import json
    
    # Récupérer le panier depuis la requête JSON
    try:
        data = json.loads(request.body) if request.body else {}
        cart_data = data.get('cart', [])
    except:
        cart_data = []
    
    if not cart_data:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Votre panier est vide.'
            }, status=400)
        messages.error(request, "Votre panier est vide.")
        return redirect("galerie:cart_detail")
    
    # Vérifier les stocks
    for item in cart_data:
        try:
            oeuvre = Oeuvre.objects.get(pk=item['id'])
            if item['quantity'] > oeuvre.stock:
                error_msg = f"Stock insuffisant pour: {oeuvre.titre}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': error_msg
                    }, status=400)
                messages.error(request, error_msg)
                return redirect("galerie:cart_detail")
        except Oeuvre.DoesNotExist:
            error_msg = f"Œuvre introuvable (ID: {item['id']})"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=404)
            messages.error(request, error_msg)
            return redirect("galerie:cart_detail")
    
    # Créer la commande
    total = sum(item['price'] * item['quantity'] for item in cart_data)
    commande = Commande.objects.create(
        client=request.user,
        total=total
    )
    
    # Créer les lignes de commande et mettre à jour le stock
    for item in cart_data:
        oeuvre = Oeuvre.objects.get(pk=item['id'])
        LigneCommande.objects.create(
            commande=commande,
            oeuvre=oeuvre,
            quantite=item['quantity'],
            prix_unitaire=item['price'],
        )
        oeuvre.stock -= item['quantity']
        oeuvre.save(update_fields=["stock"])
    
    # Vider le panier de la session
    if 'cart' in request.session:
        del request.session['cart']
    
    # Retourner JSON pour les requêtes AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Commande #{commande.id} créée',
            'redirect_url': reverse('galerie:order_pay', kwargs={'order_id': commande.id})
        })
    
    # Sinon redirection classique
    messages.success(request, f"Commande #{commande.id} créée. Procédez au paiement.")
    return redirect("galerie:order_pay", order_id=commande.id)


@login_required
def orders_list(request):
    commandes = Commande.objects.filter(client=request.user).order_by("-date_creation")
    return render(request, "galerie/orders_list.html", {"commandes": commandes})


@login_required
def order_pay(request, order_id):
    import stripe
    from django.conf import settings
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    commande = get_object_or_404(Commande, pk=order_id, client=request.user)

    if commande.statut != Commande.Statut.EN_ATTENTE:
        messages.info(request, "Cette commande n'est pas payable.")
        return redirect("galerie:orders_list")

    if request.method == "POST":
        try:
            # Créer une intention de paiement Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(commande.total * 100),  # Montant en centimes
                currency="eur",
                metadata={
                    "order_id": commande.id,
                    "user_id": request.user.id,
                }
            )
            
            # Sauvegarder les détails du paiement
            Paiement.objects.update_or_create(
                commande=commande,
                defaults={
                    "methode": "stripe",
                    "statut": Paiement.Statut.EN_ATTENTE,
                    "reference": intent.id,
                },
            )
            
            context = {
                "commande": commande,
                "client_secret": intent.client_secret,
                "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
            }
            return render(request, "galerie/order_pay.html", context)
        except Exception as e:
            messages.error(request, f"Erreur lors du paiement: {str(e)}")
            return redirect("galerie:orders_list")

    context = {
        "commande": commande,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, "galerie/order_pay.html", context)


@login_required
def payment_confirm(request, order_id):
    """Endpoint AJAX pour confirmer la création d'une intention de paiement"""
    import stripe
    import json
    from django.conf import settings
    
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        commande = get_object_or_404(Commande, pk=order_id, client=request.user)
        
        # Créer une intention de paiement
        intent = stripe.PaymentIntent.create(
            amount=int(commande.total * 100),
            currency="eur",
            metadata={"order_id": commande.id},
        )
        
        return JsonResponse({"client_secret": intent.client_secret})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def payment_success(request, order_id):
    """Page de succès après paiement"""
    import stripe
    from django.conf import settings
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    commande = get_object_or_404(Commande, pk=order_id, client=request.user)
    
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
    return render(request, "galerie/payment_success.html", {"commande": commande})


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
