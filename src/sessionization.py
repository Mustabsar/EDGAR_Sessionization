# coding: utf-8
"""
Created on Thu Apr  5 22:32:49 2018

@author: Subhadip Chowdhury

@sample-usage: see run.sh

@description: This Python script reads [commandline_input_1] as logfile and [commansline_input_2] as inactivity_period
and writes sessionization data into [commandline_input_3] in required format

@required libraries: sys, numpy and dask
"""
import sys
import numpy as np
import dask.dataframe as dd

#read the logfile
logfile= sys.argv[1]

#read the inactivity period text file and store the data as an integer
inactivity_period = int(open(sys.argv[2]).read())

#initialize the output file
output_text = sys.argv[3]

#read the log.csv file and store it in a Dask dataframe
sessiondata = dd.read_csv(logfile, 
                          usecols=['ip','date','time'], # can also include ['cik','accession','extention'] if we want, but these are not needed. The reasoning is explained ,   
                          dtype={'ip':str}, # include these if needed ['cik':str,'accession':str,'extension':str},
                          na_filter=False, #assuming no missing data to make parsing faster
                          parse_dates = {'timestamp' : ['date','time']}, #Combining the 'date' and 'time' column to a 'timestamp' column
                          infer_datetime_format=True,
                          error_bad_lines=False, warn_bad_lines=True #“bad lines”, e.g. extra commas in csv file, will be dropped from the DataFrame and A Warning will be given
                         )

#Dropping the document id columns
"""
Since the same document accessed more than once at the same time timestamp counts as multiple 
requests, we don't need to actually keep track of these columns for the purpose of current problem.
So we can just drop these columns altogether.  In fact, there was no need to read these into the
dataframe at all. We only included them since the problem statement says to pay attention to these fields.
"""
# sessiondata = sessiondata.drop(['cik','accession','extention'],axis=1)

#Make an 'entry_order' column. This is required since we need to output the sorted data in a particular order that depends on the entry order in the input
sessiondata['entry_order']=sessiondata.index

#Make a EOF timestamp to end all sessions
max_timestamp = sessiondata['timestamp'].max()

"""
The following part of the script is the main code to identify distinct session. 
The essential algorithm is as follows: We identify when an user has been idle for more than the inactivity period 
by checking the difference between consequtive requests. Each time this condition is met, a new session is started.
The 'session_id' column keeps track of the current session.
"""
sessiondata=sessiondata.groupby('ip').apply(lambda df: df.assign(idle_time=df.timestamp.diff(1))).reset_index(drop=True) #Calculating the difference between consequtive timestamps

sessiondata['start_new_session']=sessiondata['idle_time'].apply(lambda x: int(x/np.timedelta64(1,'s')> inactivity_period), meta = ('start_new_session', 'int'))
sessiondata['session_id'] = sessiondata.groupby('ip')['start_new_session'].cumsum() + 1

#We do not need the intermediate columns any more. So we can optionally drop them to make our memory usage lighter.
sessiondata=sessiondata.drop(['start_new_session', 'idle_time'], axis=1)

"""
Once the sessions have been identified, it is easy to figure out the start and end
of each session. Also we can count the total number of requests in each session.
"""

#Define a function that is applied to GroupBy objects, obtained by grouping sessiondata according to 'ip' and 'session_id'
def assign_start_end_count(df):
    
    df['total_no_of_request'] = df['timestamp'].count() #per session
    
    df['start_session'] = df['timestamp'].min()
    
    df['actual_end_session'] = df['timestamp'].max()
    
    #Another column to keep track of those session that were forcefully ended when EOF was reached
    actual_end_timestamp = df['timestamp'].max()
    if actual_end_timestamp < (max_timestamp.compute()-np.timedelta64(inactivity_period,'s')):
        df['EOF_end_session'] = actual_end_timestamp
    else:
        df['EOF_end_session'] = max_timestamp.compute()
    
    return df
        
sessiondata=sessiondata.groupby(['ip','session_id']).apply(assign_start_end_count)

"""
Finally we sort the data properly in required order and write it in a output file.

First sort by Session end timestamp, including if it was due to EOF.
Second, sort by the session start timestamp.
Third, sort by the order the entries appear in input file
"""

output_data = sessiondata.compute()

output_data = output_data.sort_values(by=['EOF_end_session','start_session','entry_order'])

#Collapsing all document requests per ip and per session to a single entry with the total count
output_data = output_data.drop_duplicates(subset=['ip','session_id'])

#Calculating the session length = (end-start+1), since it is counted as range inclusive
output_data['session_length']=((output_data['actual_end_session']-output_data['start_session'])/np.timedelta64(1,'s')).astype('int') + 1 #Changing datatype from timedelta to float to int


#Output the columns in the required format to output file
output_data.to_csv(output_text, columns=['ip','start_session','actual_end_session', 'session_length', 'total_no_of_request'],header=False, index=False)    
    

