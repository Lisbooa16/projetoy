"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.conf.urls import handler403
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path


def custom_permission_denied_view(request, exception=None):
    """
    Retorna uma página 403 estilizada dentro do tema do admin.
    """
    return render(request, "admin/403.html", status=403)


handler403 = custom_permission_denied_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("custom_auth.urls")),
    path("api/", include("subscription.urls")),
    path("messages/", include("mail.urls", namespace="mailbox")),
]
