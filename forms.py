from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextField, IntegerField, TextAreaField, RadioField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from wtforms import TextAreaField

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
    associate_names = StringField('Associate Names', validators=[DataRequired(), Regexp(regex =r'[a-zA-Z]|[0-9]|\;|\s',message="letter, number and ; only")])
    category =  SelectField('Properties*', choices = [('product','Product'),('process', 'Process'),('use','Use')])
    description = TextAreaField('Technology Description*',render_kw={"rows": 12},
                            validators=[DataRequired(), Length(min=2)])
    impact = TextAreaField('Building Environment Impact*', render_kw={"rows": 8},
                        validators = [DataRequired(), Length(min=2)])
    # sector = SelectMultipleField('')
    embed_tech = StringField('Embedded Technologies', validators=[DataRequired(), Regexp(regex =r'[a-zA-Z]|[0-9]|\;|\s',message="letter, number and ; only")])
    sources = TextAreaField('Sources*', render_kw={"rows": 2}, validators=[DataRequired(), Regexp(regex=r'[a-zA-z]+://[^s]*',message="input valid url")])


    submit = SubmitField('Submit')


class TechEditForm(FlaskForm):


    submit = SubmitField('Submit')
