# mail/utils.py
from typing import Iterable, List, Optional, Union

from django.contrib.auth import get_user_model

from mail.models.mailbox import Message, MessageThread

User = get_user_model()


def send_internal_message(
    subject: str, body: str, sender: Optional[User], recipients: List[User]
):
    """
    Cria/reutiliza uma thread e envia mensagem interna para recipients.
    """
    if not recipients:
        return None

    thread, _ = MessageThread.objects.get_or_create(subject=subject)
    participants = list({*(recipients or []), *([sender] if sender else [])})
    thread.participants.set([p for p in participants if p is not None])

    msgs = []
    for u in recipients:
        msgs.append(
            Message.objects.create(
                thread=thread,
                sender=sender,  # pode ser None (mensagem do sistema)
                recipient=u,
                body=body,
            )
        )
    return msgs


def notificar_usuario(
    destinatarios: Union[User, Iterable[User]],
    subject: str,
    message: str,
    *,
    sender: Optional[User] = None,
):
    """
    Wrapper que aceita 1 usuário ou lista/QuerySet de usuários e manda mensagem interna.
    """
    if destinatarios is None:
        return
    if isinstance(destinatarios, User):
        recipients = [destinatarios]
    else:
        recipients = list(destinatarios)
    if not recipients:
        return
    return send_internal_message(
        subject=subject, body=message, sender=sender, recipients=recipients
    )
