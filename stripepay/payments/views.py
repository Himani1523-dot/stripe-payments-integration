from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from django.conf import settings
from django.http import JsonResponse

import stripe
from .models import User, Subscription
from .forms import RegisterForm


stripe.api_key = settings.STRIPE_SECRET_KEY

# ========== REGISTER VIEW ====================================================================================================
"""def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
    
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors) 
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    
    return render(request, 'payments/register.html', {'form': form})"""


#========== REGISTER VIEW ====================================================================================================
"""immediately create stripe customer when the user registers"""
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            #Create Stripe Customer immediately 
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    "app_user_id": user.id
                }
            )
            user.stripe_customer_id = customer.id
            user.save()
            print(f"Stripe customer created for {user.email}: {customer.id}")

            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('dashboard')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = RegisterForm()

    return render(request, 'payments/register.html', {'form': form})


# ========== LOGIN VIEW =======================================================================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'payments/login.html')


# ========== LOGOUT VIEW =======================================================================================================
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('login')


# ========== DASHBOARD VIEW ====================================================================================================
@login_required
def dashboard_view(request):
    user = request.user
    subscription = getattr(user, 'subscription', None)
    
    context = {
        'user': user,
        'subscription': subscription,
        'has_active_subscription': subscription and subscription.status == Subscription.Status.ACTIVE
    }
    
    return render(request, 'payments/dashboard.html', context)

#===============CHECKOUT SESSION=================================================================================================
"""@login_required
@require_http_methods(["POST"])
def create_checkout_session(request):
    print("USING PRICE:", settings.STRIPE_PRICE_ID)
    
    user = request.user
    
    subscription = getattr(user, "subscription", None)
    if subscription and subscription.status == Subscription.Status.ACTIVE:
        return JsonResponse({"error": "You already have an active subscription"},status=400)

    try:                                                                                   #Stripe stores this metadata unchanged and sends it back in webhook events.
        session_data = {
            "mode": "subscription",
            # "payment_method_types": ["card"],
            "line_items": [{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            "metadata": {
                "user_id": str(user.id),
                "email": user.email, 
            },
             "success_url": "https://kristofer-ginglymoid-extemporally.ngrok-free.dev/payments/subscription/success/",
             "cancel_url": "https://kristofer-ginglymoid-extemporally.ngrok-free.dev/payments/subscription/cancel/",

         }
    
        if user.stripe_customer_id:                                                            #if user already have a stripe customer ID its fine otherwise Stripe wil create a new ID 
            session_data["customer"] = user.stripe_customer_id
            print("USING PRICE:", settings.STRIPE_PRICE_ID)

        else:
            session_data["customer_email"] = user.email                                       # First-time user → Stripe will create customer

        
        session = stripe.checkout.Session.create(**session_data)                               #using kwargs to pass the dict of the. session data so didnt have to write all the keys again 

        return redirect(session.url)
        # return JsonResponse({"checkout_url": session.url})

    
    except stripe.error.StripeError as e:
        print("STRIPE ERROR:", e)
        return JsonResponse({"error": str(e)}, status=400)"""
#===============CHECKOUT SESSION=================================================================================================
@login_required
@require_http_methods(["POST"])
def create_checkout_session(request):
    user = request.user

    if not user.stripe_customer_id:
        return JsonResponse({"error": "Stripe customer missing"},status=400)

    subscription = getattr(user, "subscription", None)
    if subscription and subscription.status == Subscription.Status.ACTIVE:
        return JsonResponse(
            {"error": "You already have an active subscription"},status=400)

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=user.stripe_customer_id,                                 #Always exists
            line_items=[{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url="https://kristofer-ginglymoid-extemporally.ngrok-free.dev/payments/subscription/success/",
            cancel_url="https://kristofer-ginglymoid-extemporally.ngrok-free.dev/payments/subscription/cancel/",
            metadata={
                "user_id": str(user.id),                                     #sending user ID in metadata to indentify  user in webhook 
            }
        )

        return redirect(session.url)

    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)


#====================MANAGE / UPGRADE SUBSCRIPTION (STRIPE CUSTOMER PORTAL)================================================================================================ 
@login_required 
@require_http_methods(["POST"])
def manage_subscription(request):

    user = request.user

    if not user.stripe_customer_id:
        return JsonResponse({"error": "No Stripe customer found"},status = 400)
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url= "https://kristofer-ginglymoid-extemporally.ngrok-free.dev/payments/dashboard/",
            )
        return redirect(portal_session.url)
    
    except stripe.error.StripeError as e:
        print("STRIPE ERROR:", e)
        return JsonResponse({"error": str(e)},status=400)

#====================STRIPE WEBHOOK================================================================================================
"""@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body                                                               #raw JSON sent by Stripe as We need raw body to verify Stripe signature
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")                               #Special header added by Stripe Used to verify the request really came from Stripe    

    try:
        event = stripe.Webhook.construct_event(                                          #event(dict) = Verifies the signature ,Verifies the payload, Converts JSON → Python dictionary     
            payload, 
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({"error": "Invalid webhook"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]                                                  #here event["data"]["object"]  means send me the checkout session object from event data and                                 

        user_id = session["metadata"].get("user_id")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        try:
            user = User.objects.get(id=user_id)                                            #find the user in db who paid for subscription 

            if not user.stripe_customer_id:
                user.stripe_customer_id = customer_id
                user.save()
                print(f"✅ Customer ID generated for {user.email}: {customer_id}")
    

            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "stripe_subscription_id": subscription_id,                            #If subscription exists → update it
                    "status": Subscription.Status.ACTIVE                                  #If it doesn’t → create it
                }
            )
            print(f"✅ Subscription created for {user.email}: {subscription_id}")
        except User.DoesNotExist:
            pass
    return JsonResponse({"status": "success"})
    # return redirect('dashboard')"""

#====================STRIPE WEBHOOK================================================================================================
@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body                                                             #raw JSON sent by Stripe as We need raw body to verify Stripe signature
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")                             #Special header added by Stripe Used to verify the request really came from Stripe    


    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({"error": "Invalid webhook"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        user_id = session["metadata"]["user_id"]
        subscription_id = session["subscription"]                                    #subscription id created by stripe during checkout session 

        try:
            user = User.objects.get(id=user_id)                                        

            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "stripe_subscription_id": subscription_id,
                    "status": Subscription.Status.ACTIVE,
                }
            )

            print(f"✅ Subscription activated for {user.email}: {subscription_id}")

        except User.DoesNotExist:
            print(" User not found for webhook event")

    return JsonResponse({"status": "success"})


#====================NEW STRIPE WEBHOOK HANDLING 5 EVENTS  ================================================================================================
"""@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body                                                               #raw JSON sent by Stripe as We need raw body to verify Stripe signature
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")                               #Special header added by Stripe Used to verify the request really came from Stripe    

    try:
        event = stripe.Webhook.construct_event(                                          #event(dict) = Verifies the signature ,Verifies the payload, Converts JSON → Python dictionary     
            payload, 
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({"error": "Invalid webhook"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]                                                  #here event["data"]["object"]  means send me the checkout session object from event data and                                 

        user_id = session["metadata"].get("user_id")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        try:
            user = User.objects.get(id=user_id)                                            #find the user in db who paif for subscription 

            if not user.stripe_customer_id:
                user.stripe_customer_id = customer_id
                user.save()
                print(f"✅ Customer ID generated for {user.email}: {customer_id}")


            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "stripe_subscription_id": subscription_id,                            #If subscription exists → update it
                    "status": Subscription.Status.ACTIVE                                  #If it doesn’t → create it
                }
            )
            print(f"Subscription created for {user.email}: {subscription_id}")
        except User.DoesNotExist:
            pass
    
    
    elif event["type"] == "customer.subscription.updated":
        subscription_data = event["data"]["object"]
        
        Subscription.objects.filter(
            stripe_subscription_id=subscription_data["id"]
        ).update(status=subscription_data["status"])
        
        print(f"Subscription updated: {subscription_data['id']} → {subscription_data['status']}")

    elif event["type"] == "customer.subscription.deleted":
        subscription_data = event["data"]["object"]

        Subscription.objects.filter(
            stripe_subscription_id=subscription_data["id"]
        ).update(status=Subscription.Status.CANCELED)
        
        print(f" Subscription canceled: {subscription_data['id']}")
    
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        print(f" Payment succeeded: {invoice['id']}")
    
   
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        print(f" Payment failed: {invoice['id']}")

    return JsonResponse({"status": "success"})"""

  
#=================REDIRECTING PAGES ==========================================================================================================
def subscription_success(request):
    messages.success(request, "✅Payment successful! Your subscription is active.")
    return redirect('dashboard')

def subscription_cancel(request):
    messages.error(request, "❌Payment cancelled. Your subscription was not activated.")
    return redirect('dashboard')

""" def subscription_success(request):
#     return render(request, 'subscription/success.html')


# @login_required
# def subscription_cancel(request):
#     return render(request, 'subscription/cancel.html')"""


      




    


