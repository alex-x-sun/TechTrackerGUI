from flask import Flask, render_template, url_for, flash, redirect, request, g
from forms import RegistrationForm, LoginForm, TechScoutForm
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField,SelectField
from wtforms import validators, ValidationError

from datetime import datetime
datetime.now()
# for sqlite3 database test
import sqlite3
from dbTest import connect_db,  get_db

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

############ Change this part after we finish user login control ################
current_user = 0
#################################################################################



@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

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
    db = get_db()

    ######################### test only, link this part to the database later ###########################
    # sectors = ['Land Selection ', 'Design ' ,'Entitlement ', 'Capital Stack ', 'Construction ','Leasing & Brokerage ','Asset Monitoring & Operations ','Acquisition & Disposition ','Demolition ','Redevelopment ']
    #####################################################################################################

    sectors_cur = db.execute('select sec_id, sector from impacted_sector_order')
    sectors_results = sectors_cur.fetchall()

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

            db.execute('insert into tech_main_log (contributor, tech_name, scout_time, description, impact, desc_source, asso_names, impa_sector, emb_techs) values (?, ?, ?, ?, ?, ?, ?, ?, ?)', [current_user, form.tech_name.data, datetime.timestamp(datetime.now()), form.description.data, form.impact.data, form.sources.data, form.associate_names.data, ';'.join(checkbox), form.embed_tech.data])

            # we might need some cleaner functions here
            db.commit()

            return redirect(url_for('home'))
        else:
            flash(form.errors if len(form.errors)!= 0 else 'select Impact Sectors', 'danger') #spits out any and all errors**
        # if form.validate_on_submit():
        #     print('yea')
        #     flash(f'Technology {form.tech_name.data} added')
        #     return redirect(url_for('home'))
        # else:

    return render_template('tech_scout.html', title='Technology Scout', form=form, sectors = sectors_results)

@app.route("/tech_analytics", methods = ['GET', 'POST'])
def tech_analytics():
    return None

@app.route("/tech_edit", methods = ['GET', 'POST'])
def tech_edit():
    return None


if __name__ == '__main__':
    app.run(debug=True)
