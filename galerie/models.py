from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


# ============================================
# 1. MODÈLE UTILISATEUR PERSONNALISÉ
# ============================================

class Utilisateur(AbstractUser):
    """Modèle utilisateur avec 4 rôles : visiteur, artiste, curateur, super_admin"""
    

    ROLES = [
        ("visiteur", "Visiteur"),
        ("artiste", "Artiste"),
        ("curateur", "Curateur"),
        ("super_admin", "Super Admin"),
    ]

    telephone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES, default="visiteur")
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "utilisateur"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ============================================
# 2. MODÈLE ARTISTE
# ============================================

class Artiste(models.Model):
    """Extension du profil Utilisateur pour les artistes"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artiste",
    )

    nom = models.CharField(max_length=150)
    date_naissance = models.DateField(null=True, blank=True)
    nationalite = models.CharField(max_length=100, blank=True)
    biographie = models.TextField(blank=True)
    photo_profil = models.ImageField(upload_to="artistes/", blank=True, null=True)

    class Meta:
        db_table = "artiste"
        verbose_name = "Artiste"
        verbose_name_plural = "Artistes"

    def __str__(self):
        return self.nom


# ============================================
# 3. MODÈLE CATÉGORIE (Type_oeuvre dans ton PDF)
# ============================================

class Categorie(models.Model):
    """Catégories d'œuvres (Peinture, Sculpture, Photographie, etc.)"""

    nom_categorie = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "categorie"
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.nom_categorie


# ============================================
# 4. MODÈLE ŒUVRE
# ============================================

class Oeuvre(models.Model):
    """Œuvres d'art soumises par les artistes"""

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente de validation"
        VALIDE = "valide", "Validée"
        REFUSE = "refuse", "Refusée"

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="oeuvres/")
    technique = models.CharField(max_length=100, blank=True)
    annee_creation = models.IntegerField(null=True, blank=True)

    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=1)

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )

    # Relations
    artiste = models.ForeignKey(
        Artiste,
        on_delete=models.CASCADE,
        related_name="oeuvres",
    )
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="oeuvres",
    )

    # Dates
    date_soumission = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "oeuvre"
        verbose_name = "Œuvre"
        verbose_name_plural = "Œuvres"
        ordering = ["-date_soumission"]

    def __str__(self):
        return f"{self.titre} - {self.artiste}"

    @property
    def est_disponible(self):
        """Vérifie si l'œuvre est disponible à la vente"""
        return self.statut == self.Statut.VALIDE and self.stock > 0


# ============================================
# 5. MODÈLE LIEU
# ============================================

class Lieu(models.Model):
    """Lieux d'exposition (galeries, musées, etc.)"""

    nom_lieu = models.CharField(max_length=150)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)

    class Meta:
        db_table = "lieu"
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"

    def __str__(self):
        return f"{self.nom_lieu} - {self.ville}"


# ============================================
# 6. MODÈLE EXPOSITION
# ============================================

class Exposition(models.Model):
    """Expositions regroupant plusieurs œuvres"""

    nom_exposition = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_debut = models.DateField()
    date_fin = models.DateField()

    # Dans ton MCD: Exposition (1,1) -> Lieu donc pas null/blank
    # PROTECT empêche de supprimer un lieu si des expositions l'utilisent
    lieu = models.ForeignKey(
        Lieu,
        on_delete=models.PROTECT,
        related_name="expositions",
    )

    affiche = models.ImageField(upload_to="expositions/", blank=True, null=True)

    # M:N Exposition <-> Oeuvre
    oeuvres = models.ManyToManyField(
        Oeuvre,
        related_name="expositions",
        blank=True,
    )

    class Meta:
        db_table = "exposition"
        verbose_name = "Exposition"
        verbose_name_plural = "Expositions"
        ordering = ["-date_debut"]

    def __str__(self):
        return self.nom_exposition

    @property
    def est_en_cours(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.date_debut <= today <= self.date_fin


# ============================================
# 7. MODÈLE COMMANDE
# ============================================

class Commande(models.Model):
    """Commandes passées par les clients"""

    STATUTS = [
        ("en_cours", "En cours"),
        ("payee", "Payée"),
        ("annulee", "Annulée"),
        ("validee", "Validée"),
    ]

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="commandes",
    )

    # Pour la relation "Gérer (Admin – Commande)" de ton MCD
    # (un admin gère plusieurs commandes, une commande gérée par un admin)
    geree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes_gerees",
    )

    date_commande = models.DateTimeField(auto_now_add=True)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    statut = models.CharField(max_length=20, choices=STATUTS, default="en_cours")
    adresse_livraison = models.TextField(blank=True)

    class Meta:
        db_table = "commande"
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-date_commande"]

    def __str__(self):
        return f"Commande #{self.id} - {self.utilisateur.username}"


# ============================================
# 8. MODÈLE LIGNE COMMANDE (association Commande-Oeuvre)
# ============================================

class LigneCommande(models.Model):
    """Détails des œuvres dans une commande"""

    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name="lignes",
    )
    oeuvre = models.ForeignKey(
        Oeuvre,
        on_delete=models.CASCADE,
        related_name="lignes_commande",
    )

    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "ligne_commande"
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
        constraints = [
            models.UniqueConstraint(
                fields=["commande", "oeuvre"],
                name="unique_commande_oeuvre",
            )
        ]

    def __str__(self):
        return f"{self.oeuvre.titre} x{self.quantite}"

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire


# ============================================
# 9. MODÈLE PAIEMENT
# ============================================

class Paiement(models.Model):
    """Paiements associés aux commandes"""

    MODES = [
        ("carte", "Carte bancaire"),
        ("virement", "Virement"),
        ("especes", "Espèces"),
        ("paypal", "PayPal"),
    ]

    commande = models.OneToOneField(
        Commande,
        on_delete=models.CASCADE,
        related_name="paiement",
    )

    date_paiement = models.DateTimeField(auto_now_add=True)
    mode_paiement = models.CharField(max_length=20, choices=MODES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    reference_transaction = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "paiement"
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement {self.get_mode_paiement_display()} - {self.montant}"


# ============================================
# 10. MODÈLE PANIER
# ============================================

class Panier(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="paniers",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "panier"
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def __str__(self):
        return f"Panier de {self.client.username}"

    def total(self):
        return sum(item.sous_total for item in self.items.all())


class PanierItem(models.Model):
    panier = models.ForeignKey(
        Panier,
        on_delete=models.CASCADE,
        related_name="items",
    )
    oeuvre = models.ForeignKey(
        Oeuvre,
        on_delete=models.CASCADE,
        related_name="items_panier",
    )
    quantite = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "panier_item"
        verbose_name = "Article panier"
        verbose_name_plural = "Articles panier"
        constraints = [
            models.UniqueConstraint(
                fields=["panier", "oeuvre"],
                name="unique_panier_oeuvre",
            )
        ]

    @property
    def sous_total(self):
        return self.quantite * self.oeuvre.prix
