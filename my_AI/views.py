from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import TemplateView
from google import genai
from google.genai import types
from .forms import RegisterForm
import os
from dotenv import load_dotenv
from .models import ChatMessage

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect('/')

    else:
        form = RegisterForm()

    return render(request, 'my_AI/register.html', {
        'form': form
    })


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')

        return render(request, "my_AI/login.html", {
            "error": "Invalid username or password"
        })

    return render(request, "my_AI/login.html")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")


@login_required
def gemini_view(request):
    error = None

    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()

        if prompt:
            try:
                history = ChatMessage.objects.filter(
                    user=request.user
                ).order_by("created_at", "id")

                contents = []

                for message in history:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(
                                    text=message.prompt
                                )
                            ]
                        )
                    )

                    contents.append(
                        types.Content(
                            role="model",
                            parts=[
                                types.Part.from_text(
                                    text=message.answer
                                )
                            ]
                        )
                    )

                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt)
                        ]
                    )
                )

                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=contents
                )

                answer = response.text

                if answer:
                    ChatMessage.objects.create(
                        user=request.user,
                        prompt=prompt,
                        answer=answer
                    )
                else:
                    error = "Gemini вернул пустой ответ."

            except Exception as e:
                error = f"Ошибка Gemini: {e}"

    messages = ChatMessage.objects.filter(
        user=request.user
    ).order_by("created_at", "id")

    return render(request, "my_AI/ask.html", {
        "messages": messages,
        "error": error,
    })
