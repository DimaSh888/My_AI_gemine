from django.urls import path
from my_AI import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.gemini_view, name="ask"),
    path("chat/new/", views.new_chat, name="new_chat"),
    path("chat/<int:chat_id>/", views.gemini_view, name="chat_detail"),
    path("chat/<int:chat_id>/delete/", views.delete_chat, name="delete_chat"),
    path("message/<int:pk>/delete/", views.ask_delete, name="ask_delete"),
]
