from django.urls import path 
from payment_subscribe.views import (PaypalOrderStatusView,CreatePaypalOrderView,
    paypal_payment_success,paypal_payment_cancel,paypal_webhook,DoctorSubscriptionStatusView,
    CreateDoctorSubscriptionView,paypal_webhook_subscription,subscription_success,subscription_cancel
)

urlpatterns= [
    
    path('paypal/status/<str:order_id>/', PaypalOrderStatusView.as_view(), name='paypal-status'),
    
    path('paypal/create/', CreatePaypalOrderView.as_view(), name='paypal-create'),

    path('payment/success/', paypal_payment_success, name='paypal-payment-success'),

    path('payment/return/', paypal_payment_success, name='paypal-return'),

    path('payment/cancel/', paypal_payment_cancel, name='paypal-payment-cancel'),

    path('paypal/webhook/', paypal_webhook, name='paypal-webhook'),

    path('subscriber/', DoctorSubscriptionStatusView.as_view(), name='doctor-subscriber'),

     path('subscription/create/', CreateDoctorSubscriptionView.as_view(), name='create-subscription'),

    path('subscription/webhook/', paypal_webhook_subscription, name='paypal-subscription-webhook'),


    path('subscription/success/', subscription_success, name='subscription-success'),
    
    path('subscription/cancel/', subscription_cancel, name='subscription-cancel'),
]