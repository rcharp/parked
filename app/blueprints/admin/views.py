from flask import (
    Blueprint,
    redirect,
    request,
    flash,
    url_for,
    render_template)
from flask_login import login_required, current_user
from sqlalchemy import text
from app.extensions import csrf
from app.blueprints.admin.models import Dashboard
from app.blueprints.api.api_functions import print_traceback
from app.blueprints.user.decorators import role_required
from app.blueprints.billing.models.subscription import Subscription
from app.blueprints.billing.models.invoice import Invoice
from app.blueprints.user.models import User
from app.blueprints.api.models.backorder import Backorder
from app.blueprints.admin.forms import (
    SearchForm,
    BulkDeleteForm,
    UserForm,
    UserCancelSubscriptionForm,
)

admin = Blueprint('admin', __name__,
                  template_folder='templates', url_prefix='/admin')


@admin.before_request
@login_required
@role_required('admin')
def before_request():
    """ Protect all of the admin endpoints. """
    pass


# Dashboard -------------------------------------------------------------------
@admin.route('')
def dashboard():
    group_and_count_backorders = Dashboard.group_and_count_backorders()
    # group_and_count_coupons = Dashboard.group_and_count_coupons()
    group_and_count_users = Dashboard.group_and_count_users()

    return render_template('admin/page/dashboard.html',
                           group_and_count_backorders=group_and_count_backorders,
                           # group_and_count_coupons=group_and_count_coupons,
                           group_and_count_users=group_and_count_users)


@admin.route('/update_domains', methods=['GET','POST'])
@login_required
@csrf.exempt
def update_domains():
    if request.method == 'POST':
        try:
            from app.blueprints.api.domain.domain import generate_drops
            results = generate_drops()

            if results is not None:
                flash("Drops generated succesfully.", 'success')
            else:
                flash("Drops not generated succesfully.", 'error')

            return redirect(url_for('user.dashboard'))
        except Exception as e:
            print_traceback(e)
            flash("There was an error.", 'error')
            flash(e, 'error')
            return redirect(url_for('user.dashboard'))
    else:
        flash("Test wasn't run.", 'error')
        return redirect(url_for('user.dashboard'))


# Users -----------------------------------------------------------------------
@admin.route('/users', defaults={'page': 1})
@admin.route('/users/page/<int:page>')
def users(page):
    search_form = SearchForm()
    bulk_form = BulkDeleteForm()

    sort_by = User.sort_by(request.args.get('sort', 'created_on'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_users = User.query \
        .filter(User.search(request.args.get('q', text('')))) \
        .order_by(User.role.asc(), User.email, text(order_values)) \
        .paginate(page, 50, True)

    return render_template('admin/user/index.html',
                           form=search_form, bulk_form=bulk_form,
                           users=paginated_users)


# Backorders -----------------------------------------------------------------------
@admin.route('/backorders', defaults={'page': 1})
@admin.route('/backorders/page/<int:page>')
def backorders(page):
    search_form = SearchForm()
    bulk_form = BulkDeleteForm()

    sort_by = Backorder.sort_by(request.args.get('sort', 'created_on'),
                           request.args.get('direction', 'desc'))
    order_values = '{0} {1}'.format(sort_by[0], sort_by[1])

    paginated_backorders = Backorder.query \
        .order_by(Backorder.created_on.asc(), Backorder.domain_name, text(order_values)) \
        .paginate(page, 50, True)

    return render_template('admin/backorder/index.html',
                           form=search_form, bulk_form=bulk_form,
                           backorders=paginated_backorders)


@admin.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def users_edit(id):
    user = User.query.get(id)
    form = UserForm(obj=user)

    invoices = Invoice.billing_history(current_user)
    if current_user.customer:
        upcoming = Invoice.upcoming(current_user.payment_id)
        # coupon = Coupon.query \
        #     .filter(Coupon.code == current_user.subscription.coupon).first()
        coupon = None
    else:
        upcoming = None
        coupon = None

    if form.validate_on_submit():
        if User.is_last_admin(user,
                              request.form.get('role'),
                              request.form.get('active')):
            flash('You are the last admin, you cannot do that.', 'error')
            return redirect(url_for('admin.users'))

        form.populate_obj(user)

        if not user.username:
            user.username = None

        user.save()

        flash('User has been saved successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user/edit.html', form=form, user=user,
                           invoices=invoices, upcoming=upcoming, coupon=coupon)


@admin.route('/users/bulk_delete', methods=['POST'])
def users_bulk_delete():
    form = BulkDeleteForm()

    if form.validate_on_submit():
        ids = User.get_bulk_action_ids(request.form.get('scope'),
                                       request.form.getlist('bulk_ids'),
                                       omit_ids=[current_user.id],
                                       query=request.args.get('q', ''))

        # Prevent circular imports.
        from app.blueprints.billing.tasks import delete_users

        delete_users.delay(ids)

        flash('{0} user(s) were scheduled to be deleted.'.format(len(ids)),
              'success')
    else:
        flash('No users were deleted, something went wrong.', 'error')

    return redirect(url_for('admin.users'))


@admin.route('/backorders/bulk_delete', methods=['POST'])
def backorders_bulk_delete():
    form = BulkDeleteForm()

    if form.validate_on_submit():
        ids = Backorder.get_bulk_action_ids(request.form.get('scope'),
                                            request.form.getlist('bulk_ids'),
                                            omit_ids=[current_user.id],
                                            query=request.args.get('q', ''))

        # Prevent circular imports.
        from app.blueprints.billing.tasks import delete_backorders

        delete_backorders.delay(ids)

        flash('{0} backorders(s) were scheduled to be deleted.'.format(len(ids)),
              'success')
    else:
        flash('No backorders were deleted, something went wrong.', 'error')

    return redirect(url_for('admin.backorders'))


@admin.route('/users/cancel_subscription', methods=['POST'])
def users_cancel_subscription():
    form = UserCancelSubscriptionForm()

    if form.validate_on_submit():
        user = User.query.get(request.form.get('id'))

        if user:
            subscription = Subscription()
            if subscription.cancel(user):
                flash('Subscription has been canceled for {0}.'
                      .format(user.name), 'success')
        else:
            flash('No subscription was canceled, something went wrong.',
                  'error')

    return redirect(url_for('admin.users'))


# # Coupons ---------------------------------------------------------------------
# @admin.route('/coupons', defaults={'page': 1})
# @admin.route('/coupons/page/<int:page>')
# def coupons(page):
#     search_form = SearchForm()
#     bulk_form = BulkDeleteForm()
#
#     sort_by = Coupon.sort_by(request.args.get('sort', 'created_on'),
#                              request.args.get('direction', 'desc'))
#     order_values = '{0} {1}'.format(sort_by[0], sort_by[1])
#
#     paginated_coupons = Coupon.query \
#         .filter(Coupon.search(request.args.get('q', ''))) \
#         .order_by(text(order_values)) \
#         .paginate(page, 50, True)
#
#     return render_template('admin/coupon/index.html',
#                            form=search_form, bulk_form=bulk_form,
#                            coupons=paginated_coupons)


# @admin.route('/coupons/new', methods=['GET', 'POST'])
# @handle_stripe_exceptions
# def coupons_new():
#     coupon = Coupon()
#     form = CouponForm(obj=coupon)
#
#     if form.validate_on_submit():
#         form.populate_obj(coupon)
#
#         params = {
#             'code': coupon.code,
#             'duration': coupon.duration,
#             'percent_off': coupon.percent_off,
#             'amount_off': coupon.amount_off,
#             'currency': coupon.currency,
#             'redeem_by': coupon.redeem_by,
#             'max_redemptions': coupon.max_redemptions,
#             'duration_in_months': coupon.duration_in_months,
#         }
#
#         if Coupon.create(params):
#             flash('Coupon has been created successfully.', 'success')
#             return redirect(url_for('admin.coupons'))
#
#     return render_template('admin/coupon/new.html', form=form, coupon=coupon)
#
#
# @admin.route('/coupons/bulk_delete', methods=['POST'])
# def coupons_bulk_delete():
#     form = BulkDeleteForm()
#
#     if form.validate_on_submit():
#         ids = Coupon.get_bulk_action_ids(request.form.get('scope'),
#                                          request.form.getlist('bulk_ids'),
#                                          query=request.args.get('q', ''))
#
#         # Prevent circular imports.
#         from app.blueprints.billing.tasks import delete_coupons
#
#         delete_coupons.delay(ids)
#
#         flash('{0} coupons(s) were scheduled to be deleted.'.format(len(ids)),
#               'success')
#     else:
#         flash('No coupons were deleted, something went wrong.', 'error')
#
#     return redirect(url_for('admin.coupons'))
