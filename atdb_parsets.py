# APERTIF PARSET GENERATOR ATDB VERSION 1.0 (atdb_parsets.py)
# Input: source text file
# V.A. Moss 10/10/2018 (vmoss.astro@gmail.com)
__author__ = "V.A. Moss"
__date__ = "$10-oct-2018 17:00:00$"
__version__ = "1.0"

import os
import sys
from beamcalc import *
from datetime import datetime,timedelta
from astropy.io import ascii
import numpy as np


# scopes: edit this to suit the current available scopes!
scopes = '[RT2, RT3, RT4, RT5, RT6, RT7, RT8, RT9, RTA, RTB, RTC, RTD]'

# Weight pattern dictionary
weightdict = {'compound': 'square_39p1_8bit_37beams',
			  'XXelement': 'ebm_20171214T104900.dat',
			  'YYelement': 'ebm_20171214T104900.dat',
			  'hybrid': 'hybridXX_20180928_8bit'}


# beam switching time
swtime = 10.25
rndbm_set = list(np.arange(0,37))

# renumber scans
renum = False 

# Read in the source file
try:
	fname = sys.argv[1]
except:
	fname = 'input/input_20181005.txt'

def ra2dec(ra):
    if not ra:
        return None
      
    r = ra.split(':')
    if len(r) == 2:
        r.append(0.0)
    return (float(r[0]) + float(r[1])/60.0 + float(r[2])/3600.0)*15

def dec2dec(dec):
    if not dec:
        return None
    d = dec.split(':')
    if len(d) == 2:
        d.append(0.0)
    if d[0].startswith('-') or float(d[0]) < 0:
        return float(d[0]) - float(d[1])/60.0 - float(d[2])/3600.0
    else:
        return float(d[0]) + float(d[1])/60.0 + float(d[2])/3600.0


def writesource(i,j,scan,date,stime,date2,etime,lo,sub1,src,ra,dec,old_date,old_etime,field,ints,weightpatt):

	# Determine the execute time
	if j == 0:

		# Old method, needs to change!! 
		#exetime = 'utcnow()'
		#exectime = None
 
		# Set the exec time to 10 min before start of scan (9/05/2018 VAM)
		exectime = datetime.strptime(date+stime,'%Y-%m-%d%H:%M:%S')-timedelta(minutes=10)
		exetime = str(exectime.date()) + ' ' + str(exectime.time())
		exetime = 'utcnow()'

	else:

		sdate_dt = datetime.strptime(str(date)+str(stime),'%Y-%m-%d%H:%M:%S')

		# Make it a 15 second gap between execution of the next parset (25/9/18 VM)
		exectime = datetime.strptime(old_date+old_etime,'%Y-%m-%d%H:%M:%S')+timedelta(seconds=15)
		exetime = str(exectime.date()) + ' ' + str(exectime.time())

		# Correct if too long
		if (sdate_dt-exectime).seconds > 600.:
			# Set the exec time to 10 min before start of scan (9/05/2018 VAM)
			exectime = datetime.strptime(date+stime,'%Y-%m-%d%H:%M:%S')-timedelta(minutes=10)
			exetime = str(exectime.date()) + ' ' + str(exectime.time())


	# Determine what the scan id is
	print(renum)
	if renum != False:
		print (d['scan'][i])
		scan = str(d['scan'][i])[:-2]+ '%.2d' % (j+1)
		print (scan)


	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=0 --starttime='%s %s' --endtime='%s %s' --pattern=%s --integration_factor=%s --central_frequency=1400 --data_dir=/data/apertif/ --operation=specification --atdb_host=prod \n\n""" % (src,ra,dec,date,stime,date2,etime,weightpatt,ints))
	out.flush()

	return scan
	

################################################

# Read file
d = ascii.read(fname,delimiter='\s',guess=False)
print(list(d.keys())) 

# Start the file
outname = '%s_params_ag.sh' % (fname.split('.')[0])
out = open(outname,'w')
out.write('#!/bin/bash\n# Script to create parsets for APERTIF ATDB\n# Automatic generation script by V.A. Moss 04/10/2018\n# Last updated by V.A. Moss 04/10/2018\n\n')
out.flush()

# Task ID counter
j = 0
sendcmd = 'send_file -t 0'

# Initialise
old_date = None
old_etime = None

# Loop through sources
for i in range(0,len(d)):

	# Details source
	src = d['source'][i]
	src_obstype = d['type'][i]
	field = d['intent'][i].upper()

	# Define weight pattern
	weightpatt = weightdict[d['weight'][i]]

	# Account for RFI sources:
	if 'deg' in d['ra'][i]:
		ra = float(d['ra'][i].split('deg')[0])
		dec = float(d['dec'][i].split('deg')[0])

	# With :
	elif ':' in d['ra'][i]:
		ra = ra2dec(d['ra'][i])
		dec = dec2dec(d['dec'][i])

	# With HMS
	else:
		ra = ra2dec(d['ra'][i].replace('h',':').replace('m',':').replace('s',''))
		dec = dec2dec(d['dec'][i].replace('d',':').replace('m',':').replace('s',''))
	
	# Details obs
	stime = d['time1'][i]
	etime = d['time2'][i]
	date = d['date1'][i]
	ints = d['int'][i]

	# Details system
	lo = d['lo'][i]
	sub1 = d['sub1'][i]
	scan = d['scan'][i]

	# Fix times if they aren't the right length
	if len(stime.split(':')[0]) < 2:
		stime = '0'+stime
	if len(etime.split(':')[0]) < 2:
		etime = '0'+etime

	# do a check for the end time
	stime_dt = datetime.strptime(stime,'%H:%M:%S')
	etime_dt = datetime.strptime(etime,'%H:%M:%S')
	if etime_dt < stime_dt:
		date2 = datetime.strptime(date,'%Y-%m-%d')+timedelta(days=1)
		date2 = datetime.strftime(date2,'%Y-%m-%d')
	else:
		date2 = date

	# total date time
	sdate_dt = datetime.strptime(date+stime,'%Y-%m-%d%H:%M:%S')
	edate_dt = datetime.strptime(date2+etime,'%Y-%m-%d%H:%M:%S')

	# Account for beam switching
	if 'S' in src_obstype:

		obslength = (etime_dt-stime_dt).seconds/3600.
		step = swtime/60.
		numscans = obslength / (step + 1/60.)
		print(step, step*60.,numscans,obslength)

		# Randomise beams if there is a ? in the specification
		if '?' in src_obstype:
			rndbm = [0]
			bm = 0
			for jj in range(0,int(numscans)):
				print('Finding beams...')

				# Note: this cannot handle 37 beams yet...
				while bm in rndbm:
					bm = int(rand()*36)
				rndbm.append(bm)
		else:
			rndbm = rndbm_set	
		nbeams = len(rndbm)
		print('Selected beams: ',rndbm)
		print('Number of beams: ',nbeams)	
		
		# Write the observations to a file:
		for k in range(0,int(numscans)):

			# Need to divide by num beams to decide which beam it will do?
			print(k)
			print(k % len(rndbm))
			chosenbeam = rndbm[k % len(rndbm)]
			print('chosen beam:',chosenbeam)

			# Update the scan
			scan = str(d['scan'][i])[:-2]+ '%.3d' % (j+1)
			print(scan)

			beamname = 'B0%.2d' % chosenbeam
			src = '%s_%s' % (d['source'][i],chosenbeam)

			print(beamname,src)

			# Calculate the new position for that given beam
			# Note: using compound beam positions
			ra_new,dec_new = calc_pos_compound(ra,dec,beamname)
			print(ra_new,dec_new)

			# New execute time
			print(old_date,old_etime)
			exectime = datetime.strptime(old_date+old_etime,'%Y-%m-%d%H:%M:%S')+timedelta(seconds=15)

			# Recalculate the start and end time
			if k == 0:
				sdate = exectime + timedelta(minutes=10.)
				edate = exectime + timedelta(minutes=step*60.+10.)
			else:
				sdate = exectime + timedelta(minutes=1.)
				edate = exectime + timedelta(minutes=step*60.)

			# Write sources to file
			scannum = writesource(i,j,scan,sdate.date(),sdate.time(),edate.date(),edate.time(),lo,sub1,src,ra_new,dec_new,old_date,old_etime,field,ints,weightpatt)		

			# update parameters
			old_etime = str(edate.time())
			old_date = str(edate.date())
			j+=1

			sendcmd = sendcmd + ' ' + '/opt/apertif/share/parsets/%s.parset' % scannum

	# Standard observation otherwise
	else:	

		# Write sources to file
		scannum = writesource(i,j,scan,date,stime,date2,etime,lo,sub1,src,ra,dec,old_date,old_etime,field,ints,weightpatt)		
		j+=1
		sendcmd = sendcmd + ' ' + '/opt/apertif/share/parsets/%s.parset' % scannum

	# update parameters
	old_etime = etime
	old_date = date2


# Make the resultting file executable
os.system('chmod oug+x %s' % outname)

print (sendcmd)



