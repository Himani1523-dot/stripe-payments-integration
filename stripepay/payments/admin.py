from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'stripe_customer_id', 'is_active', 'created_at']
    search_fields = ['email', 'name', 'stripe_customer_id']
    list_filter = ['is_active', 'is_staff', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Login Info', {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('name',)
        }),
        ('Stripe Info', {
            'fields': ('stripe_customer_id',),
            'classes': ('collapse',)  
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    # Fields shown when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    
    list_display = ['user_email', 'status', 'stripe_subscription_id', 'created_at']
    search_fields = ['user__email', 'stripe_subscription_id']
    list_filter = ['status', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Subscription Details', {
            'fields': ('status', 'stripe_subscription_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    # Custom method to display user email in list
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'