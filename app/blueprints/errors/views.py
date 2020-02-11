from flask import (
  Blueprint,
  current_app,
  render_template,
  url_for,
  request,
  redirect,
  flash,
)
from app.extensions import csrf

errors = Blueprint('errors', __name__, template_folder='templates')


@errors.route('/error_404', methods=['GET','POST'])
@csrf.exempt
def error_404():
    return render_template('errors/404.html')


@errors.route('/error_500', methods=['GET','POST'])
@csrf.exempt
def error_500():
    return render_template('errors/500.html')