#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, Email, EqualTo

from ..config import Config


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN)], render_kw={'autofocus': True})
    password = StringField('Password', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN)])
    remember = BooleanField('Remember')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN),
                           Regexp(regex='^[A-Za-z][A-Za-z0-9_.]*$', message='Invalid username.')],
                           render_kw={'autofocus': True})
    email = StringField('Email', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN),
                        Regexp(regex='([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+',
                               message='Invalid email.')])
    password = StringField('Password', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN)])
    confirm_password = StringField('Confirm Password', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN),
                                   EqualTo('password', message='Passwords mush match.')])
    submit = SubmitField('Register')

class SettingForm(FlaskForm):
    old_password = StringField('Old Password', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN)], render_kw={'autofocus': True})
    new_password = StringField('New Password', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN)])
    confirm_password = StringField('Confirm Password', validators=[DataRequired(), Length(Config.MIN_STR_LEN, Config.SHORT_STR_LEN),
                                   EqualTo('new_password', message='Passwords mush match.')])
    submit = SubmitField('Apply')

