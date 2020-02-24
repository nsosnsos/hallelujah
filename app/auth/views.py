# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user

from .. import db
from ..models import User
from ..utilities import send_email
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ChangeEmailForm,\
    PasswordResetForm, PasswordResetRequestForm


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.update_last_seen()
        if not current_user.confirmed and request.endpoint and \
                request.blueprint != 'auth' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(db.or_(User.email == form.id.data.lower(), User.name == form.id.data)).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember.data)
            next_url = request.args.get('next')
            if next_url is None or not next_url.startswith('/'):
                next_url = url_for('main.index')
            flash('Welcome {} [{}].'.format(user.name, request.remote_addr))
            return redirect(next_url)
        flash('Invalid user or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/info/')
@login_required
def info():
    return render_template('auth/info.html')


@auth.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.id.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        confirm_token = user.get_confirm_token()
        send_email(user.email, 'Confirm your account', 'auth/email/confirm', user=user, token=confirm_token)
        flash('A confirmation email has been sent to you, please confirm by the email link.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/change_password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        flash('Invalid password.')
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset_password/', methods=['GET', 'POST'])
def request_reset_password():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter(db.or_(User.email == form.id.data.lower(), User.name == form.id.data)).first()
        if user:
            token = user.get_password_reset_token()
            send_email(user.email, 'Reset your password', 'auth/email/reset_password',
                       site_name=current_app.config['SITE_NAME'], user=user, token=token)
            flash('An email with instructions to reset your password has been sent to you.')
            return redirect(url_for('auth.login'))
        flash('Invalid user.')
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.new_password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid request.')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email/', methods=['GET', 'POST'])
@login_required
def request_change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.new_email.data.lower()
            token = current_user.get_email_change_token(new_email)
            send_email(current_user.email, 'Change your email', 'auth/email/change_email',
                       site_name=current_app.config['SITE_NAME'], user=current_user, token=token)
            flash('An email with instructions to change your email has been sent to you.')
            return redirect(url_for('main.index'))
        flash('Invalid password.')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))


@auth.route('/confirm/')
@login_required
def request_confirm():
    if current_user.confirmed:
        flash('Your account has already been confirmed.')
        return redirect(url_for('main.index'))
    token = current_user.get_confirm_token()
    send_email(current_user.email, 'Confirm your account', 'auth/email/confirm',
               site_name=current_app.config['SITE_NAME'], user=current_user, token=token)
    flash('A confirmation email has been resent to you, please confirm by the email link.')
    return redirect(url_for('main.index'))


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('Your account has already been confirmed.')
    if current_user.confirm(token):
        db.session.commit()
        flash('Your account has been confirmed.')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/unconfirmed/')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')
