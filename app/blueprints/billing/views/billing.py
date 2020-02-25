from flask import (
  Blueprint,
  current_app,
  render_template,
  url_for,
  request,
  redirect,
  flash,
)

import traceback

from flask_login import login_required, current_user

from app.blueprints.api.api_functions import print_traceback
from config import settings
from app.blueprints.billing.forms import CreditCardForm, \
    UpdateSubscriptionForm, CancelSubscriptionForm
from app.blueprints.billing.models.subscription import Subscription
from app.blueprints.billing.models.invoice import Invoice
from app.blueprints.billing.decorators import subscription_required, \
    handle_stripe_exceptions
from app.extensions import cache, timeout, csrf

billing = Blueprint('billing', __name__, template_folder='../templates',
                    url_prefix='/subscription')


@billing.route('/pricing')
@csrf.exempt
# @cache.cached(timeout=timeout)
def pricing():
    if current_user.is_authenticated and current_user.customer:
        return redirect(url_for('billing.update'))

    form = UpdateSubscriptionForm()

    return render_template('page/pricing.html', form=form,
                           plans=settings.STRIPE_PLANS)


# @billing.route('/create', methods=['GET', 'POST'])
# @handle_stripe_exceptions
# @login_required
# @csrf.exempt
# def create():
#     try:
#         if current_user.customer:
#             flash('You already have an active subscription.', 'info')
#             return redirect(url_for('user.dashboard'))
#
#         plan = request.args.get('plan')
#         subscription_plan = Subscription.get_plan_by_id(plan)
#
#         # Guard against an invalid or missing plan.
#         if subscription_plan is None and request.method == 'GET':
#             flash('Sorry, that plan did not exist.', 'error')
#             return redirect(url_for('billing.pricing'))
#
#         stripe_key = current_app.config.get('STRIPE_KEY')
#         form = CreditCardForm(stripe_key=stripe_key, plan=plan)
#
#         if form.validate_on_submit():
#             subscription = Subscription()
#             created = subscription.create(user=current_user,
#                                         name=request.form.get('name'),
#                                         plan=request.form.get('plan'),
#                                         coupon=request.form.get('coupon_code'),
#                                         token=request.form.get('stripe_token'))
#
#             if created:
#                 from app.blueprints.billing.billing_functions import signup_limits
#                 signup_limits(current_user, subscription.plan)
#
#                 current_user.trial = False
#                 current_user.save()
#
#                 from app.blueprints.user.tasks import send_plan_signup_email
#                 send_plan_signup_email.delay(current_user.email, subscription.plan)
#
#                 flash('Your account has been upgraded!', 'success')
#             else:
#                 flash('You must enable JavaScript for this request.', 'warning')
#
#             return redirect(url_for('user.dashboard'))
#
#         return render_template('user/checkout.html')
#         # return render_template('billing/payment_method.html', form=form, plan=subscription_plan)
#     except Exception as e:
#         print_traceback(e)
#
#         flash('There was an error. We weren\'t able to subscribe you to a plan at this time.', 'error')
#         return redirect(url_for('user.dashboard'))


@billing.route('/create', methods=['GET', 'POST'])
@handle_stripe_exceptions
@login_required
@csrf.exempt
def create():
    try:
        if current_user.customer:
            # flash('You already have an active subscription.', 'info')
            return redirect(url_for('user.dashboard'))

        # plan = request.args.get('plan')
        # subscription_plan = Subscription.get_plan_by_id(plan)
        #
        # # Guard against an invalid or missing plan.
        # if subscription_plan is None and request.method == 'GET':
        #     flash('Sorry, that plan did not exist.', 'error')
        #     return redirect(url_for('billing.pricing'))

        stripe_key = current_app.config.get('STRIPE_KEY')
        form = CreditCardForm(stripe_key=stripe_key)

        # if form.validate_on_submit():
        #     subscription = Subscription()
        #
        #     created = subscription.create(user=current_user,
        #                                   name=request.form.get('name'),
        #                                   token=request.form.get('stripe_token'))
        #                                   # token=request.form.get('stripe_token'))
        #                                   # plan=request.form.get('plan'),
        #                                   #  coupon=request.form.get('coupon_code'),
        #
        #     if created:
        #         current_user.trial = False
        #         current_user.save()
        #
        #         # from app.blueprints.user.tasks import send_plan_signup_email
        #         # send_plan_signup_email.delay(current_user.email, subscription.plan)
        #
        #         flash('Your account has been upgraded!', 'success')
        #     else:
        #         flash('You must enable JavaScript for this request.', 'warning')
        #
        #     return redirect(url_for('user.dashboard'))

        return render_template('user/checkout.html')
        # return render_template('billing/payment_method.html', form=form, plan=subscription_plan)
        # return render_template('billing/payment_method.html', form=form)
    except Exception as e:
        print_traceback(e)

        flash('There was an error. We weren\'t able to subscribe you to a plan at this time.', 'error')
        return redirect(url_for('user.dashboard'))


@billing.route('/update', methods=['GET', 'POST'])
@handle_stripe_exceptions
@subscription_required
@login_required
@csrf.exempt
def update():
    try:
        current_plan = current_user.subscription.plan
        active_plan = Subscription.get_plan_by_id(current_plan)
        new_plan = Subscription.get_new_plan(request.form.keys())

        plan = Subscription.get_plan_by_id(new_plan)

        # Guard against an invalid, missing or identical plan.
        is_same_plan = new_plan == active_plan['id']
        if ((new_plan is not None and plan is None) or is_same_plan) and \
                request.method == 'POST':
            return redirect(url_for('billing.update'))

        form = UpdateSubscriptionForm(coupon_code=current_user.subscription.coupon)

        if form.validate_on_submit():
            subscription = Subscription()
            updated = subscription.update(user=current_user,
                                        coupon=request.form.get('coupon_code'),
                                        plan=plan.get('id'))

            if updated:
                from app.blueprints.billing.billing_functions import change_limits
                change_limits(current_user, plan, active_plan)

                from app.blueprints.user.tasks import send_plan_change_email
                send_plan_change_email.delay(current_user.email, plan)

                flash('Your plan has been updated. Changes will take effect immediately.', 'success')
                return redirect(url_for('user.dashboard'))

        return render_template('billing/pricing.html',
                            form=form,
                            plans=settings.STRIPE_PLANS,
                            active_plan=active_plan)
    except Exception as e:
        print_traceback(e)

        flash('There was an error. We weren\'t able to change your plan at this time.', 'error')
        return redirect(url_for('user.dashboard'))


@billing.route('/cancel', methods=['GET', 'POST'])
@handle_stripe_exceptions
@login_required
@csrf.exempt
def cancel():

    form = CancelSubscriptionForm()

    if form.validate_on_submit():

        # Cancel the user's Stripe account here
        # if current_user.customer:
        #     # subscription = Subscription()
        #     # canceled = subscription.cancel(user=current_user)
        # else:
        #     # If there is no subscription, then delete the user
        #     canceled = True
        canceled = True

        if canceled:
            # Get the user's email
            email = current_user.email

            # Delete the user.
            from app.blueprints.billing.tasks import delete_users
            ids = [current_user.id]

            # Delete the user
            delete_users.delay(ids)

            # Send a cancellation email.
            from app.blueprints.user.tasks import send_cancel_email
            send_cancel_email.delay(email)

            flash('Sorry to see you go! Your subscription has been canceled.',
                  'success')
            return redirect(url_for('user.logout'))

    return render_template('billing/cancel.html', form=form)


@billing.route('/update_payment_method', methods=['GET', 'POST'])
@handle_stripe_exceptions
@login_required
@csrf.exempt
def update_payment_method():
    if not current_user.credit_card:
        flash('You do not have a payment method on file.', 'error')
        return redirect(url_for('user.dashboard'))

    active_plan = Subscription.get_plan_by_id(
        current_user.subscription.plan)

    card = current_user.credit_card
    stripe_key = current_app.config.get('STRIPE_KEY')
    form = CreditCardForm(stripe_key=stripe_key,
                          plan=active_plan,
                          name=current_user.name)

    if form.validate_on_submit():
        subscription = Subscription()
        updated = subscription.update_payment_method(user=current_user,
                                                     credit_card=card,
                                                     name=request.form.get(
                                                         'name'),
                                                     token=request.form.get(
                                                         'stripe_token'))

        if updated:
            flash('Your payment method has been updated.', 'success')
        else:
            flash('You must enable JavaScript for this request.', 'warning')

        return redirect(url_for('user.dashboard'))

    return render_template('billing/payment_method.html', form=form,
                           plan=active_plan, card_last4=str(card.last4))


@billing.route('/billing_details')
@handle_stripe_exceptions
@login_required
@csrf.exempt
def billing_details():
    invoices = Invoice.billing_history(current_user)

    if current_user.customer:
        upcoming = Invoice.upcoming(current_user.payment_id)
        coupon = None
        # coupon = Coupon.query \
        #     .filter(Coupon.code == current_user.subscription.coupon).first()
    else:
        upcoming = None
        coupon = None

    return render_template('billing/billing_details.html',
                           invoices=invoices, upcoming=upcoming, coupon=coupon)
