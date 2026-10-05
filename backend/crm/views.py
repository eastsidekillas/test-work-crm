import secrets
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import connection
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from .models import Lead, Tag
from .serializers import LeadSerializer, TagSerializer, TagAssignmentSerializer, TelegramLeadSerializer

@require_GET
@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})

class LoginThrottle(ScopedRateThrottle):
    scope = "login"
    def get_rate(self):
        return self.THROTTLE_RATES["login"]
    def allow_request(self, request, view):
        view.throttle_scope = "login"
        return super().allow_request(request, view)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=256, trim_whitespace=False)

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
@csrf_protect
def sign_in(request):
    data = LoginSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    user = authenticate(request, **data.validated_data)
    if user is None:
        return Response({"detail": "Неверный логин или пароль."}, status=400)
    login(request, user)
    return Response({"id": user.id, "username": user.username})

@api_view(["POST"])
def sign_out(request):
    logout(request)
    return Response({"detail": "Вы вышли из CRM."})

@api_view(["GET"])
def me(request):
    return Response({"id": request.user.id, "username": request.user.username})

@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})

class LeadViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = LeadSerializer
    def get_queryset(self):
        queryset = Lead.objects.prefetch_related("tags").all()
        tag_id = self.request.query_params.get("tag_id")
        if tag_id is not None:
            try:
                value = int(tag_id)
                if value < 1 or value > 9223372036854775807:
                    raise ValueError
            except (ValueError, TypeError):
                raise serializers.ValidationError({"tag_id": "Нужен положительный числовой ID тега."})
            queryset = queryset.filter(tags__id=value)
        return queryset
    def perform_create(self, serializer):
        serializer.save(source=Lead.Source.MANUAL)
    def partial_update(self, request, pk=None):
        lead = self.get_object()
        data = TagAssignmentSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        lead.tags.set(data.validated_data["tag_ids"])
        lead.save(update_fields=["updated_at"])
        return Response(LeadSerializer(lead).data)

class TagViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

class BotPermission(BasePermission):
    def has_permission(self, request, view):
        expected = settings.TELEGRAM_API_SECRET
        supplied = request.headers.get("X-Bot-Secret", "")
        return bool(expected) and secrets.compare_digest(supplied.encode(), expected.encode())

class TelegramLeadView(APIView):
    authentication_classes = []
    permission_classes = [BotPermission]
    def post(self, request):
        data = TelegramLeadSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        fields = data.validated_data.copy()
        submission_id = fields.pop("submission_id")
        # Unique db cost
        lead, created = Lead.objects.get_or_create(submission_id=submission_id, defaults={**fields, "source": Lead.Source.TELEGRAM})
        return Response(LeadSerializer(lead).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
