from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager

# When using email as the login field with AbstractUser, Django requires a custom UserManager, otherwise createsuperuser fails.

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)     #can access admin panel
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    username = None         

    name = models.CharField(max_length=150, blank = True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    stripe_customer_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS =  [ ]     #Required for createsuperuser when email is used as USERNAME_FIELD

    objects = UserManager()

    def __str__(self):
        return self.email
    

class Subscription(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        CANCELED = "canceled", "Canceled"              #stripe uses single L in canceled not double L ,it can throw silent error if method name doesn"t match 
        PAST_DUE = "past_due", "Past Due"              #  Payment failed, retrying
        UNPAID = "unpaid", "Unpaid"                                                                                                                    #  Payment failed multiple times
        TRIALING = "trialing", "Trialing"              #  Free trial period
        INCOMPLETE = "incomplete", "Incomplete"        #  Initial payment failed
        INCOMPLETE_EXPIRED = "incomplete_expired", "Incomplete Expired"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    stripe_subscription_id = models.CharField(max_length=255, unique= True,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 
    status = models.CharField(max_length=20,choices=Status.choices,default=Status.INACTIVE)
    

    def __str__(self):
        return f"Subscription for {self.user.email} - status: {self.status}"

