from django.contrib import admin
from django.urls import path, include
from .import views
urlpatterns = [
    # Auth routes
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Subscription
    path('subscription/checkout/', views.create_checkout_session, name='checkout'),
    path('subscription/manage/', views.manage_subscription, name='manage-subscription'), 
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views.subscription_cancel, name='subscription_cancel'),
    
    # Webhook
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),

]