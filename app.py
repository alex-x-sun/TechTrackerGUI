from flask import Flask, render_template, url_for, flash, redirect, request, g, session, request
from forms import RegistrationForm, LoginForm, TechScoutForm, TechAnalyticsForm, EditTechStoryForm
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField,SelectField
from wtforms import validators, ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from werkzeug.security import generate_password_hash, check_password_hash

import json
import pandas as pd
from datetime import datetime, timedelta
import time
# for sqlite3 database test
import sqlite3
from dbTest import connect_db,  get_db
from random import randrange
# if use Hydrogen or Jupyter
# ipython3 kernelspec install-self

# for milestone string process
from milestones import milestones, milestones_tuplist


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


############ helper functions #################################################
def get_current_user():
    user_result = None

    if 'user' in session:
        user_email = session['user']

        db = get_db()
        user_cur = db.execute('select user_id, email, password, can_scout, can_analyse, can_edit, admin from users where email = ?', [user_email])
        user_result = user_cur.fetchone()

    return user_result

def repeat_scout_checker(form, mode = 'scout_only'):
    db = get_db()

    # check repeat form
    if mode == 'scout_only':
        existing_sc_cur = db.execute('''
                                    select log_id
                                    from tech_main_log
                                    where tech_name = ?
                                    ''', [form.tech_name.data])
        existing_sc = existing_sc_cur.fetchone()
    elif mode == 'full_check':
        existing_sc_cur = db.execute('''
                                    select log_id
                                    from tech_main_log
                                    where tech_name = ?
                                    and description = ?
                                    and impact = ?

                                    and asso_names = ?
                                    and emb_techs = ?
                                    and category = ?
                                    and desc_source = ?
                                    ''', [form.tech_name.data, form.description.data, form.impact.data, form.associate_names.data, form.embed_tech.data, form.category.data, form.sources.data])
        existing_sc = existing_sc_cur.fetchone()

    return existing_sc

def repeat_story_checker(form):
    db = get_db()
    # check repeat form
    existing_ms_cur = db.execute('''
                                select log_s_id
                                from tech_story_log
                                where story_year = ?
                                and story_date = ?
                                and milestone = ?
                                and story_content = ?
                                and sources = ?
                                ''', [form.story_year.data, form.story_date.data, form.milestone.data, form.story_content.data, form.sources.data])
    existing_ms = existing_ms_cur.fetchone()
    return existing_ms

def random_date(year):
    """
    This function will return a random datetime in a year
    """
    start = datetime.strptime(str(year) + '/01/01', '%Y/%m/%d')
    end = datetime.strptime(str(year+1) + '/01/01', '%Y/%m/%d')
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return datetime.timestamp(start + timedelta(seconds=random_second))

# random_date(1996)

#################################################################################
# form = ['A','B','C','D','E']
# sql_where = 'where'
# for field in form[:-1]:
#     sql_where += str(field) + ' = ? and '
#
# sql_where += str(form[-1]) + ' = ? '
# sql_where

def repeat_checker(form, table_name):
    """
    This function requires that the field naming should be consistent in all tables and forms
    """
    db = get_db()
    form_data = [field.data for field in form]
    sql_where = 'where'
    for field in form[:-1]:
        sql_where += str(field.name) + ' = ? and '

    sql_where += str(form[-1].name) + ' = ? '

    existing_cur = db.execute('select * from' + str(table_name) + sql_where, form_data)
    existing = existing_cur.fetchone()

    return existing
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
def tech_scout():
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


        if form.validate_on_submit() and trigger:

            if repeat_scout_checker(form):
                flash(f'Scout field: The Technology {form.tech_name.data} already exists. Please check.', 'danger')
            else:
                db.execute('''
                            insert into tech_main_log
                                (contributor, tech_name, scout_time, description, impact, desc_source, asso_names, impa_sector, emb_techs, wiki_link, category)
                            values
                                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', [user['user_id'], form.tech_name.data, datetime.timestamp(datetime.now()), form.description.data, form.impact.data, form.sources.data, form.associate_names.data, ';'.join(checkbox), form.embed_tech.data, form.wikilink.data, form.category.data])

                # we might need some cleaner functions here
                db.commit()
                flash(f'Technology {form.tech_name.data} added', 'success')

        else:
            flash(form.errors if len(form.errors)!= 0 else 'Select Impact Sectors', 'danger') #spits out any and all errors**
        # if form.validate_on_submit():
        #     print('yea')
        #     flash(f'Technology {form.tech_name.data} added')
        #     return redirect(url_for('home'))
        # else:



    return render_template('tech_scout.html', title='Technology Scout', user= user, form=form, sectors = sectors_results, tech_name=tech_name)

#################### NEXT STEPS: USE SESSION TO MAKE THE CONFIRMATION PAGE ###################

##############################################################################################

@app.route("/task_board_a", methods = ['GET', 'POST'])
def task_board_a():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_analyse'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))
############ get all tech scout outcomes that needs analysis ##############
    ## NOTE: Here we query the tech_main_log table #######
    db = get_db()
    ## sqlite3 specific datetime function!!
    task_cur = db.execute('''select
                                tml.log_id log_id,
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
# sqlite3 specific functions: substr() for substring(), || for concat()
    stories_cur = db.execute('''
                            select
                                tsl.log_s_id log_s_id,
                                tsl.milestone,
                                substr(tsl.story_content, 1, 100)|| '...' story_content, tsl.story_year,
                                tsl.contributor contributor_id,
                                u.username contributor_name, datetime(tsl.contribute_time,'unixepoch') contribute_time
                            from tech_story_log tsl, users u, milestones m
                            where tsl.tech_name = ?
                            and tsl.contributor = u.user_id
                            and tsl.milestone = m.ms_name
                            order by tsl.story_year asc, m.milestone_id

                            ''', [tech])
    stories_results = stories_cur.fetchall()


    ms_cur = db.execute('''
                            select ms_left.ms_name ms_name, ms.milestone_id ms_id
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
    ms_left = ms_cur.fetchall()
    ms_left_l = [row[0] for row in ms_left]
#####################################################
    form = TechAnalyticsForm()
    form.milestone.choices = milestones_tuplist

    if request.method == 'POST':
        # form process

        # dynamic selection
        # form.milestone.choices = [('None', 'None')] + [(str(row[0]), str(row[0])) for row in ms_left]


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
                                (contributor, tech_name, contribute_time, story_year, story_date, story_content, milestone, sources)
                              values (?, ?, ?, ?, ?, ?, ?, ?)''', [user['user_id'], tech, datetime.timestamp(datetime.now()), form.story_year.data, form.story_date.data, form.story_content.data, form.milestone.data,  form.sources.data])

                # we might need some cleaner functions here
                db.commit()
                flash(f'New story added', 'success')
                return redirect(url_for('tech_analytics',tech=tech))

    return render_template('tech_analytics.html', title='Technology Analytics', form=form, user= user,  milestones = milestones[:-1], ms_left = ms_left_l, stories = stories_results, tech=tech)

@app.route("/task_board_e", methods = ['GET', 'POST'])
def task_board_e():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_edit'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    # get all tech outcomes and their status
    ## NOTE: Here we query the tech_main_log table #######
    db = get_db()
    ## sqlite3 specific datetime function!!
    task_cur = db.execute('''
                            select
                                tml.log_id log_id,
                                tml.tech_name tech_name,
                                tml.scout_count scout_count,
                                tml.latest_scout,
                                tml.change_committed change_committed,
                                tsl.story_count story_count,
                                tsl.latest_commit latest_commit
                            from
                                (select distinct tech_name, max(log_id) log_id, count(*) scout_count, max(change_committed) change_committed,
                                max(datetime(scout_time,'unixepoch')) latest_scout
                                 from tech_main_log
                                 group by tech_name) tml left join
                                (select distinct tech_name, count(*) story_count, max(datetime(contribute_time,'unixepoch')) latest_commit
                                 from tech_story_log
                                 group by tech_name) tsl

                                on tml.tech_name = tsl.tech_name

                            order by lower(tml.tech_name) asc
                         ''')

    task_result = task_cur.fetchall()

    return render_template('task_board_e.html', title='Task Board', user= user, tasks = task_result)



@app.route("/view_log/<log_s_id>", methods = ['GET', 'POST'])
@app.route("/view_log/<log_s_id>/<mode>", methods = ['GET', 'POST'])
def view_log(log_s_id, mode = 'analytics'):
    """
    For all users, see a form submitted by him/herself or other users. Users can only edit his/her own form and rewrite the corresponding entry in log table.
    """
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_analyse'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    db = get_db()
    story_cur = db.execute('''
                            select *, datetime(contribute_time,'unixepoch') contribute_time_dt
                            from tech_story_log tsl join users
                            on contributor = user_id
                            where log_s_id = ?
                            ''', [log_s_id])
    story = story_cur.fetchone()

    return render_template('view_log.html', title='View Tech Story', user = user, story = story, mode=mode)

@app.route("/edit_log/<log_s_id>", methods = ['GET', 'POST'])
def edit_log(log_s_id):
    """
    For all users, see a form submitted by him/herself or other users. Users can only edit his/her own form and rewrite the corresponding entry in log table.
    """
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_analyse'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    # get the log that will be edited
    db = get_db()
    story_cur = db.execute('''
                            select *, datetime(contribute_time,'unixepoch') contribute_time_dt
                            from tech_story_log tsl join users
                            on contributor = user_id
                            where log_s_id = ?
                            ''', [log_s_id])
    story = story_cur.fetchone()

    tech = story['tech_name']

    form = EditTechStoryForm()
    form.milestone.choices = milestones_tuplist

    if request.method == 'POST':
        if form.validate_on_submit():
            if repeat_story_checker(form):
                flash(f'Edit field: please do not submit repeated content', 'danger')
            else:
                # commit changes
                db.execute('''update tech_story_log
                              set contributor = ?, contribute_time = ?, story_year = ?, story_date = ?, story_content = ?, milestone = ?, sources = ?
                              where log_s_id = ?''', (user['user_id'], datetime.timestamp(datetime.now()), form.story_year.data, form.story_date.data, form.story_content.data, form.milestone.data,  form.sources.data, log_s_id))

                # we might need some cleaner functions here
                db.commit()
                flash(f'Tech Story Updated', 'success')
                return redirect(url_for('tech_analytics',tech=tech))


    return render_template('edit_log.html', title='View Tech Story', form = form, user = user, story = story)

@app.route("/view_scout/<log_id>", methods = ['GET', 'POST'])
@app.route("/view_scout/<log_id>/<mode>", methods = ['GET', 'POST'])
def view_scout(log_id, mode = 'analytics' ):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    scout_cur = db.execute('''
                            select *, datetime(scout_time,'unixepoch') scout_time_dt
                            from tech_main_log join users
                            on contributor = user_id
                            where log_id = ?
                            ''', [log_id])
    scout = scout_cur.fetchone()

    b = tuple(map(int, scout['impa_sector'].split(';'))) if len(scout['impa_sector']) >1 else '('+str(scout['impa_sector']) + ')'

    sectors_sql = 'select sector from impacted_sector_order where sec_id in ' + str(b)

    sectors_cur = db.execute(sectors_sql)
    sectors = sectors_cur.fetchall()

    return render_template('view_scout.html', title='View Tech Scout', user = user, scout = scout, sectors = sectors, mode = mode)

###### Merge this function/route with the previous one in the future ############
@app.route("/edit_scout/<log_id>", methods = ['GET', 'POST'])
def edit_scout(log_id):

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_edit'] == 0:
        flash('No access to TechAnalytics. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    ##### get the scout that will be edited ######################################
    db = get_db()
    scout_cur = db.execute('''
                            select *, datetime(scout_time,'unixepoch') scout_time_dt
                            from tech_main_log join users
                            on contributor = user_id
                            where log_id = ?
                            ''', [log_id])
    scout = scout_cur.fetchone()
    b = tuple(map(int, scout['impa_sector'].split(';'))) if len(scout['impa_sector']) >1 else '('+str(scout['impa_sector']) + ')'

    sectors_sql = 'select sector from impacted_sector_order where sec_id in ' + str(b)

    sectors_cur = db.execute(sectors_sql)
    current_sectors = sectors_cur.fetchall()

    sectors_cur = db.execute('select sec_id, sector from impacted_sector_order')
    all_sectors = sectors_cur.fetchall()

    ##########################################################################
    form = TechScoutForm()

    if request.method == 'POST':
        trigger = True
        checkbox = request.form.getlist('mycheckbox')

        if len(checkbox) ==0:
            trigger = False #

        if form.validate_on_submit():

            if repeat_scout_checker(form, mode = 'full_check'):
                flash(f'Edit field: please do not submit repeated content', 'danger')
            else:
                # commit changes
                db.execute('''
                            update tech_main_log
                            set contributor = ?, tech_name = ?, scout_time = ?, description = ?, impact = ?, desc_source = ?, asso_names = ?, impa_sector = ?, emb_techs = ?, wiki_link = ?, category = ?
                            where log_id = ?

                            ''', (user['user_id'], form.tech_name.data, datetime.timestamp(datetime.now()), form.description.data, form.impact.data, form.sources.data, form.associate_names.data, ';'.join(checkbox), form.embed_tech.data, form.wikilink.data, form.category.data, log_id))

                # we might need some cleaner functions here
                db.commit()
                flash(f'Tech Scout Updated', 'success')
                return redirect(url_for('view_scout',log_id=log_id))
        else:
            flash(form.errors if len(form.errors)!= 0 else 'Select Impact Sectors', 'danger')

    return render_template('edit_scout.html', title='Edit Tech Scout', form = form, user = user, scout = scout, sectors = all_sectors, selected_sec = current_sectors )
#################################################################################

@app.route("/commit_scout/<log_id>", methods = ['GET', 'POST'])
def commit_scout(log_id):
    """
    For editor users, commit a tech story to main table.
    """
    user = get_current_user()
    db = get_db()
    if not user:
        return redirect(url_for('login'))
    if user['can_edit'] == 0:
        flash('No access. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    log_cur = db.execute('select * from tech_main_log where log_id = ?',[log_id])
    log = log_cur.fetchone()

    is_use = 1 if log['category'] == 'use' else 0
    is_prod = 1 if log['category']  == 'product' else 0
    is_proc = 1 if log['category']  == 'process' else 0

    ########### commit changes to main tables ######################
    tech_main_cur = db.execute('select * from tech_main where name = ?',[log['tech_name']])
    tech_main_result = tech_main_cur.fetchone()

    if tech_main_result:
        db.execute('''
                    update tech_main
                    set name = ?,
                        description = ?,
                        impact = ?,
                        impa_sector = ?,
                        is_use = ?,
                        is_prod = ?,
                        is_proc = ?
                   ''',[log['tech_name'], log['description'], log['impact'], log['impa_sector'], is_use, is_prod, is_proc])
        db.commit()

        ########### commit to other related tables #####################
        # embedded techs
        db.execute('''
                    update tech_embed
                    set embed_li = ?
                    where id = ?
                    ''', [log['emb_techs'], tech_main_result['id']])
        db.commit()



    else: # if this is a new tech
        db.execute('''
                    insert into tech_main
                        (name, description, impact, impa_sector, is_use, is_prod, is_proc)
                    values
                        (?, ?, ?, ?, ?, ?, ?)
                    ''', [log['tech_name'], log['description'], log['impact'], log['impa_sector'], is_use, is_prod, is_proc])
        db.commit()

        tech_main_cur = db.execute('select * from tech_main where name = ?',[log['tech_name']])
        tech_main_result = tech_main_cur.fetchone()

        ########### commit to other related tables #####################
        # embedded techs
        db.execute('''
                    insert into tech_embed
                        (id, embed_li)
                    values
                        (?, ?)
                    ''', [tech_main_result['id'], log['emb_techs']])
        db.commit()

    # associated names to the lookup table
    for name in list(map(lambda x:x.strip(), log['asso_names'].split(';'))):
        db.execute('''
                    insert into tech_lookup
                        (tech_main_id, tech_lookup_name)
                    values
                        (?, ?)
                    ''', [tech_main_result['id'], name])
        db.commit()

    ########### change the commit status #############################
    db.execute('''
                update tech_main_log
                set change_committed = ?
                where log_id = ?
               ''', [datetime.timestamp(datetime.now()), log_id])

    db.commit()


    flash('Congrats! New technology scout committed to the main database.', 'success')
    return redirect(url_for('home'))



@app.route("/view_all_stories/<tech>", methods = ['GET', 'POST'])
def view_all_stories(tech):
    db = get_db()
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['can_edit'] == 0:
        flash('No access. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    stories_cur = db.execute('''
                            select
                                tsl.log_s_id log_s_id,
                                tsl.tech_name,
                                tsl.milestone,
                                substr(tsl.story_content, 1, 100)|| '...' story_content, tsl.story_year,
                                tsl.contributor contributor_id,
                                tsl.change_committed,
                                u.username contributor_name, datetime(tsl.contribute_time,'unixepoch') contribute_time
                            from tech_story_log tsl, users u, milestones m
                            where tsl.tech_name = ?
                            and tsl.contributor = u.user_id
                            and tsl.milestone = m.ms_name
                            order by tsl.story_year asc, m.milestone_id

                            ''', [tech])
    stories_results = stories_cur.fetchall()

    return render_template('view_all_stories.html', title='View Progress',  user = user, stories = stories_results, tech=tech)



@app.route("/commit_story/<log_s_id>", methods = ['GET', 'POST'])
def commit_story(log_s_id):
    """
    For editor users, commit a tech story to main table.
    """
    user = get_current_user()
    db = get_db()
    if not user:
        return redirect(url_for('login'))
    if user['can_edit'] == 0:
        flash('No access. Please contact administrators', 'danger')
        return redirect(url_for('home'))

    # get log info
    log_cur = db.execute('select distinct * from tech_story_log where log_s_id = ?',[log_s_id])
    log = log_cur.fetchone()

    # check if tech exists
    tech_cur = db.execute('''
                            select * from tech_main
                            where name = ?
                          ''',[log['tech_name']] )
    tech = tech_cur.fetchone()

    if not tech: # if the tech does not exist, commit the tech first
        flash('Action not allowed. Please commit the technology scout firstly', 'danger')
        return redirect(url_for('task_board_e'))

    tech_id = tech['id']

    # check if the milestone exists
    story_cur = db.execute('''
                              select * from tech_story
                              where name = ?
                              and story_content = ?
                              and milestone = ?
                              and story_year = ?
                           ''', [log['tech_name'], log['story_content'] ,  log['milestone'], log['story_year']])
    existing_story = story_cur.fetchone()

    if existing_story:
        flash('The same story already exists', 'danger')
        return redirect(url_for('view_log'))



    ########### prepare the variables #############################
    if log['story_date']:
        story_time = datetime.timestamp((datetime.strptime(str(log['story_year']) + '/' + log['story_date'], '%Y/%m/%d')))
        exact_time = 1
    else:
        story_time = random_date(log['story_year'])
        exact_time = 0

    db.execute('''
                  insert into tech_story
                    (id, name, story_time, story_content, milestone, exact_time, source_check, sources, story_year)
                  values
                    (?,?,?,?,?,?,?,?,?)
               ''',[ tech_id, log['tech_name'], story_time, log['story_content'], log['milestone'], exact_time, 1, log['sources'], log['story_year'] ] )
    db.commit()

    ########### commit to other related tables #####################
    # if there are any


    ########### change the commit status ###########################
    db.execute('''
                update tech_story_log
                set change_committed = ?
                where log_s_id = ?
               ''', [datetime.timestamp(datetime.now()), log_s_id])

    db.commit()


    flash('Congrats! New technology story committed to the main database.', 'success')

    return redirect(url_for('task_board_e'))



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
# ps -fA | grep python
