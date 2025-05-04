import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        email_h = hashlib.sha256(email.encode()).hexdigest()
        name_h = hashlib.sha256(name.encode()).hexdigest()
        user = self.model(email_hash=email_h, name_hash=name_h)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        return self.create_user(email, name, password)


class CustomUser(AbstractBaseUser):
    email_hash = models.CharField(max_length=64, unique=True)
    name_hash = models.CharField(max_length=64, unique=True)

    USERNAME_FIELD = 'name_hash'
    REQUIRED_FIELDS = ['email_hash']

    objects = CustomUserManager()

    def __str__(self):
        return self.email_hash
