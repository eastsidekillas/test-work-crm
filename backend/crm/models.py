from django.db import models

class Tag(models.Model):
    name = models.CharField("Название", max_length=50, unique=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name

class Lead(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Вручную"
        TELEGRAM = "telegram_bot", "Telegram"

    name = models.CharField("Имя", max_length=150)
    contact = models.CharField("Контакт", max_length=255)
    request = models.TextField("Запрос", max_length=5000)
    source = models.CharField("Источник", max_length=20, choices=Source.choices, default=Source.MANUAL)
    tags = models.ManyToManyField(Tag, blank=True, related_name="leads")
    submission_id = models.UUIDField(null=True, blank=True, unique=True)
    telegram_user_id = models.BigIntegerField(null=True, blank=True)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.name
