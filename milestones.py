import pandas as pd
import sqlite3
import os



milestones_0 = ['inception',\
 'conceptual_design',\
 'prototype',\
 'academic_thesis',\
 'published_paper',\
 'book_mention',\
 'university_lab',\
 'private_r&d',\
 'patent_filed',\
 'patent_issued',\
 'first_commercial_product',\
 'competing_products_enter_the_market',\
 'first_commercial_product_failure',\
 'incorporated_into_other_technologies',\
 'national_standards_body',\
 'regulatory_requirements',\
 'word_in_the_dictionary']

def text_pretty(varchar):
    return varchar.replace('_', ' ').title()

def ToMachineReadable(char):
    """
    Change a string into standard format
    """
    return char.lower().strip().replace(' ', '_')

milestones = list(map(text_pretty, milestones_0))


df_milestones = pd.DataFrame(milestones)
df_milestones['milestone_id'] = df_milestones.index
df_milestones['milestone_name'] = df_milestones.iloc[:,0].apply(lambda x: text_pretty(x))

df_milestones.columns = ['ma_std_name', 'milestone_id','ms_name']



dbpath = os.getcwd() + '/TechTrackerTemp.db'
sql = sqlite3.connect(dbpath)

df_milestones.to_sql(name = 'milestones', con = sql)
