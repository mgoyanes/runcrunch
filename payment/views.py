from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
import os
import psycopg2 as psy

from scripts import postgres as db

import stripe
stripe.api_key = os.environ['STRIPE_SECRET_KEY']
STRIPE_PUBLISHABLE_KEY = 'pk_live_z1sPeJjQcW88Z2yLfYtjhlr0000Zj1LTM5'

def support(request):
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'")

    return render(request, 'support.html', {'athlete': athlete})

def upgrade(request, success=1):
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'")

    return render(request, 'upgrade.html', {'athlete': athlete, 'success': bool(success)})

def subscribe(request):
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'")
    email = request.POST.get('email')
    user = request.POST['user']
    price = {
            '$1.99 /month': 'price_1GuLgxB1V92AxtqIa3AtO3ov',
            '$19.99 /year': 'price_1GuLgxB1V92AxtqIxlGRjaqg'
            }
    stripe_config = {'publicKey': STRIPE_PUBLISHABLE_KEY}

    if request.method == 'POST':
        print('Data:', request.POST)

    if athlete['customer'] != None:
        try:
            customer = stripe.Customer.retrieve(athlete['customer'])
            customer = stripe.Customer.modify(athlete['customer'],
                                              metadata={'email': email})
        except:
            customer = stripe.Customer.create(
                    name=user,
                    email=email,
                    source=request.POST['stripeToken']
                    )
    else:
        customer = stripe.Customer.create(
                    name=user,
                    email=email,
                    source=request.POST['stripeToken']
                    )

    try:
        subscription = stripe.Subscription.create(
            customer=customer,
            items=[{"price": price[request.POST['plan']]}],
            payment_behavior='error_if_incomplete'
            )
    except:
        return redirect(reverse('subscribed', args=('False', 'None')))

    return redirect(reverse('subscribed', args=(email, subscription['id'])))

def subscribed(request, email, subscription_id):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'", conn=conn)

    if email == 'False':
        return redirect(reverse('upgrade', args=(0)))

    db.UPDATE('auth_user', where=f"username = '{request.user}'", numCols=1, cols='email',
              vals=f"'{email}'", conn=conn)
    db.UPDATE('athletes', where=f"username = '{request.user}'", numCols=2,
              cols="tier, subscription", vals=f"'pro', '{subscription_id}'", conn=conn)

    conn.close()

    return render(request, 'subscribed.html', {'email': email, 'athlete': athlete})

def charge(request):
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'")
    amount =  int(request.POST['amount'])
    stripe_config = {'publicKey': STRIPE_PUBLISHABLE_KEY}

    if request.method == "POST":
        print('Data:', request.POST)

    if athlete['customer'] != None:
        try:
            customer = stripe.Customer.retrieve(athlete['customer'])
        except:
            customer = stripe.Customer.create(
                    name=request.POST['user'],
                    source=request.POST['stripeToken']
                    )
    else:
        customer = stripe.Customer.create(
                    name=request.POST['user'],
                    source=request.POST['stripeToken']
                    )

    try:
        charge = stripe.Charge.create(
            customer=customer,
            amount=amount*100,
            currency='usd',
            description='Donation'
            )
    except:
        return redirect(reverse('success', args=('False', 'None')))

    return redirect(reverse('success', args=(amount, customer['id'])))

def success(request, amount, customer_id):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'", conn=conn)

    if amount == 'False':
        conn.close()
        return render(request, 'success.html', {'amount': amount, 'athlete': athlete})

    db.UPDATE('athletes', where=f"username = '{request.user}'", numCols=1,
              cols='customer', vals=f"'{customer_id}'")
    conn.close()

    return render(request, 'success.html', {'amount': amount, 'athlete': athlete})

def cancel(request):
    import datetime

    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'", conn=conn)

    # Find out how long user has left
    try:
        subscription = stripe.Subscription.retrieve(athlete['subscription'])
        expiration = datetime.datetime.fromtimestamp(subscription['current_period_end']).strftime('%Y-%m-%d')
        cancelled = False
    except:
        expiration = athlete['subscription']
        cancelled = True

    return render(request, 'cancel.html', {'athlete': athlete, 'expiration': expiration,
                                           'cancelled': cancelled})

def cancelled(request, expiration):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    athlete = db.SELECT('athletes', where=f"username = '{request.user}'", conn=conn)

    stripe.Subscription.delete(athlete['subscription'])
    db.UPDATE('athletes', where=f"username = '{request.user}'", numCols=1,
              cols='subscription', vals=f"'{expiration}'")

    return render(request, 'cancelled.html', {'athlete': athlete})