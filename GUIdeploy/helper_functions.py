from flask import g, session
from datetime import datetime, timedelta
import pytz
import time
from dbTest import connect_db,  get_db
from random import randrange
# You might need to check this:
# https://indradhanush.github.io/blog/dealing-with-datetime-objects-in-python/
default_tz = pytz.timezone('US/Eastern')

############ helper functions #################################################
def get_current_user():
    user_result = None

    if 'user' in session:
        user_email = session['user']

        db = get_db()
        db.execute('select user_id, email, password, can_scout, can_analyse, can_edit, admin from users where email = %s', (user_email, )) # tuple for postgres
        user_result = db.fetchone()

    return user_result

def repeat_scout_checker(form, mode = 'scout_only'):
    db = get_db()

    # check repeat form
    if mode == 'scout_only':
        db.execute('''
                                    select log_id
                                    from tech_main_log
                                    where tech_name = %s
                                    ''', (form.tech_name.data, ))
        existing_sc = db.fetchone()
    elif mode == 'full_check':
        db.execute('''
                                    select log_id
                                    from tech_main_log
                                    where tech_name = %s
                                    and description = %s
                                    and impact = %s

                                    and asso_names = %s
                                    and emb_techs = %s
                                    and category = %s
                                    and desc_source = %s
                                    ''', (form.tech_name.data, form.description.data, form.impact.data, form.associate_names.data, form.embed_tech.data, form.category.data, form.sources.data))
        existing_sc = db.fetchone()

    return existing_sc

def repeat_story_checker(form):
    db = get_db()
    # check repeat form
    db.execute('''
                                select log_s_id
                                from tech_story_log
                                where story_year = %s
                                and story_date = %s
                                and milestone = %s
                                and story_content = %s
                                and sources = %s
                                ''', (form.story_year.data, form.story_date.data, form.milestone.data, form.story_content.data, form.sources.data))
    existing_ms = db.fetchone()
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
    return start + timedelta(seconds=random_second)

# random_date(1996)

#################################################################################
# form = ['A','B','C','D','E']
# sql_where = 'where'
# for field in form[:-1]:
#     sql_where += str(field) + ' = %s and '
#
# sql_where += str(form[-1]) + ' = %s '
# sql_where

def repeat_checker(form, table_name):
    """
    This function requires that the field naming should be consistent in all tables and forms
    """
    db = get_db()
    form_data = [field.data for field in form]
    sql_where = 'where'
    for field in form[:-1]:
        sql_where += str(field.name) + ' = %s and '

    sql_where += str(form[-1].name) + ' = %s '

    db.execute('select * from' + str(table_name) + sql_where, form_data)
    existing = db.fetchone()

    return existing
#################################################################################
