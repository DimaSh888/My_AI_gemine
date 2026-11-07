from dotenv import load_dotenv
import os

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from google.genai import types
from google import genai

from .forms import RegisterForm
from .models import Chat, ChatMessage

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("ask")
    else:
        form = RegisterForm()
    return render(request, "my_AI/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("ask")
        return render(request, "my_AI/login.html", {
            "error": "Неверный логин или пароль"
        })
    return render(request, "my_AI/login.html")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")


@login_required
def gemini_view(request, chat_id=None):
    chats = Chat.objects.filter(user=request.user)
    if chat_id is None:
        chat = chats.first()
        if chat is None:
            chat = Chat.objects.create(user=request.user, title="Новый чат")
        return redirect("chat_detail", chat_id=chat.id)

    chat = get_object_or_404(chats, id=chat_id)
    error = None

    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        if prompt:
            try:
                history = ChatMessage.objects.filter(
                    chat=chat, user=request.user
                ).order_by("created_at", "id")

                contents = []
                for message in history:
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=message.prompt)]
                    ))
                    contents.append(types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=message.answer)]
                    ))

                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                ))

                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=contents
                )
                answer = response.text

                if answer:
                    with transaction.atomic():
                        ChatMessage.objects.create(
                            chat=chat,
                            user=request.user,
                            prompt=prompt,
                            answer=answer
                        )
                        if chat.title == "Новый чат":
                            chat.title = prompt[:45].strip()
                            if len(prompt) > 45:
                                chat.title += "…"
                        chat.updated_at = timezone.now()
                        chat.save(update_fields=["title", "updated_at"])
                    return redirect("chat_detail", chat_id=chat.id)
                error = "Gemini вернул пустой ответ."
            except Exception as e:
                error = f"Ошибка Gemini: {e}"

    messages = ChatMessage.objects.filter(
        chat=chat, user=request.user
    ).order_by("created_at", "id")

    return render(request, "my_AI/ask.html", {
        "chats": chats,
        "active_chat": chat,
        "messages": messages,
        "error": error,
    })


@login_required
def new_chat(request):
    if request.method == "POST":
        chat = Chat.objects.create(user=request.user, title="Новый чат")
        return redirect("chat_detail", chat_id=chat.id)
    return redirect("ask")


@login_required
def delete_chat(request, chat_id):
    if request.method == "POST":
        chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        chat.delete()
    return redirect("ask")


@login_required
def ask_delete(request, pk):
    if request.method == "POST":
        message = get_object_or_404(
            ChatMessage, id=pk, user=request.user
        )
        chat_id = message.chat_id
        message.delete()
        return redirect("chat_detail", chat_id=chat_id)
    return redirect("ask")
