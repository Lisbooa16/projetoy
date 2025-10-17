from django.db import models
from django.utils.translation import gettext_lazy as _

class Bills(models.Model):
    class Status(models.TextChoices):
        PENDING = "1", _("Pending")
        PAY = "2", _("Pay")
        REFUSE = "3", _("Refuse")

    sub = models.ForeignKey("Subscription", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=4, choices=Status.choices, default=Status.PENDING)

    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"

    def __str__(self):
        return f"Bill #{self.id} - {self.get_status_display()}"
