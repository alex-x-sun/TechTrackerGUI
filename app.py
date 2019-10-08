from flask import Flask, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, TechScoutForm
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField,SelectField
from wtforms import validators, ValidationError

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/tech_scout", methods=['GET', 'POST'])
def tech_scout():
    form = TechScoutForm()
    if request.method == 'POST':
        trigger = True
        checkbox = request.form.getlist('mycheckbox')
        if len(checkbox) ==0:
            trigger = False
        print(checkbox)
        if form.validate() and trigger == True:
            print('yea')
            flash(f'Technology {form.tech_name.data} added', 'success')
            return redirect(url_for('home'))
        else:
            flash(form.errors if len(form.errors)!= 0 else 'select Impact Sectors', 'danger') #spits out any and all errors**
        # if form.validate_on_submit():
        #     print('yea')
        #     flash(f'Technology {form.tech_name.data} added')
        #     return redirect(url_for('home'))
        # else:
    return render_template('tech_scout.html', title='Technology Scout', form=form)





if __name__ == '__main__':
    app.run(debug=True)