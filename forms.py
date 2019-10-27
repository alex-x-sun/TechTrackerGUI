from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextField, IntegerField, TextAreaField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, URL, Optional
from wtforms import TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from milestones import milestones_tuplist



regex_url = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

regex_multi_url = regex_url # change this

regex_words_semicolumns = r'([a-zA-Z0-9_]+(;\s|;))*([a-zA-Z0-9_]+)'

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])

    password = PasswordField('Password', validators=[DataRequired()])

    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class TechScoutForm(FlaskForm):
    tech_name = StringField('Technology Name*',
                            validators=[DataRequired(), Length(min=2, max=40)])
    associate_names = StringField('Associate Names*', validators=[DataRequired(),Regexp(regex = regex_words_semicolumns , message="letters or numbers separated by ; only")])
    category =  SelectField('Properties*', choices = [('product','Product'),('process', 'Process'),('use','Use')])
    description = TextAreaField('Technology Description*',render_kw={"rows": 12},
                            validators=[DataRequired(), Length(min=2)])
    impact = TextAreaField('Built Environment Impact*', render_kw={"rows": 8},
                        validators = [DataRequired(), Length(min=2)])
    # sector = SelectMultipleField('')
    embed_tech = StringField('Embedded Technologies*', validators=[DataRequired(), Regexp(regex = regex_words_semicolumns ,message="letters or numbers separated by ; only")])

    sources = TextAreaField('Sources*', render_kw={"rows": 3}, validators=[DataRequired(),Regexp(regex = regex_multi_url ,message="not a valid url or url list")])

    wikilink = TextAreaField('Wikipedia Link', render_kw={"rows": 1}, validators=[Optional()])

    submit = SubmitField('Submit')


class TechAnalyticsForm(FlaskForm):
    story_year = IntegerField('Year*')
    story_date = StringField('Date', validators=[Optional(), Regexp(regex =r'(0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])',message="Please insert data in mm/dd format")])
    milestone = SelectField('Milestone*', choices = [])
    story_content = TextAreaField('Story Content*',render_kw={"rows": 12})
    sources = TextAreaField('Sources*', render_kw={"rows": 3})
    submit = SubmitField('Submit')



class EditTechStoryForm(FlaskForm):
    story_year = IntegerField('Year*')
    story_date = StringField('Date', validators=[Optional(), Regexp(regex =r'(0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])',message="Please insert data in mm/dd format")])
    milestone = SelectField('Milestone*', choices = [])
    story_content = TextAreaField('Story Content*',render_kw={"rows": 12})
    sources = TextAreaField('Sources*', render_kw={"rows": 3})
    submit = SubmitField('Confirm & Submit Edit')
