"""Circle invitations managers."""

# Django
from django.db import models

# Local
import random
from string import ascii_uppercase, digits


class InvitationManager(models.Manager):
    """Invitations manager.

    Used to handler code creation.
    """

    CODE_LENGTH = 10

    def create(self, **kwargs):
        """Handle code creation."""
        pool = ascii_uppercase + digits + '-'
        code = kwargs.get('code', ''.join(random.choices(pool, k=self.CODE_LENGTH)))
        while self.filter(code=code).exists():
            code = ''.join(random.choices(pool, k=self.CODE_LENGTH))
        kwargs['code'] = code
        return super(InvitationManager, self).create(**kwargs)