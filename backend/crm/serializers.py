from rest_framework import serializers
from .models import Lead, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]

class LeadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, write_only=True, source="tags", required=False)
    class Meta:
        model = Lead
        fields = ["id", "name", "contact", "request", "source", "tags", "tag_ids", "created_at"]
        read_only_fields = ["id", "source", "created_at"]

class TagAssignmentSerializer(serializers.Serializer):
    tag_ids = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)

class TelegramLeadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    contact = serializers.CharField(max_length=255)
    request = serializers.CharField(max_length=5000)
    submission_id = serializers.UUIDField()
    telegram_user_id = serializers.IntegerField(min_value=1, max_value=9223372036854775807)
    telegram_chat_id = serializers.IntegerField(min_value=1, max_value=9223372036854775807)
