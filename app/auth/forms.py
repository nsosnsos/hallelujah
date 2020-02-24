# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo

from config import Config
from ..models import User


class LoginForm(FlaskForm):
    id = StringField('Username/Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                     render_kw={'autofocus': True, 'placeholder': 'Username or Email'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'placeholder': 'Password'})
    remember = BooleanField('Keep me login in')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    id = StringField('Username', validators=[DataRequired(), Length(5, Config.SHORT_STR_LEN),
                     Regexp(regex='^[A-Za-z][A-Za-z0-9_.]*$', message='Username must start with letters, '
                            'having only letters, numbers, dots or underscores.')],
                     render_kw={'autofocus': True, 'placeholder': 'Username'})
    email = StringField('Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()],
                        render_kw={'placeholder': 'Email'})
    password = PasswordField('Password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                             render_kw={'placeholder': 'Password'})
    confirm_password = PasswordField('Confirm password',
                                     validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                 EqualTo('password', message='Passwords must match.')],
                                     render_kw={'placeholder': 'Confirm password'})
    submit = SubmitField('Register')

    def validate_id(self, field):
        if not self.is_submitted() or User.query.filter_by(name=field.data).first():
            raise ValidationError('Id already registered.')

    def validate_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()],
                                 render_kw={'autofocus': True, 'placeholder': 'Old password'})
    new_password = PasswordField('New password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                                 render_kw={'placeholder': 'New password'})
    confirm_new_password = PasswordField('Confirm new password',
                                         validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                     EqualTo('new_password', message='Passwords mush match.')],
                                         render_kw={'placeholder': 'Confirm new password'})
    submit = SubmitField('Change password')


class PasswordResetRequestForm(FlaskForm):
    id = StringField('Username/Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                     render_kw={'autofocus': True, 'placeholder': 'Username or Email'})
    submit = SubmitField('Reset password')


class PasswordResetForm(FlaskForm):
    new_password = PasswordField('New password', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                                 render_kw={'autofocus': True, 'placeholder': 'New password'})
    confirm_new_password = PasswordField('Confirm new password',
                                         validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                                                     EqualTo('new_password', message='Passwords mush match.')],
                                         render_kw={'placeholder': 'Confirm new password'})
    submit = SubmitField('Reset password')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('New email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()],
                            render_kw={'autofocus': True, 'placeholder': 'New email'})
    password = PasswordField('Password', validators=[DataRequired()],
                             render_kw={'placeholder': 'Password'})
    submit = SubmitField('Change email')

    @staticmethod
    def validate_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')
