import secrets

from django.conf import settings
from django.db import models


class Circle(models.Model):
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='administered_circles')
    name = models.CharField(max_length=255)
    invite_code = models.CharField(max_length=8, unique=True, editable=False)
    contribution_amount = models.PositiveIntegerField()
    penalty_rate = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            while True:
                code = secrets.token_hex(4).upper()
                if not type(self).objects.filter(invite_code=code).exists():
                    self.invite_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Membership(models.Model):
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='circle_memberships')
    position = models.PositiveIntegerField()
    paid_out = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['circle', 'user'], name='unique_membership_circle_user'),
            models.UniqueConstraint(fields=['circle', 'position'], name='unique_membership_circle_position'),
        ]

    def __str__(self):
        return f'{self.circle} - {self.user}'


class Round(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending approval'
        CLOSED = 'CLOSED', 'Closed'

    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.PositiveIntegerField()
    recipient = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='recipient_rounds')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    deadline = models.DateTimeField()
    final_payout_amount = models.PositiveIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.circle} - Round {self.round_number}'


class Contribution(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='contributions')
    member = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='contributions')
    amount_owed = models.PositiveIntegerField()
    amount_paid = models.PositiveIntegerField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    penalty = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['round', 'member'], name='unique_contribution_round_member'),
        ]

    def __str__(self):
        return f'{self.round} - {self.member}'
