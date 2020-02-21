# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from config import Config
from ..models import User


class LoginForm(FlaskForm):
    id = StringField('Id/Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Keep me login in')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    id = StringField('Id', validators=[DataRequired(), Length(5, Config.SHORT_STR_LEN),
                     Regexp(regex='^[A-Za-z][A-Za-z0-9_.]*$', message='Username must start with letters, '
                            'having only letters, numbers, dots or underscores.')])
    email = StringField('Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    confirm_password = PasswordField('Confirm password',
                                     validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                 EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_id(self, field):
        if not self.is_submitted() or User.query.filter_by(name=field.data).first():
            raise ValidationError('Id already registered.')

    def validate_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    confirm_new_password = PasswordField('Confirm new password',
                                         validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                     EqualTo('new_password', message='Passwords mush match.')])
    submit = SubmitField('Change password')


class PasswordResetRequestForm(FlaskForm):
    id = StringField('Id/Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    submit = SubmitField('Reset password')


class PasswordResetForm(FlaskForm):
    new_password = PasswordField('New password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)])
    confirm_new_password = PasswordField('Confirm new password',
                                         validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                     EqualTo('new_password', message='Passwords mush match.')])
    submit = SubmitField('Reset password')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('New email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Change email')

    @staticmethod
    def validate_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')
