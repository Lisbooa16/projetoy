from django import template

from mail.models.mailbox import Message

register = template.Library()


@register.simple_tag(takes_context=True)
def unread_count(context):
    user = context["user"]
    if not user.is_authenticated:
        return 0
    return Message.objects.filter(recipient=user, is_read=False).count()
