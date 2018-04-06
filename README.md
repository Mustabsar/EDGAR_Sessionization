# EDGAR Sessionization

The Electronic Data Gathering, Analysis and Retrieval (EDGAR) system by the SEC maintains (publicly available) weblogs that collect entries corresponding to document access from different IP addresses at different timestamps. This project is about [sessionizing](https://www.wikiwand.com/en/Session_(web_analytics)) that data to get a summary of individual session durations, idle periods, number of documents requested per session etc.

This was posed as a coding challenge from Insight Data Engineering Team.

## Getting Started

To get a copy of the project up and running on your local machine, simply copy the following code to your command line while you are working in the project directory

```
$ ./run.sh
```

### Prerequisites

The main program is written in Python. As such you will need Python 3.6 installed to run the code. Additionally, the following libraries are needed:

1. NumPy
2. Dask
3. Sys (usually installed by default with Python installation)

The best way to satify all dependencies is to install the Anaconda package from [here](https://anaconda.org/).

Please see below for a short explanation behind these choices.

### Structure of the Repository

To use the program with your own test files, put `log.csv` and `inactivity_period.txt` in the input folder and run the script as above. The output folder will contain the sessionization data in a text file called `sessionization.txt`.

### Description of the input and output file format

+ The `log.csv` file should be in the same format as EDGAR logs found [here](https://www.sec.gov/dera/data/edgar-log-file-data-set.html). You can use a smaller similar dataset as long as it contains a header line with `ip` , `date` (yyyy-mm-dd), and `time` (hh:mm:ss) column.

Note that for the purpose of the challenge, we are treating document requests from the same id at same time as distinct instances even if the document ids are same. As such, we do not really need to keep track of the document id to count total number of requests. It can be inferred directly from the Timestamps.

+ The `inactivity_period.txt` file holds a single integer value denoting the period of inactivity (in seconds) that the program uses to identify a user session. Note that if a session starts at 00:00:02 (first doc request) and ends as 00:00:04 (last doc request), the session length is counted as 3 seconds. If the session is forcefully terminated, due to EOF in the log, the last instance of doc request is taken as session end.

+ The `sessionization.txt` file lists the unique sessions. The fields on each line reads as
  - IP address of the user exactly as found in log.csv
  - date and time of the first webpage request in the session (yyyy-mm-dd hh:mm:ss)
  - date and time of the last webpage request in the session (yyyy-mm-dd hh:mm:ss)
  - duration of the session in seconds
  - count of webpage requests during the session
  
### Running the program

Please note that if the names of the input files are changed, the run.sh file will not work. However it can be manually run by typing following in current working directory.

```
python ./src/sessionization.py ./input/log.csv ./input/inactivity_period.txt ./output/sessionization.txt
```

with the three arguments changed accordingly.

## Description of the Main Algorithm
You will find `sessionization.py` extensively annotated to denote which part of it corresponds to each of the steps below. 

The rough outline of the algorithm is as follows:

+ *Step 1:* Read the csv file into a Dask dataframe and create a `timestamp` column from the `time` and `date` column.
+ *Step 2:* Group the data by `ip` and for each group calculate the difference between consequtive `timestamp` entries. If it is bigger than the `incativity_period`, then mark the start of a new session in `start_new_session` column. 
+ *Step 3:* For each group, mark the distinct sessions by taking cumulative sum of `start_new_session` values. 
+ *Step 4:* Once the sessions are identified, calculate the latest (amx) and earliest (min) timestamp in that session. Their difference gives the `session_length`.
+ *Step 5:* A simple count of the number of timestamps each session gives total number of documents requested.
+ *Step 6:* We follow the guidelines for the required format of the output in the challenge. So we sort the dataframe by session_end, session_start, and the logfile entry order (in that particular order) and output the required columns.


### An Example
+ __input 1:__ `log.csv`

```
ip,date,time,zone,cik,accession,extention,code,size,idx,norefer,noagent,find,crawler,browser
101.81.133.jja,2017-06-30,00:00:00,0.0,1608552.0,0001047469-17-004337,-index.htm,200.0,80251.0,1.0,0.0,0.0,9.0,0.0,
101.81.133.jja,2017-06-30,00:00:00,0.0,1608552.0,0001047469-17-004337,-index.htm,200.0,80251.0,1.0,0.0,0.0,9.0,0.0,
107.23.85.jfd,2017-06-30,00:00:00,0.0,1027281.0,0000898430-02-001167,-index.htm,200.0,2825.0,1.0,0.0,0.0,10.0,0.0,
107.23.85.jfd,2017-06-30,00:00:00,0.0,1136894.0,0000905148-07-003827,-index.htm,200.0,3021.0,1.0,0.0,0.0,10.0,0.0,
101.81.133.jja,2017-06-30,00:00:01,0.0,1608552.0,0001047469-17-004337,-index.htm,200.0,80251.0,1.0,0.0,0.0,9.0,0.0,
107.23.85.jfd,2017-06-30,00:00:01,0.0,841535.0,0000841535-98-000002,-index.html,200.0,2699.0,1.0,0.0,0.0,10.0,0.0,
108.91.91.hbc,2017-06-30,00:00:01,0.0,1295391.0,0001209784-17-000052,.txt,200.0,19884.0,0.0,0.0,0.0,10.0,0.0,
106.120.173.jie,2017-06-30,00:00:02,0.0,1470683.0,0001144204-14-046448,v385454_20fa.htm,301.0,663.0,0.0,0.0,0.0,10.0,0.0,
107.178.195.aag,2017-06-30,00:00:02,0.0,1068124.0,0000350001-15-000854,-xbrl.zip,404.0,784.0,0.0,0.0,0.0,10.0,1.0,
107.23.85.jfd,2017-06-30,00:00:03,0.0,842814.0,0000842814-98-000001,-index.html,200.0,2690.0,1.0,0.0,0.0,10.0,0.0,
107.178.195.aag,2017-06-30,00:00:04,0.0,1068124.0,0000350001-15-000731,-xbrl.zip,404.0,784.0,0.0,0.0,0.0,10.0,1.0,
108.91.91.hbc,2017-06-30,00:00:04,0.0,1618174.0,0001140361-17-026711,.txt,301.0,674.0,0.0,0.0,0.0,10.0,0.0,
107.23.85.jfd,2017-06-30,00:00:05,0.0,842814.0,0000842814-98-000001,-index.html,200.0,2690.0,1.0,0.0,0.0,10.0,0.0,
107.178.195.aag,2017-06-30,00:00:05,0.0,1068124.0,0000350001-15-000731,-xbrl.zip,404.0,784.0,0.0,0.0,0.0,10.0,1.0,
107.23.85.jfd,2017-06-30,00:00:09,0.0,1136894.0,0000905148-07-003827,-index.htm,200.0,3021.0,1.0,0.0,0.0,10.0,0.0,
```

+ __input 2:__`inactivity_period.txt`

```
3
```

+ __output:__`sessionization.txt`

```
101.81.133.jja,2017-06-30 00:00:00,2017-06-30 00:00:01,2,3
106.120.173.jie,2017-06-30 00:00:02,2017-06-30 00:00:02,1,1
108.91.91.hbc,2017-06-30 00:00:01,2017-06-30 00:00:04,4,2
107.23.85.jfd,2017-06-30 00:00:00,2017-06-30 00:00:05,6,5
107.178.195.aag,2017-06-30 00:00:02,2017-06-30 00:00:05,4,3
107.23.85.jfd,2017-06-30 00:00:09,2017-06-30 00:00:09,1,1
```

## Why Dask?

 The `log.csv` file that we are currently handling is practically minuscule compared to the logfiles available at EDGAR website. As such, we need a scalable code to handle larger data sets. However, we do not want to use a distributed computing system for such a small dataset either. So we need a system capable of scaling up and out while also not losing performance when run in a single machine. The main reason *Pandas* library is not favored for this job is its lack of scalability. So we find the solution in the *Dask* library. While relatively new, and not entirely as well-implemented as Pandas, it is fully capable of both *multithreading* and *distributed computing* to tackle the large data sets rom EDGAR. Additionally, the *Dask.distributed* library is capable of processing streaming data parallely as they come in. If needed, we can easily modify the current code to handle datasets that night not even fit in computer memory.
 
 ## Final Comments
 
 + I would like to thank Insight Data Engineering team for the challenge. It was a pleasure to research and think about best ways of implementing the required program correctly and efficiently.
 
 + The code can be modified easily to include a list of document ids that were requested. 
 
 + If you have any question or comment regarding the code, or find a mistake somewhere, feel free to reach out to me   at `subhadipnet@gmail.com`.
