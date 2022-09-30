#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from sqlalchemy import exc
from flask import Blueprint, current_app, url_for, session, render_template, request, redirect, flash
from flask_login import current_user, login_user, logout_user, login_required

from ..extensions import db, login_manager
from ..models import User
from ..utility import redirect_before, redirect_save, redirect_back
from .forms import LoginForm, RegisterForm, SettingForm


bp_auth = Blueprint('auth', __name__)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('auth.login', next=request.endpoint, _external=True))

@bp_auth.route('login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_before()

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(db.or_(User.name == form.username.data, User.email == form.username.data.lower())).first()
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            if 'Cf-Connecting-Ip' in request.headers:
                ip_addr = request.headers['Cf-Connecting-Ip']
            else:
                ip_addr = request.headers.get('X-Real-Ip', request.remote_addr)
            login_info = {'user_name': user.name, 'ip_addr': ip_addr, 'last_seen': user.last_seen}
            flash(login_info, category='login')
            current_user.update_last_seen()
            return redirect_before()
        flash('Invalid Username or Password')
    redirect_save(request.referrer)
    return render_template('auth/login.html', form=form)

@bp_auth.route('logout')
@login_required
def logout():
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
                current_app.config.get('LOGGER').error('setting: {}'.format(str(e)))
                return
            flash('Your password has been updated.')
            return redirect_before()
    redirect_save(request.referrer)
    return render_template('auth/setting.html', form=form)

@bp_auth.route('register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter(User.name == form.username.data).first():
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
                current_app.config.get('LOGGER').error('register: {}'.format(str(e)))
                return
            flash('Success! Welcome {}!'.format(user.name))
            return redirect(url_for('auth.login', _external=True))
    redirect_save(request.referrer)
    return render_template('auth/register.html', form=form)

