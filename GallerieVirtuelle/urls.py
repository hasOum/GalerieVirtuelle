"""
URL configuration for GallerieVirtuelle project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView

urlpatterns = [
    # Galerie URLs must come BEFORE admin to avoid conflicts with /admin/dashboard/
    path('', include('galerie.urls')),
    # Custom auth URLs pointing to galerie/auth/ templates
    path('accounts/login/', LoginView.as_view(template_name='galerie/auth/login.html'), name='login'),
    path('accounts/logout/', LogoutView.as_view(template_name='galerie/auth/logout.html'), name='logout'),
    path('admin/', admin.site.urls),  # Django admin - must be last to avoid conflicts
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




