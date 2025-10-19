from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from .forms import ComposeForm, ReplyForm
from .models.mailbox import MessageThread, Message


@login_required
def inbox(request):
    threads = MessageThread.objects.filter(participants=request.user).order_by("-created_at")
    # anexa contagem de não lidas
    for t in threads:
        t.unread_count = t.unread_count_for(request.user)
    return render(request, "mail/inbox.html", {"threads": threads})


@login_required
def thread_detail(request, thread_id):
    thread = get_object_or_404(MessageThread, id=thread_id)
    if not thread.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden("Você não participa desta conversa.")

    messages = thread.messages.select_related("sender", "recipient").order_by("sent_at")

    # Marcar como lidas as recebidas pelo usuário nesta thread
    Message.objects.filter(
        thread=thread, recipient=request.user, is_read=False
    ).update(is_read=True)

    if request.method == "POST":
        form = ReplyForm(request.POST, user=request.user, thread=thread)
        if form.is_valid():
            form.save()
            return redirect("mailbox:thread_detail", thread_id=thread.id)
    else:
        form = ReplyForm(user=request.user, thread=thread)

    return render(
        request,
        "mail/thread_detail.html",
        {"thread": thread, "messages": messages, "form": form},
    )


@login_required
def compose(request):
    if request.method == "POST":
        form = ComposeForm(request.POST, user=request.user)
        if form.is_valid():
            msg = form.save()
            return redirect("mailbox:thread_detail", thread_id=msg.thread.id)
    else:
        form = ComposeForm(user=request.user)
    return render(request, "mail/compose.html", {"form": form})
