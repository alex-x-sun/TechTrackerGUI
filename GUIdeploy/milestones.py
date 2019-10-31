import pandas as pd
import sqlite3
import os
from sqlalchemy import create_engine


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

milestones_tuplist = [('None', 'None Milestone Story')] + [(text_pretty(ms), text_pretty(ms)) for ms in milestones_0]

milestones_1 = ['none'] + milestones_0
milestones = list(map(text_pretty, milestones_1))

milestones = ['None','Inception',\
 'Conceptual Design',\
 'Prototype',\
 'Academic Thesis',\
 'Published Paper',\
 'Book Mention',\
 'University Lab',\
 'Private R&D',\
 'Patent Filed',\
 'Patent Issued',\
 'First Commercial Product',\
 'Competing Products Enter The Market',\
 'First Commercial Product Failure',\
 'Incorporated Into Other Technologies',\
 'National Standards Body',\
 'Regulatory Requirements',\
 'Word In The Dictionary']
df_milestones = pd.DataFrame(milestones_1)
df_milestones['milestone_id'] = df_milestones.index
df_milestones['milestone_name'] = df_milestones.iloc[:,0].apply(lambda x: text_pretty(x))
#
df_milestones.columns = ['ma_std_name', 'milestone_id','ms_name']
#


df_milestones

impacted_sector_order = ['Land Selection','Design','Entitlement','Capital Stack','Construction','Leasing & Brokerage','Asset Monitoring & Operations','Acquisition & Disposition','Demolition','Redevelopment']


# df_impa = pd.DataFrame(impacted_sector_order)
# df_impa.columns = ['sector']
# df_impa['sec_id'] = df_impa.index

# df_impa
#################### Write it into postgres database ############################

# from sqlalchemy import create_engine
# from dbTest import uri

#
# engine = create_engine(uri)
# df_milestones.to_sql('milestones', engine)
#
# df_impa.to_sql('impacted_sector_order', engine)










#
