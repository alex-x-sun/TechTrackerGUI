from flask import g
import sqlite3
import os

######################### database test with sqlite3 ########################
dbpath = os.getcwd() + '/TechTrackerTemp.db'
# database helper functions
def connect_db(RowMode=True):
    
    sql = sqlite3.connect(dbpath)
    if RowMode:
        sql.row_factory = sqlite3.Row
    else:
        sql.row_factory = lambda cursor, row: row[0]
    return sql

def get_db():
    if not hasattr(g, 'sqlite3_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

##############################################################################
