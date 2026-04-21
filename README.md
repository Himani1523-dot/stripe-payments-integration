# Stripe Payments Integration (Django)

A production-style Django project demonstrating **Stripe Checkout–based subscription payments**, 
customer management, and secure webhook handling.

This project covers the **complete subscription lifecycle**: user registration, Stripe customer creation, checkout, subscription activation, and customer self-service via the Stripe Billing Portal.

---

##  Features

- User registration, login, and logout
- Automatic Stripe Customer creation on signup
- Subscription payments using Stripe Checkout
- Secure Stripe webhook handling
- Subscription status tracking in database
- Stripe Customer Billing Portal integration
- Protected dashboard with subscription status
- Django messages for user feedback

---

## 🛠 Tech Stack

- **Backend:** Django, Python
- **Payments:** Stripe API
- **Auth:** Django Authentication
- **Database:** SQLite (default, easily replaceable)
- **Webhooks:** Stripe Webhook Verification

---

## 🔐 Stripe Flow Overview

1. User registers → Stripe customer created immediately
2. User starts subscription → Stripe Checkout Session
3. Payment completed → Stripe sends webhook
4. Webhook activates subscription in database
5. User can manage subscription via Stripe Billing Portal

---

## 📍 Application Routes

### Authentication
- `/register/` – User registration
- `/login/` – User login
- `/logout/` – User logout

### Dashboard
- `/dashboard/` – User dashboard with subscription status

### Subscription
- `/subscription/checkout/` – Create Stripe Checkout session
- `/subscription/manage/` – Stripe customer portal
- `/subscription/success/` – Payment success redirect
- `/subscription/cancel/` – Payment cancel redirect

### Webhooks
- `/stripe/webhook/` – Stripe webhook endpoint

---

## ⚙️ Setup Instructions

###  Clone the Repository
```bash
git clone https://github.com/yourusername/stripe-payments-integration.git
cd stripe-payments-integration
