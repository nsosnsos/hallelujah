#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from sqlalchemy import exc
from flask import Blueprint, current_app, url_for, session, render_template, request, flash
from flask_login import current_user, login_user, logout_user, login_required

from ..extensions import db, login_manager
from ..models import User
from ..utility import get_request_ip, redirect_save, redirect_back, send_email
from .forms import LoginForm, RegisterForm, SettingForm


bp_auth = Blueprint('auth', __name__)

@login_manager.unauthorized_handler
def unauthorized():
    redirect_save(url_for(request.endpoint, **request.view_args, _external=True))
    return redirect_back('auth.login')

@bp_auth.route('login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_back()

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(db.or_(User.name == form.username.data, User.email == form.username.data.lower())).first()
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            if form.remember.data:
                session.permanent = True
            current_user.update_last_seen()
            current_app.logger.info('Auth: login user {}.'.format(user.name))
            ip_addr = get_request_ip(request)
            login_info = {'user_name': user.name, 'ip_addr': ip_addr, 'last_seen': user.last_seen}
            flash(login_info, category='login')
            return redirect_back(redirect_before=True)
        flash('Invalid Username or Password')
    redirect_save(request.referrer)
    return render_template('auth/login.html', form=form)

@bp_auth.route('logout')
@login_required
def logout():
    current_app.logger.info('Auth: logout user {}.'.format(current_user.name))
    logout_user()
    flash('You are logged out.')
    return redirect_back()

@bp_auth.route('profile')
@login_required
def profile():
    name, email = current_user.name, current_user.email
    return render_template('auth/profile.html', name=name, email=email)

@bp_auth.route('setting', methods=['GET', 'POST'])
@login_required
def setting():
    form = SettingForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('Invalid old password.')
        elif form.new_password.data != form.confirm_password.data:
            flash('The passwords does not match.')
        else:
            current_user.password = form.new_password.data
            db.session.add(current_user)
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                current_app.logger.error('setting: {}'.format(str(e)))
                return
            current_app.logger.info('Auth: setting user {}.'.format(current_user.name))
            flash('Your password has been updated.')
            return redirect_back(redirect_before=True)
    redirect_save(request.referrer)
    return render_template('auth/setting.html', form=form)

@bp_auth.route('register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if not current_app.config.get('SYS_REGISTER'):
            flash('Register is closed for now, sorry about that.')
        elif User.query.filter(User.name == form.username.data).first():
            flash('Username has been taken, please choose again')
        elif User.query.filter(User.email == form.email.data.lower()).first():
            flash('Email has been taken, please choose again')
        elif form.password.data != form.confirm_password.data:
            flash('The passwords does not match.')
        else:
            user = User(name=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            try:
                db.session.commit()
            except exc.SQLAlchemyError as e:
                current_app.logger.error('register: {}'.format(str(e)))
                return
            thread = send_email(to=user.email, subject=current_app.config.get('SITE_NAME'),
                                msg=f'Hello, {user.name}. Thanks for registering!')
            thread.join()
            current_app.logger.info('Auth: register user {}.'.format(user.name))
            flash('Success! Welcome {}!'.format(user.name))
            return redirect_back('auth.login')
    return render_template('auth/register.html', form=form)

