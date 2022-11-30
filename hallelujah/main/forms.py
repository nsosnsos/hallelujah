#!/usr/bin/env python3
# -*- coding:utf-8 -*-


from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class ArticleForm(FlaskForm):
    title = StringField('Article Title', validators=[DataRequired()], render_kw={'autofocus': True})
    content = TextAreaField('Article Content', validators=[DataRequired()], render_kw={'rows': 20, 'cols': 120})
    is_public = BooleanField('Is Public')
    submit = SubmitField('Post Article')

class ResourceForm(FlaskForm):
    uri = StringField('Resource URI', validators=[DataRequired()], render_kw={'autofocus': True})
    title = StringField('Title')
    rank = StringField('Rank')
    category = StringField('Category')
    submit = SubmitField('Add Resource')

