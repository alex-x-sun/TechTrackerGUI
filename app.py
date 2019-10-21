from flask import Flask, render_template, url_for, flash, redirect, request, g, session, request
from forms import RegistrationForm, LoginForm, TechScoutForm, TechAnalyticsForm
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField,SelectField
from wtforms import validators, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

import pandas as pd
from datetime import datetime

# for sqlite3 database test
import sqlite3
from dbTest import connect_db,  get_db

# for milestone string process



###############################################################################
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


############ user login control #################################################
def get_current_user():
    user_result = None

    if 'user' in session:
        user_email = session['user']

        db = get_db()
        user_cur = db.execute('select user_id, email, password, can_scout, can_analyse, can_edit, admin from users where email = ?', [user_email])
        user_result = user_cur.fetchone()

    return user_result


#################################################################################


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route("/")
@app.route("/home")
def home():
    user = get_current_user()
    return render_template('home.html', posts=posts, user = user)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    user = get_current_user()
    form = RegistrationForm()

    if request.method == 'POST':

        db = get_db()

        if form.validate_on_submit():
            username = form.username.data
            user_email = str(form.email.data).lower()
            hashed_password = generate_password_hash(form.password.data, method='sha256')

            existing_user_cur = db.execute('select user_id from users where email = ? or username = ?', [user_email, username])
            existing_user = existing_user_cur.fetchone()

            if existing_user:
                flash('User email already exist', 'danger')

            else:
                db.execute('insert into users (username, email, password) values (?, ?, ?)', [username, user_email, hashed_password])
                db.commit()


                flash('Account created', 'success')
                session['user'] = form.email.data
                return redirect(url_for('home'))

        else:
            flash('Invalid email or password')

    return render_template('register.html', title='Register', form=form, user = user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    user = get_current_user()
    form = LoginForm()

    if request.method == 'POST':
        db = get_db()

        if form.validate_on_submit():
            user_email = str(form.email.data).lower()
            password = form.password.data

            user_cur = db.execute('select user_id, email, password, can_scout, can_analyse, can_edit, admin from users where email = ?',[user_email])
            user_result = user_cur.fetchone()

            if user_result:

                if check_password_hash(user_result['password'], password):
                    session['user'] = user_result['email']
                    flash('You have been logged in!', 'success')
                    return redirect(url_for('home'))

            else:
                flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html', title='Login', user = user, form=form)

@app.route("/tech_scout", methods=['GET', 'POST'])
def tech_scout(tech=None):
    user = get_current_user()


    if not user:
        return redirect(url_for('login'))
    if user['can_scout'] == 0:
        flash('No access to TechScout. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    ######################### test only, link this part to the database later ###########################
    # sectors = ['Land Selection ', 'Design ' ,'Entitlement ', 'Capital Stack ', 'Construction ','Leasing & Brokerage ','Asset Monitoring & Operations ','Acquisition & Disposition ','Demolition ','Redevelopment ']
    #####################################################################################################
    db = get_db()
    sectors_cur = db.execute('select sec_id, sector from impacted_sector_order')
    sectors_results = sectors_cur.fetchall()

    form = TechScoutForm()

    tech_name = None

    if request.method == 'POST':
        trigger = True
        checkbox = request.form.getlist('mycheckbox')

        if len(checkbox) ==0:
            trigger = False #?


        if form.validate_on_submit():
            if tech:
                tech_name = tech
            else:
                tech = form.tech_name.data

            db.execute('insert into tech_main_log (contributor, tech_name, scout_time, description, impact, desc_source, asso_names, impa_sector, emb_techs, wiki_link, category) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [user['user_id'], tech_name, datetime.timestamp(datetime.now()), form.description.data, form.impact.data, form.sources.data, form.associate_names.data, ';'.join(checkbox), form.embed_tech.data, form.wikilink.data, form.category.data])

            # we might need some cleaner functions here
            db.commit()
            flash(f'Technology {form.tech_name.data} added', 'success')


            # if form.submit:
            #     return redirect(url_for('home'))
            # elif form.submit_proceed:
            #     return redirect(url_for('tech_analytics'))


        else:
            flash(form.errors if len(form.errors)!= 0 else 'select Impact Sectors', 'danger') #spits out any and all errors**
        # if form.validate_on_submit():
        #     print('yea')
        #     flash(f'Technology {form.tech_name.data} added')
        #     return redirect(url_for('home'))
        # else:

#################### NEXT STEPS: USE SESSION TO MAKE THE CONFIRMATION PAGE ###################

##############################################################################################

    return render_template('tech_scout.html', title='Technology Scout', user= user, tech=tech, form=form, sectors = sectors_results, tech_name=tech_name)

@app.route("/task_board_a", methods = ['GET', 'POST'])
def task_board_a():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_analyse'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))
    # get all tech scout outcomes that needs analysis
    ## NOTE: Here we query the tech_main_log table #######
    db = get_db()
    ## sqlite3 specific datetime function!!
    task_cur = db.execute('''select
                                tml.tech_name tech_name,
                                datetime(tml.scout_time,'unixepoch') scout_time,
                                u.username contributor_name
                            from tech_main_log tml, users u
                            where tml.tech_name in
                                (select distinct tech_name from tech_main_log)
                            and tml.contributor = u.user_id
                            group by tech_name
                            order by lower(tech_name) asc''')

    task_result = task_cur.fetchall()

    return render_template('task_board_a.html', title='Task Board', user= user, tasks = task_result)


@app.route("/tech_analytics/<tech>", methods = ['GET', 'POST'])
def tech_analytics(tech):
    db = get_db()
    # check user
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_analyse'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    # check & show progress
    # get all finished milestones

################## TEST ONLY ########################
# use tech_story in the future

    stories_cur = db.execute('''
                            select
                                tsl.milestone, tsl.story_content, tsl.story_year, u.username contributor_name, datetime(tsl.contribute_time,'unixepoch') contribute_time
                            from tech_story_log tsl, users u
                            where tsl.tech_name = ?
                            and tsl.contributor = u.user_id
                            order by tsl.story_year
                            ''', [tech])
    stories_results = stories_cur.fetchall()


    ms_cur = db.execute('''
                            select ms_left.ms_name, ms.milestone_id
                            from milestones ms,
                                 (select distinct m.ms_name
                                  from milestones m

                                  except

                                  select distinct milestone ms
                                  from tech_story_log
                                  where tech_name = ?) ms_left
                            where ms_left.ms_name = ms.ms_name
                            order by ms.milestone_id

                           ''', [tech])
    milestones = ms_cur.fetchall()

#####################################################

    # form process
    form = TechAnalyticsForm()
    if form.validate_on_submit():

        # check repeat form
        existing_ms_cur = db.execute('''
                                    select log_s_id
                                    from tech_story_log
                                    where story_content = ?
                                    and contributor = ?
                                    ''', [form.story_content.data, user['user_id']])
        existing_ms = existing_ms_cur.fetchone()

        if existing_ms:
            flash('You have already submitted this story', 'danger')
        else:
            # commit changes
            db.execute('''insert into tech_story_log
                            (contributor, tech_name, contribute_time, story_year, story_date, story_content, milestone, source)
                          values (?, ?, ?, ?, ?, ?, ?, ?)''', [user['user_id'], tech, datetime.timestamp(datetime.now()), form.story_year.data, form.story_date.data, form.story_content.data, form.milestone.data,  form.sources.data])

            # we might need some cleaner functions here
            db.commit()
            flash(f'New story added', 'success')
            return redirect(url_for('tech_analytics',tech=tech))

    return render_template('tech_analytics.html', title='Technology Analytics', user= user, form=form, milestones = milestones, stories = stories_results, tech=tech)

@app.route("/task_board_e", methods = ['GET', 'POST'])
def task_board_e():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_analyse'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))
    # get all tech scout outcomes that needs analysis
    ## NOTE: Here we query the tech_main_log table #######
    db = get_db()
    ## sqlite3 specific datetime function!!
    task_cur = db.execute('''select
                                tml.tech_name tech_name,
                                datetime(tml.scout_time,'unixepoch') scout_time,
                                u.username contributor_name
                            from tech_main_log tml, users u
                            where tml.tech_name in
                                (select distinct tech_name from tech_main_log)
                            and tml.contributor = u.user_id
                            group by tech_name
                            order by lower(tech_name) asc''')

    task_result = task_cur.fetchall()

    return render_template('task_board_e.html', title='Task Board', user= user, tasks = task_result)

@app.route("/tech_edit", methods = ['GET', 'POST'])
def tech_edit():

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_edit'] == 0:
        flash('No access to TechEdit. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    return '<h1>Tech Edit </h1>'

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        flash('You are not an administrator', 'danger')
        return redirect(url_for('home'))

    db = get_db()
    users_cur = db.execute('select user_id, username, email, can_scout, can_analyse, can_edit, admin from users')
    users_results = users_cur.fetchall()

    return render_template('admin.html', user=user, users=users_results)

if __name__ == '__main__':
    app.run(debug=True)
