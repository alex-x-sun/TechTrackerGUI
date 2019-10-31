from flask import Flask, render_template, url_for, flash, redirect, request, g, session, request
from forms import RegistrationForm, LoginForm, TechScoutForm, TechAnalyticsForm, EditTechStoryForm
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField,SelectField
from wtforms import validators, ValidationError
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from werkzeug.security import generate_password_hash, check_password_hash

import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
# You might need to check this:
# https://indradhanush.github.io/blog/dealing-with-datetime-objects-in-python/
default_tz = pytz.timezone('US/Eastern')

# for sqlite3 database test
# import sqlite3
from dbTest import connect_db,  get_db
from random import randrange
# if use Hydrogen or Jupyter
# ipython3 kernelspec install-self

# for milestone string process
from milestones import milestones, milestones_tuplist

# for helper functions
from helper_functions import get_current_user, random_date, repeat_checker, repeat_scout_checker, repeat_story_checker

###############################################################################
app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'




@app.teardown_appcontext
# def close_db(error):
#     if hasattr(g, 'sqlite_db'):
#         g.sqlite_db.close()

def close_db(error):
    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()
    if hasattr(g, 'postgres_db_cunn'):
        g.postgres_db_conn.close()

@app.route("/")
@app.route("/home")
def home():
    user = get_current_user()
    return render_template('home.html',  user = user)


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

            db.execute('select user_id from users where email = %s or username = %s', (user_email, username))
            existing_user = db.fetchone()

            if existing_user:
                flash('User email already exist', 'danger')

            else:
                db.execute('insert into users (username, email, password) values (%s, %s, %s)', (username, user_email, hashed_password))

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

            db.execute('select user_id, email, password, can_scout, can_analyse, can_edit, admin from users where email = %s',(user_email, ))
            user_result = db.fetchone()

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
    db.execute('select sec_id, sector from impacted_sector_order')
    sectors_results = db.fetchall()

    form = TechScoutForm()

    tech_name = None

    if request.method == 'POST':
        trigger = True
        checkbox = request.form.getlist('mycheckbox')

        if len(checkbox) ==0:
            trigger = False #%s


        if form.validate_on_submit() and trigger:

            if repeat_scout_checker(form):
                flash(f'Scout field: The Technology {form.tech_name.data} already exists. Please check.', 'danger')
            else:
                db.execute('''
                            insert into tech_main_log
                                (contributor, tech_name, scout_time, description, impact, desc_source, asso_names, impa_sector, emb_techs, wiki_link, category)
                            values
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ''', (user['user_id'], form.tech_name.data, datetime.now(default_tz), form.description.data, form.impact.data, form.sources.data, form.associate_names.data, ';'.join(checkbox), form.embed_tech.data, form.wikilink.data, form.category.data))

                # we might need some cleaner functions here

                flash(f'Technology {form.tech_name.data} added', 'success')
                return redirect(url_for('home'))

        else:
            flash(form.errors if len(form.errors)!= 0 else 'Select Impact Sectors', 'danger') #spits out any and all errors**
        # if form.validate_on_submit():
        #     print('yea')
        #     flash(f'Technology {form.tech_name.data} added')
        #     return redirect(url_for('home'))
        # else:



    return render_template('tech_scout.html', title='Technology Scout', user= user, form=form, sectors = sectors_results, tech_name=tech_name)


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
    db.execute('''select
                    log_id,
                    tech_name,
                    to_char(tml.scout_time, 'YYYY-MM-DD HH24:MI') scout_time,
                    username contributor_name
                from (tech_main_log tml join users u on tml.contributor = u.user_id)
                where tech_name in
                    (select distinct tech_name from tech_main_log)

                order by lower(tech_name) asc''')

    task_result = db.fetchall()

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
    db.execute('''
                            select
                                log_s_id,
                                milestone,
                                substr(story_content, 1, 100)|| '...' story_content,
                                story_year,
                                contributor contributor_id,
                                username contributor_name,
                                to_char(contribute_time, 'YYYY-MM-DD HH24:MI') contribute_time
                            from tech_story_log inner join milestones on milestone = ms_name
                                inner join users on contributor = user_id

                            where tech_name = %s

                            order by story_year, milestone_id asc

                            ''', (tech,))
    stories_results = db.fetchall()


    db.execute('''
                            select ms_left.ms_name ms_name, ms.milestone_id ms_id
                            from milestones ms,
                                 (select distinct m.ms_name
                                  from milestones m

                                  except

                                  select distinct milestone ms
                                  from tech_story_log
                                  where tech_name = %s) ms_left
                            where ms_left.ms_name = ms.ms_name
                            order by ms.milestone_id

                           ''', (tech,))
    ms_left = db.fetchall()
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
            db.execute('''
                                        select log_s_id
                                        from tech_story_log
                                        where story_content = %s
                                        and contributor = %s
                                        ''', (form.story_content.data, user['user_id']))
            existing_ms = db.fetchone()

            if existing_ms:
                flash('You have already submitted this story', 'danger')
            else:
                # commit changes
                db.execute('''insert into tech_story_log
                                (contributor, tech_name, contribute_time, story_year, story_date, story_content, milestone, sources)
                              values (%s, %s, %s, %s, %s, %s, %s, %s)''', (user['user_id'], tech, datetime.now(default_tz), form.story_year.data, form.story_date.data, form.story_content.data, form.milestone.data,  form.sources.data))

                # we might need some cleaner functions here
                flash(f'New story added', 'success')
                return redirect(url_for('tech_analytics',tech=tech))

    return render_template('tech_analytics.html', title='Technology Analytics', form=form, user= user,  milestones = milestones[1:], ms_left = ms_left_l, stories = stories_results, tech=tech)

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
    db.execute('''
                            select
                                tml.log_id log_id,
                                tml.tech_name tech_name,
                                tml.scout_count scout_count,
                                to_char(tml.latest_scout,'YYYY-MM-DD HH24:MI') latest_scout,
                                tml.change_committed change_committed,
                                tsl.story_count story_count,
                                to_char(tsl.latest_commit,'YYYY-MM-DD HH24:MI') latest_commit
                            from
                                (select distinct tech_name, max(log_id) log_id, count(*) scout_count, max(change_committed) change_committed,
                                max(scout_time) latest_scout
                                 from tech_main_log
                                 group by tech_name) tml left join
                                (select distinct tech_name, count(*) story_count, max(contribute_time) latest_commit
                                 from tech_story_log
                                 group by tech_name) tsl

                                on tml.tech_name = tsl.tech_name

                            order by lower(tml.tech_name) asc
                         ''')

    task_result = db.fetchall()

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
    db.execute('''
                            select *, to_char(contribute_time,'YYYY-MM-DD HH24:MI') contribute_time_dt
                            from tech_story_log tsl join users
                            on contributor = user_id
                            where log_s_id = %s
                            ''', (log_s_id,))
    story = db.fetchone()

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
    db.execute('''
                            select *, to_char(contribute_time,'YYYY-MM-DD HH24:MI') contribute_time_dt
                            from tech_story_log tsl join users
                            on contributor = user_id
                            where log_s_id = %s
                            ''', (log_s_id,))
    story = db.fetchone()

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
                              set contributor = %s, contribute_time = %s, story_year = %s, story_date = %s, story_content = %s, milestone = %s, sources = %s
                              where log_s_id = %s''', (user['user_id'], datetime.now(default_tz), form.story_year.data, form.story_date.data, form.story_content.data, form.milestone.data,  form.sources.data, log_s_id))

                # we might need some cleaner functions here

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
    db.execute('''
                            select *, scout_time scout_time_dt
                            from tech_main_log join users
                            on contributor = user_id
                            where log_id = %s
                            ''', (log_id,))
    scout = db.fetchone()

    b = tuple(map(int, scout['impa_sector'].split(';'))) if len(scout['impa_sector']) >1 else '('+str(scout['impa_sector']) + ')'

    sectors_sql = 'select sector from impacted_sector_order where sec_id in ' + str(b)

    db.execute(sectors_sql)
    sectors = db.fetchall()

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
    db.execute('''
                            select *, scout_time scout_time_dt
                            from tech_main_log join users
                            on contributor = user_id
                            where log_id = %s
                            ''', (log_id,))
    scout = db.fetchone()
    b = tuple(map(int, scout['impa_sector'].split(';'))) if len(scout['impa_sector']) >1 else '('+str(scout['impa_sector']) + ')'

    sectors_sql = 'select sector from impacted_sector_order where sec_id in ' + str(b)

    db.execute(sectors_sql)
    current_sectors = db.fetchall()

    db.execute('select sec_id, sector from impacted_sector_order')
    all_sectors = db.fetchall()

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
                            set contributor = %s, tech_name = %s, scout_time = %s, description = %s, impact = %s, desc_source = %s, asso_names = %s, impa_sector = %s, emb_techs = %s, wiki_link = %s, category = %s
                            where log_id = %s

                            ''', (user['user_id'], form.tech_name.data, datetime.now(default_tz), form.description.data, form.impact.data, form.sources.data, form.associate_names.data, ';'.join(checkbox), form.embed_tech.data, form.wikilink.data, form.category.data, log_id))

                # we might need some cleaner functions here

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

    db.execute('select * from tech_main_log where log_id = %s',[log_id])
    log = db.fetchone()

    is_use = True if log['category'] == 'use' else False
    is_prod = True if log['category']  == 'product' else False
    is_proc = True if log['category']  == 'process' else False

    ########### commit changes to main tables ######################
    db.execute('select * from tech_main where name = %s',[log['tech_name']])
    tech_main_result = db.fetchone()

    if tech_main_result:
        db.execute('''
                    update tech_main
                    set name = %s,
                        description = %s,
                        impact = %s,
                        impa_sector = %s,
                        is_use = %s,
                        is_prod = %s,
                        is_proc = %s
                   ''',(log['tech_name'], log['description'], log['impact'], log['impa_sector'], is_use, is_prod, is_proc))


        ########### commit to other related tables #####################
        # embedded techs
        db.execute('''
                    update tech_embed
                    set embed_li = %s
                    where id = %s
                    ''', (log['emb_techs'], tech_main_result['id']))


    else: # if this is a new tech
        db.execute('''
                    insert into tech_main
                        (name, description, impact, impa_sector, is_use, is_prod, is_proc)
                    values
                        (%s, %s, %s, %s, %s, %s, %s)
                    ''', (log['tech_name'], log['description'], log['impact'], log['impa_sector'], is_use, is_prod, is_proc))


        db.execute('select * from tech_main where name = %s',[log['tech_name']])
        tech_main_result = db.fetchone()

        ########### commit to other related tables #####################
        # embedded techs
        db.execute('''
                    insert into tech_embed
                        (id, embed_li)
                    values
                        (%s, %s)
                    ''', (tech_main_result['id'], log['emb_techs']))


    # associated names to the lookup table
    for name in list(map(lambda x:x.strip(), log['asso_names'].split(';'))):
        db.execute('''
                    insert into tech_lookup
                        (tech_main_id, tech_lookup_name)
                    values
                        (%s, %s)
                    ''', (tech_main_result['id'], name))


    ########### change the commit status #############################
    db.execute('''
                update tech_main_log
                set change_committed = %s
                where log_id = %s
               ''', (datetime.now(default_tz), log_id))




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

    db.execute('''
                            select
                                tsl.log_s_id log_s_id,
                                tsl.tech_name,
                                tsl.milestone,
                                substr(tsl.story_content, 1, 100)|| '...' story_content, tsl.story_year,
                                tsl.contributor contributor_id,
                                tsl.change_committed,
                                u.username contributor_name, tsl.contribute_time contribute_time
                            from tech_story_log tsl, users u, milestones m
                            where tsl.tech_name = %s
                            and tsl.contributor = u.user_id
                            and tsl.milestone = m.ms_name
                            order by tsl.story_year asc, m.milestone_id

                            ''', (tech,))
    stories_results = db.fetchall()

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
    db.execute('select distinct * from tech_story_log where log_s_id = %s',(log_s_id,))
    log = db.fetchone()

    # check if tech exists
    db.execute('''
                            select * from tech_main
                            where name = %s
                          ''',(log['tech_name'],) )
    tech = db.fetchone()

    if not tech: # if the tech does not exist, commit the tech first
        flash('Action not allowed. Please commit the technology scout firstly', 'danger')
        return redirect(url_for('task_board_e'))

    tech_id = tech['id']

    # check if the milestone exists
    db.execute('''
                              select * from tech_story
                              where name = %s
                              and story_content = %s
                              and milestone = %s
                              and story_year = %s
                           ''', (log['tech_name'], log['story_content'] ,  log['milestone'], log['story_year']))
    existing_story = db.fetchone()

    if existing_story:
        flash('The same story already exists', 'danger')
        return redirect(url_for('view_log', log_s_id = log['log_s_id'] ))



    ########### prepare the variables #############################
    if log['story_date']:
        story_time = datetime.strptime(str(log['story_year']) + '/' + log['story_date'], '%Y/%m/%d')
        exact_time = 1
    else:
        story_time = random_date(log['story_year'])
        exact_time = 0

    db.execute('''
                  insert into tech_story
                    (id, name, story_time, story_content, milestone, exact_time, source_check, sources, story_year)
                  values
                    (%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ''',(tech_id, log['tech_name'], story_time, log['story_content'], log['milestone'], exact_time, 1, log['sources'], log['story_year'] ) )

    ########### commit to other related tables #####################
    # if there are any


    ########### change the commit status ###########################
    db.execute('''
                update tech_story_log
                set change_committed = %s
                where log_s_id = %s
               ''', (datetime.now(default_tz), log_s_id))

    flash('Congrats! New technology story committed to the main database.', 'success')

    return redirect(url_for('view_all_stories', tech=log['tech_name']))



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
    db.execute('select user_id, username, email, can_scout, can_analyse, can_edit, admin from users')
    users_results = db.fetchall()

    return render_template('admin.html', user=user, users=users_results)

if __name__ == '__main__':
    app.run(debug=True)
# ps -fA | grep python
