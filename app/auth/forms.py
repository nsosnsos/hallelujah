# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from config import Config
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Keep me login in')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                           Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Username must start with letters, '
                                  'having only letters, numbers, dots or underscores.')])
    email = StringField('Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    confirm_password = PasswordField('Confirm password',
                                     validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                 EqualTo('password', message='Passwords mush match.')])
    submit = SubmitField('Submit')

    @staticmethod
    def validate_email(field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

    @staticmethod
    def validate_username(field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('Username already registered.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    confirm_new_password = PasswordField('Confirm new password',
                                         validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                     EqualTo('new_password', message='Passwords mush match.')])


class PasswordResetForm(FlaskForm):
    new_password = PasswordField('New password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    confirm_new_password = PasswordField('Confirm new password',
                                         validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                     EqualTo('new_password', message='Passwords mush match.')])
    submit = SubmitField('Submit')


class ChangeEmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

    @staticmethod
    def validate_email(field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')
