#!/usr/bin/env python
# coding: utf-8

# # Creating the previous lists to compare too

# In[18]:

import numpy as np
import pandas as pd

#Interacting with Postgres SQL
import psycopg2

#importing database and creds
from database_config import postgres as cfg

#Get the previous date
from datetime import date, timedelta, datetime

import time


# In[277]:


print('Change Report has begun')


# In[21]:


todays_date = str(datetime.today())[:10]
week_of = str(datetime.today() - timedelta(7))[:10]


# In[22]:


#Setting up the connection to the PostgreSQL -feeddate
conn = psycopg2.connect(**cfg)


# In[279]:


taxnomy_Gdrive = 'G:/Team Drives/GroupBy Public/Client Services/Enrich Services/Taxonomy/Change Report/'


# In[23]:


table_list = ['attributes','buckets','values']


# ## Pulling in current data from SQL server

# In[24]:


def current_list(table_name):
    #query the specific tables
    query = (
    """SELECT
        id,
        name
    FROM {}""")

    df = pd.read_sql(query.format(table_name,table_name,table_name),conn)
    return df


# In[280]:


def file_changes(file):
    """

    ----------------------------------------------------
    Parameters:
    ----------------------------------------------------
    file: this is the table you would like to check
    to see if there were any new values
    {example} file_changes('attriubtes')



    """
    #previous files used
    file1 = taxnomy_Gdrive+'Previous files - Rolling Weekly Window/previous_'+file+'.csv'
    #current files from the function above.
    file2 = current_list(file)

    #this acts aas a filter below to filter out duplicate names.
    cols_to_show = ['name']

    old = pd.read_csv(file1)
    new = file2

    #labeling the files
    old['version'] = 'old'
    new['version'] = 'new'

    #combining the data into 1 full dataset for comparision.
    full_set = pd.concat([old, new], ignore_index=True,sort=True)
    full_set = full_set[['id','name','version']]

    changes = full_set.drop_duplicates(subset=cols_to_show, keep='last')

    dup_index =changes.set_index('id').index
    dupe_names = dup_index[dup_index.duplicated()].unique()
    dupes = changes[changes['id'].isin(dupe_names)]

    #adding version control to the dataset to help determine old and new
    change_new = dupes.loc[(dupes['version'] == 'new')]
    change_old = dupes.loc[(dupes['version'] == 'old')]
    change_new = change_new.drop(['version'], axis=1)
    change_old = change_old.drop(['version'], axis=1)
    #Set index for each of the values to compare data when combining.
    change_new.set_index('id', inplace=True)
    change_old.set_index('id', inplace=True)

    #combining the old and new dataset together.
    panel = change_old.join(change_new,on=change_old.index,how='outer',lsuffix='_old',rsuffix='_new')

    panel.drop(columns='key_0',inplace=True)

    for row in range(panel.shape[0]):
        if panel.iloc[row][1] == panel.iloc[row][0]:
            panel.iloc[row][0]
        else:
            panel.iloc[row][0] = '{0} ----> {1}'.format(panel.iloc[row][0],panel.iloc[row][1])

    panel.rename(columns={'name_old':'name','name_new':'type'}, inplace=True)
    panel['type'] = 'change'
    diff_output = panel

    changes['duplicate'] = changes['id'].isin(dupe_names)

    removed_names = changes.loc[(changes['duplicate'] == False) & (changes['version'] == 'old')]
    removed_names.set_index('id', inplace=True)
    removed_names['type'] = 'removed'

    new_name_set = full_set.drop_duplicates(subset=cols_to_show)
    new_name_set['duplicate'] = new_name_set['id'].isin(dupe_names)

    added_names = new_name_set.loc[(new_name_set['duplicate'] == False) & (new_name_set['version'] == 'new')]
    added_names.set_index('id', inplace=True)
    added_names['type'] = 'added'

    df = pd.concat([diff_output, removed_names, added_names],sort=False)
    df['check_date'] =  todays_date
    exec(('df["table"] = {!r}').format(file))

    return df[['name','type','table','check_date']]


# In[281]:


full_data = pd.DataFrame()
for table in table_list:
    try:
        temp = file_changes(table)
        print(temp.shape[0])
        full_data = full_data.append(temp)
    except:
        print('no new data in '+table)
        pass

if full_data.shape[0] > 0:
    with open(taxnomy_Gdrive+"Change_Report.txt",'r+',encoding='utf-8') as f:
        previous_contents = f.read()
        f.seek(0,0)
        f.write(todays_date+" Changes have occured. Please see the report for more information.\n")
        f.write(previous_contents)

else:
    with open(taxnomy_Gdrive+"Change_Report.txt",'r+',encoding='utf-8') as f:
        previous_contents =f.read()
        f.seek(0,0)
        f.write(todays_date+' No changes have occured within the past week.\n')
        f.write(previous_contents)

full_data.to_csv(taxnomy_Gdrive+'Weekly_Bucket+Attribute+Value_changes.csv',mode='a+',header=False)


# # Runs Previous list immediately after Changes have been recorded.

# In[283]:

def previous_list(table_name):
    #query the specific tables
    query = (
    """SELECT
        id,
        name
    FROM {}""")


    df = pd.read_sql(query.format(table_name,table_name,table_name),conn)

    #concat the name and id to ensure that both values are unique in case any change.
    df['unique_name_list'] = df['name']+"|"+df['id'].astype('str')
    #saving the files as a csv
    path = taxnomy_Gdrive+'Previous files - Rolling Weekly Window/previous_{}.csv'
    df.to_csv(path.format(table_name),index=False)
    return print("completed for", table_name)


# In[284]:


for table in table_list:
    previous_list(table)


# In[285]:

print('report has been completed')
time.sleep(3)


# In[ ]:
