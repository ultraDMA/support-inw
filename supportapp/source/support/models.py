from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class TicketInstance(models.Model):
    owner = models.ForeignKey(User, related_name='tickets', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    from_user = models.CharField(max_length=255)
    message = models.TextField()
    STATUS_CHOICES = (
        ('c', 'completed'),
        ('u', 'uncompleted'),
        ('f', 'frozen')
    )
    status = models.CharField(choices=STATUS_CHOICES, default='u', max_length=1)
    changed_status = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)

    objects = models.Manager()

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.id}, {self.message[:25]}, {self.status}'

    def get_absolute_url(self):
        return reverse('ticket-detail', kwargs={'pk': self.pk})


class TicketComment(models.Model):
    owner = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    from_user = models.CharField(max_length=255)
    to_ticket = models.ForeignKey(TicketInstance, related_name='answers', on_delete=models.CASCADE)
    message = models.TextField()
    answered_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'id: {self.id}, message: {str(self.message)}'

    def get_absolute_url(self):
        return reverse(viewname='comment-detail', kwargs={'pk': self.pk})
