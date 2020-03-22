# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField  # , ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp  # , EqualTo

from config import Config
# from ..models import User


class LoginForm(FlaskForm):
    id = StringField(_l('Username/Email'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                     render_kw={'autofocus': True, 'placeholder': _l('Username or Email'), 'required': 'required',
                                'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    password = PasswordField(_l('Password'), validators=[DataRequired()],
                             render_kw={'placeholder': _l('Password'), 'required': 'required',
                                        'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    remember = BooleanField(_l('Remember me', render_kw={'required': 'required', 'checked': 'checked'}))
    submit = SubmitField(_l('Login'))


class RegistrationForm(FlaskForm):
    id = StringField(_l('Username'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN),
                     Regexp(regex='^[A-Za-z][A-Za-z0-9_.]*$', message=_l('Username must start with letters, '
                            'having only letters, numbers, dots or underscores.'))],
                     render_kw={'autofocus': True, 'placeholder': _l('Username'), 'required': 'required',
                                'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN,
                                'pattern': r'^[A-Za-z][A-Za-z0-9_.]*$'})
    email = StringField(_l('Email'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()],
                        render_kw={'placeholder': _l('Email'), 'required': 'required',
                                   'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN,
                                   'pattern': r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$'})
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                             render_kw={'placeholder': _l('Password'), 'required': 'required',
                                        'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN,
                                        'pattern': r'^\S{6,}$'})
    confirm_password = PasswordField(_l('Confirm password'),
                                     validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)
                                                 # ,EqualTo('password', message=_l('Passwords must match.'))
                                                 ],
                                     render_kw={'placeholder': _l('Confirm password'), 'required': 'required',
                                                'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN,
                                                'pattern': r'^\S{6,}$'})
    submit = SubmitField(_l('Register'))


"""
    def validate_id(self, field):
        if not self.is_submitted() or User.query.filter_by(name=field.data).first():
            raise ValidationError(_l('This id has already been registered.'))

    def validate_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError(_l('This email has already been registered.'))
"""


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(_l('Old password'), validators=[DataRequired()],
                                 render_kw={'autofocus': True, 'placeholder': _l('Old password'),
                                            'required': 'required', 'minlength': Config.MIN_STR_LEN,
                                            'maxlength': Config.SHORT_STR_LEN})
    password = PasswordField(_l('New password'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                             render_kw={'placeholder': _l('New password'), 'required': 'required',
                                        'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    confirm_password = PasswordField(_l('Confirm new password'),
                                     validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)
                                                 # ,EqualTo('password', message=_l('Passwords mush match.'))
                                                 ],
                                     render_kw={'placeholder': _l('Confirm new password'), 'required': 'required',
                                                'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    submit = SubmitField(_l('Change password'))


class PasswordResetRequestForm(FlaskForm):
    id = StringField(_l('Username/Email'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                     render_kw={'autofocus': True, 'placeholder': _l('Username or Email'), 'required': 'required',
                                'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    submit = SubmitField(_l('Reset password'))


class PasswordResetForm(FlaskForm):
    password = PasswordField(_l('New password'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)],
                             render_kw={'autofocus': True, 'placeholder': _l('New password'), 'required': 'required',
                                        'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    confirm_password = PasswordField(_l('Confirm new password'),
                                     validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN)
                                                 # ,EqualTo('password', message=_l('Passwords mush match.'))
                                                 ],
                                     render_kw={'placeholder': _l('Confirm new password'), 'required': 'required',
                                                'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    submit = SubmitField(_l('Reset password'))


class ChangeEmailForm(FlaskForm):
    new_email = StringField(_l('New email'), validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()],
                            render_kw={'autofocus': True, 'placeholder': _l('New email'), 'required': 'required',
                                       'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    password = PasswordField(_l('Password'), validators=[DataRequired()],
                             render_kw={'placeholder': _l('Password'), 'required': 'required',
                                        'minlength': Config.MIN_STR_LEN, 'maxlength': Config.SHORT_STR_LEN})
    submit = SubmitField(_l('Change email'))


"""
    def validate_new_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError(_l('This email has already been registered.'))
"""
