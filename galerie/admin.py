from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilisateur, Artiste, Categorie, Oeuvre, 
    Lieu, Exposition, Commande, LigneCommande, Paiement,
    Panier, PanierItem
)

# ============================================
# 1. ADMIN UTILISATEUR
# ============================================

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_active']
    list_filter = ['role', 'is_active', 'date_inscription']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('telephone', 'role')
        }),
    )


# ============================================
# 2. ADMIN ARTISTE
# ============================================

@admin.register(Artiste)
class ArtisteAdmin(admin.ModelAdmin):
    list_display = ['user', 'nationalite', 'get_nombre_oeuvres']
    search_fields = ['utilisateur__username', 'utilisateur__first_name', 'utilisateur__last_name']
    list_filter = ["nationalite",]
    
    def get_nombre_oeuvres(self, obj):
        return obj.oeuvres.count()
    get_nombre_oeuvres.short_description = 'Nombre d\'œuvres'


    




# ============================================
# 3. ADMIN CATÉGORIE
# ============================================

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom_categorie', 'get_nombre_oeuvres']
    search_fields = ['nom_categorie']
    
    def get_nombre_oeuvres(self, obj):
        return obj.oeuvre_set.count()
    get_nombre_oeuvres.short_description = 'Nombre d\'œuvres'


# ============================================
# 4. ADMIN ŒUVRE
# ============================================

@admin.register(Oeuvre)
class OeuvreAdmin(admin.ModelAdmin):
    list_display = ['titre', 'artiste', 'categorie', 'prix', 'statut', 'stock', 'date_soumission']
    list_filter = ['statut', 'categorie', 'date_soumission']
    search_fields = ['titre', 'artiste__utilisateur__username']
    list_editable = ['statut', 'prix', 'stock']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'description', 'image', 'artiste', 'categorie')
        }),
        ('Détails techniques', {
            'fields': ('technique', 'annee_creation', 'prix', 'stock')
        }),
        ('Validation', {
            'fields': ('statut', 'date_validation')
        }),
    )

    


# ============================================
# 5. ADMIN EXPOSITION
# ============================================

@admin.register(Exposition)
class ExpositionAdmin(admin.ModelAdmin):
    list_display = ['nom_exposition', 'lieu', 'date_debut', 'date_fin', 'est_en_cours']
    list_filter = ['date_debut', 'lieu']
    search_fields = ['nom_exposition']
    filter_horizontal = ['oeuvres']


# ============================================
# 6. ADMIN COMMANDE
# ============================================

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 1
    readonly_fields = ['sous_total']

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'utilisateur', 'date_commande', 'montant_total', 'statut']
    list_filter = ['statut', 'date_commande']
    search_fields = ['utilisateur__username', 'id']
    inlines = [LigneCommandeInline]


# ============================================
# 7. ADMIN PAIEMENT
# ============================================

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['commande', 'mode_paiement', 'montant', 'date_paiement']
    list_filter = ['mode_paiement', 'date_paiement']


# ============================================
# 8. ADMIN LIEU
# ============================================

@admin.register(Lieu)
class LieuAdmin(admin.ModelAdmin):
    list_display = ['nom_lieu', 'ville', 'pays']
    search_fields = ['nom_lieu', 'ville', 'pays']

# ============================================
# 9. ADMIN PANIER
# ============================================

class PanierItemInline(admin.TabularInline):
    model = PanierItem
    extra = 1


@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'updated_at', 'nombre_articles', 'total_panier']
    list_filter = ['updated_at']
    search_fields = ['client__username']
    inlines = [PanierItemInline]
    readonly_fields = ['updated_at']
    
    def nombre_articles(self, obj):
        return obj.items.count()
    nombre_articles.short_description = 'Nombre d\'articles'
    
    def total_panier(self, obj):
        return f"{obj.total():.2f}€"
    total_panier.short_description = 'Total'


@admin.register(PanierItem)
class PanierItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'panier', 'oeuvre', 'quantite', 'get_sous_total']
    list_filter = ['panier']
    search_fields = ['oeuvre__titre', 'panier__client__username']
    
    def get_sous_total(self, obj):
        return f"{obj.sous_total:.2f}€"
    get_sous_total.short_description = 'Sous-total'