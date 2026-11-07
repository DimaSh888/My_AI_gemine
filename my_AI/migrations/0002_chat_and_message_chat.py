import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def move_old_messages_into_chats(apps, schema_editor):
    Chat = apps.get_model("my_AI", "Chat")
    ChatMessage = apps.get_model("my_AI", "ChatMessage")
    db = schema_editor.connection.alias

    user_ids = (
        ChatMessage.objects.using(db)
        .values_list("user_id", flat=True)
        .distinct()
    )
    for user_id in user_ids:
        chat = Chat.objects.using(db).create(
            user_id=user_id,
            title="Старая переписка"
        )
        ChatMessage.objects.using(db).filter(
            user_id=user_id, chat__isnull=True
        ).update(chat_id=chat.id)


class Migration(migrations.Migration):
    dependencies = [
        ("my_AI", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Chat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Новый чат", max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chats", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at", "-id"]},
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="chat",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="messages", to="my_AI.chat"
            ),
        ),
        migrations.RunPython(move_old_messages_into_chats, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="chatmessage",
            name="chat",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages", to="my_AI.chat"
            ),
        ),
    ]
