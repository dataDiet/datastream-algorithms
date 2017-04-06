# Details of Implementation 

The essential nature of this challenge was enabling abilities to handle a stream of data
while simultaneously outputting statics related to the stream.  When I first thought about
this problem, I considered that the problem fit within the realm of streaming data algorithms.
Namely, heavy hitter algorithms such as the Space Saver algorithm and the Lossy Algorithm.
However, in light of several limitations of those algorithms, I decided to use the powerful
built in data structures in Python.  These algorithms namely sacrifice accuracy for space
saving.  However, the specifications of the problem are given in such a way that inaccuracy
is not allowable.  Further, we imagined the use case for our script was for processing a batch of 
items of a manageable size from a log file and outputting the results at once.  Not processing
an effectively stream of data and in parallel outputting results at chosen moments in time, a distinction
that is important given the amount of RAM our script could potentially use in the span of processing
the log file.

Several packages in Python that I believe come built-in most installations are:

- datetime
- operator
- sys
- re
- os
- collections

### Feature 1: 
List the top 10 most active host/IP addresses that have accessed the site.

For the implementation of this feature increment a dictionary file with counts
associated with IP addresses.  The reason we chose a dictionary, is that it allows for
O(1) time in accessing counts at IP addresses and O(1) addition and removal of elements.
At the end we rely on Python's sorted method to sort the results and provide a top ten frequency.

### Feature 2: 
Identify the 10 resources that consume the most bandwidth on the site

The second feature was implemented in a analogous manner to Feature 1 only substituting counts
for bandwidth.

### Feature 3:
List the top 10 busiest (or most frequently visited) 60-minute periods 

This turned out to be the most troublesome aspect of the challenge.  For the given file
test file numerous utf-8 characters were encountered, thus a pre-cleaning step is performed
on the file prior to reading in as input.
The step of simply parsing the timestamp and transforming it into a datetime.datetime object
turns out to take considerable time.  Nonetheless, once the datetimes are properly formatted,
the frequencies of the datetimes are collected as in feature 1 and 2.  A sliding 60 minute window
is taken across the list of [datetime,frequency] and computes frequency in 1-second increment
periods.  The sorted outputs are then written to a file.  

### Feature 4: 
Detect patterns of three failed login attempts from the same IP address over 20 seconds so that all further attempts to the site can be blocked for 5 minutes. Log those possible security breaches.

For this feature we rely on two dictionaries in combination to accomplish the objective.  One dictionary
keeps track of potential ip addresses to block and the second dictionary keeps track of ip address to log
traffic from for potential further analysis.  An ip address begins as a member of neither dictionary.
Once it triggers a failed login event, it is entered as a potential ip address in the first dictioary.
Once the ip address has failed to login 3 times with a 20 second window, it is pushed onto the second
dictioary of blocked ip addresses and further traffic is logged.

A further challenge for implementing this challenge came in the form of outlining possible events and
correctly processing those events.

### Feature 5
List the top 10 ip addresses that access the most bandwidth.

Essentially we want to determine which ip addresses are consuming the most data from the site.  
Abnormally high levels of bandwidth consumption could indicate intent to scrape the site, which
is a nuisance to successful operation of the site.
