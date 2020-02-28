# !/usr/bin/env python
# -*- coding:utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp
from flask_pagedown.fields import PageDownField

from config import Config
from ..models import Role, User, Category


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    description = TextAreaField('describe yourself')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    id = StringField('Username', validators=[DataRequired(), Length(5, Config.SHORT_STR_LEN),
                     Regexp(regex='^[A-Za-z][A-Za-z0-9_.]*$', message='Username must start with letters, '
                            'having only letters, numbers, dots or underscores.')],
                     render_kw={'autofocus': True, 'placeholder': 'Username'})
    email = StringField('Email', validators=[DataRequired(), Length(1, Config.SHORT_STR_LEN), Email()],
                        render_kw={'placeholder': 'Email'})
    description = TextAreaField('describe yourself')
    confirmed = BooleanField('Confirmed')
    role_id = SelectField('Role', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role_id.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_id(self, field):
        if not self.is_submitted() or User.query.filter_by(name=field.data).first():
            raise ValidationError('Id already registered.')

    def validate_email(self, field):
        if not self.is_submitted() or User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')


class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = PageDownField("What's on your mind?", validators=[DataRequired()])
    is_private = BooleanField('Private')
    category_id = SelectField('Category', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.name) for category in
                                    Category.query.order_by(Role.name).all()]


class CommentForm(FlaskForm):
    content = StringField("Comment here", validators=[DataRequired()])
    submit = SubmitField('Submit')
