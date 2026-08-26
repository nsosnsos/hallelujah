#!/usr/bin/env python3
"""main forms"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired


class ArticleForm(FlaskForm):
    """article form"""

    title = StringField(
        "Article Title",
        validators=[DataRequired()],
        render_kw={"autofocus": True},
    )
    content = TextAreaField(
        "Article Content",
        validators=[DataRequired()],
        render_kw={"rows": 20, "cols": 120},
    )
    is_public = BooleanField("Is Public")
    submit = SubmitField("Post Article")


class ResourceForm(FlaskForm):
    """resource form"""

    uri = StringField(
        "Resource URI",
        validators=[DataRequired()],
        render_kw={"autofocus": True},
    )
    title = StringField("Title")
    rank = StringField("Rank")
    category = StringField("Category")
    submit = SubmitField("Add Resource")


class DirectoryForm(FlaskForm):
    """directory form"""

    directory_name = StringField(
        "Directory Name",
        validators=[DataRequired()],
        render_kw={"autofocus": True},
    )
    submit = SubmitField("Add Directory")
