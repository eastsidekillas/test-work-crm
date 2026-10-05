from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from crm import views

router = DefaultRouter()
router.register("leads", views.LeadViewSet, basename="lead")
router.register("tags", views.TagViewSet, basename="tag")
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/csrf/", views.csrf),
    path("api/auth/login/", views.sign_in),
    path("api/auth/logout/", views.sign_out),
    path("api/auth/me/", views.me),
    path("api/health/", views.health),
    path("api/integrations/telegram/leads/", views.TelegramLeadView.as_view()),
    path("api/", include(router.urls)),
]
