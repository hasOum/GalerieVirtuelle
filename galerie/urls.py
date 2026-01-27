from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("galerie.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from . import views

app_name = "galerie"

urlpatterns = [
    path("", views.home, name="home"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("galerie:home")),
        name="logout",
    ),
    path("password/change/", auth_views.PasswordChangeView.as_view(template_name="registration/password_change.html"), name="password_change"),
    path("password/change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"), name="password_change_done"),

    # Dashboards
    path("artiste/dashboard/", views.artiste_dashboard, name="artiste_dashboard"),
    path("artiste/sales/", views.artiste_sales, name="artiste_sales"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/validation/", views.admin_validation_list, name="admin_validation_list"),
    path("client/dashboard/", views.client_dashboard, name="client_dashboard"),
    path("profil/", views.profile_edit, name="profile_edit"),

    # Oeuvres (visiteur)
    path("oeuvres/", views.oeuvres_list, name="oeuvres_list"),
    path("oeuvres/<int:pk>/", views.oeuvre_detail, name="oeuvre_detail"),

    # Expositions (visiteur)
    path("expositions/", views.expositions_list, name="expositions_list"),
    path("expositions/<int:pk>/", views.exposition_detail, name="exposition_detail"),

    # Artiste
    path("artiste/oeuvre/create/", views.oeuvre_create, name="oeuvre_create"),
    path("artiste/oeuvre/<int:pk>/update/", views.oeuvre_update, name="oeuvre_update"),

    # Admin actions
    path("admin/oeuvre/<int:pk>/valider/", views.oeuvre_valider, name="oeuvre_valider"),
    path("admin/oeuvre/<int:pk>/refuser/", views.oeuvre_refuser, name="oeuvre_refuser"),

    # Panier / commandes
    path("panier/", views.cart_detail, name="cart_detail"),
    path("panier/", views.cart_detail, name="cart_detail"),
    path("panier/add/<int:oeuvre_id>/", views.cart_add, name="cart_add"),
    path("panier/remove/<int:oeuvre_id>/", views.cart_remove, name="cart_remove"),
    path("panier/clear/", views.cart_clear, name="cart_clear"),
    path("checkout/", views.checkout, name="checkout"),
    path("commandes/", views.orders_list, name="orders_list"),
    path("commandes/<int:order_id>/payer/", views.order_pay, name="order_pay"),
    path("commandes/<int:order_id>/payment/success/", views.payment_success, name="payment_success"),
    path("commandes/<int:order_id>/annuler/", views.order_cancel, name="order_cancel"),

    # Notifications
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("notifications/<int:pk>/lire/", views.notification_mark_read, name="notification_mark_read"),
    path("notifications/<int:pk>/supprimer/", views.notification_delete, name="notification_delete"),
    path("admin/notifications/envoyer/", views.notification_send, name="notification_send"),
]
