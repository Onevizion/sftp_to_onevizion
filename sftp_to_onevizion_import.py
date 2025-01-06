import sys
import subprocess
import glob

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'python_dependencies.txt'])


import onevizion
import argparse
import pysftp
import re
import time
import base64
import json
import os
from datetime import datetime

Description="""Import files from SFTP to OV in order
"""

# Read settings
with open('settings.json','r') as p:
	params = json.loads(p.read())
try:
	OvUserName = params['OV']['UserName']
	OvPassword = params['OV']['Password']
	OvUrl      = params['OV']['Url']
	SFtpPasswords = params['SFTP']
except Exception as e:
	raise "Please check settings by refering to documention in github repository"

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-v", "--verbose", action='count', default=0, help="Print extra debug messages and save to a file. Attach file to email if sent.")
args = parser.parse_args()

onevizion.Config["Verbosity"]=args.verbose
Message = onevizion.Message
Trace = onevizion.Config["Trace"]

###### os.remmove is not sufficent as sometimes when 

###### sort a list file names based on imbedded timestamp
def sortalist(listOfFileName,dateprefix,datecruft,datefmt):
	if len(listOfFileName) == 0:
		return None

	def return_date_from_filename(f):
		p = re.compile(dateprefix)
		r = p.search(f)
		return datetime.strptime(r.group(0).replace(datecruft,''), datefmt)

	if datefmt is None:
		return listOfFileName
	else:
		# administrators are more comfortable with oracle date formatting.  so change it into srtptime format if necessary
		datefmt = datefmt.replace('YYYY','%Y').replace('MM','%m').replace('DD','%d').replace('HH','%H').replace('MI','%M').replace('SS','%S')
		return sorted(listOfFileName,key=return_date_from_filename)


###### Run an import and wait for it to complete
def runAndWaitForImport(filename, impspec, action, maxRunTimeInMinutes):
	tries = -1
	maxTries = maxRunTimeInMinutes * 60 / 10

	Message(filename+' x '+impspec+' x '+action)
	Message('Kilroy was not here')
	imp = onevizion.Import(
		userName = OvUserName,
		password = OvPassword,
		URL = OvUrl,
		impSpecId=impspec,
		file=filename,
		action=action,
		comments=filename
		)

	if len(imp.errors)>0:
		Message(imp.errors)
		Message('ERROR: Could not run import')
		return False

	PID = imp.processId
	Message(PID)

	d = True
	while d:
		time.sleep(10)
		Message('Checking status '+str(tries)+' tries '+str(tries/6)+' minutes')

		tries = tries + 1
		if tries>maxTries:
			#todo more error handling
			Message('ERROR: Import took too long')
			return False

		# without impSpecId and file it will not attempt to run an import on object creation
		imp = onevizion.Import(
			userName = OvUserName,
			password = OvPassword,
			URL = OvUrl,
			impSpecId=None,
			file=None,
			action=None,
			comments=None
			)
		process_data = imp.getProcessData(processId=PID)

		if len(imp.errors)>0:
			Message(imp.errors)
			Message("ERROR: Could not get Process Data")
			tries = tries + 1
			continue

		if process_data["status"] in ['EXECUTED','EXECUTED_WITHOUT_WARNINGS','EXECUTED_WITH_WARNINGS']:
			d = False


	if process_data["status"] in ['EXECUTED','EXECUTED_WITHOUT_WARNINGS','EXECUTED_WITH_WARNINGS']:
		return True


class MyCnOpts:  #used by sftp connection
	pass

#####  Main section
Req = onevizion.Trackor(trackorType = 'SFTP_TO_OV', URL = OvUrl, userName=OvUserName, password=OvPassword)
Req.read(filters = {'SOI_ENABLED':'1'}, 
		fields = ['TRACKOR_KEY','SOI_SFTP_HOST', 'SOI_SFTP_USER_NAME', 'SOI_ORDER_TO_PROCESS',
					'SOI_SFTP_FOLDER', 'SOI_FILE_MASK', 'SOI_IMPORT_NAME', 'SOI_ACTION', 'SOI_IMPORT_ID',
					'SOI_SFTP_ARCHIVE_FOLDER', 'SOI_DAYS_TO_KEEP_IN_ARCHIVE',
					'SOI_DATE_PORTION_OF_FILE_NAME', 'SOI_DATE_CRUFT_TO_REMOVE', 'SOI_DATE_FORMAT',
					'SOI_PREPROCESSOR_SCRIPT','SOI_EXTRA_SFTP_COMMAND','SOI_PREPROCESSOR_COMMAND','SOI_MAX_RUNTIME_IN_MINUTES'], 
		sort = {'SOI_ORDER_TO_PROCESS':'ASC'}, page = 1, perPage = 1000)

if len(Req.errors)>0:
	# TODO implement better error handling
	print(Req.errors)
	quit(1)

for row in Req.jsonData:
	print(row)

	# connect to SFTP
	try:
		#not best practice, but avoids needing entry in .ssh/known_hosts
		#from Joe Cool near end of https://bitbucket.org/dundeemt/pysftp/issues/109/hostkeysexception-no-host-keys-found-even
		cnopts = MyCnOpts()
		cnopts.log = False
		cnopts.compression = False
		cnopts.ciphers = None
		cnopts.hostkeys = None

		password = SFtpPasswords[row['SOI_SFTP_HOST']][row['SOI_SFTP_USER_NAME']]

		if password.startswith('-----'):
			# it is a key with \n instead of newlines.
			with open('key.txt', 'w') as the_file:
				the_file.write(password)
			
			sftp = pysftp.Connection(row['SOI_SFTP_HOST'],
				username=row['SOI_SFTP_USER_NAME'],
				private_key='key.txt',
				cnopts = cnopts
				)
		else:
			sftp = pysftp.Connection(row['SOI_SFTP_HOST'],
				username=row['SOI_SFTP_USER_NAME'],
				password=password,
				cnopts = cnopts
				)
	except:
		Trace['SFTP Connect'] = sys.exc_info()[0]
		Message('could not connect')
		Message(sys.exc_info())
		quit(1)

	#todo error handling
	# get complete list of files in directory
	with sftp.cd(row['SOI_SFTP_FOLDER']):
		files = sftp.listdir()

	print(files)

	#Message(parameters["IMPORTS"][imp])
	#r = re.compile(parameters["IMPORTS"][imp]["prefix"])
	#filteredFiles = sortalist(list(filter(r.match,files)),parameters["IMPORTS"][imp])

	r = re.compile(row['SOI_FILE_MASK'])
	print(list(filter(r.match,files)))

	filteredFiles = sortalist(
		listOfFileName = list(filter(r.match,files)),
		dateprefix = row['SOI_DATE_PORTION_OF_FILE_NAME'],
		datecruft = row['SOI_DATE_CRUFT_TO_REMOVE'],
		datefmt = row['SOI_DATE_FORMAT'])

	if filteredFiles is None:
		Message('no matching files')
		continue

	if row['SOI_PREPROCESSOR_SCRIPT']['file_name'] is not None:
		print("script %s" % row['SOI_PREPROCESSOR_SCRIPT'])
		with open(row['SOI_PREPROCESSOR_SCRIPT']['file_name'],'wb') as pp:
			base64_bytes = row['SOI_PREPROCESSOR_SCRIPT']['data'].encode('utf-8')
			decodedbinary = base64.decodebytes(base64_bytes)
			pp.write(decodedbinary)

	for f in filteredFiles:
		Message(f)
		try:
			sftp.get(row['SOI_SFTP_FOLDER']+f, preserve_mtime=True)
		except:
			Message(sys.exc_info)
			try:
				os.remove(f)
			except:
				None
			quit(1) # process files on next fun.  Error on getting file usually because file is still being written to.

		if row['SOI_PREPROCESSOR_COMMAND'] is not None:
			cp = subprocess.run(row['SOI_PREPROCESSOR_COMMAND'].replace('{filename}',f), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			Message(cp.stdout.decode('utf-8'))
			Message(cp)
			#TODO Add Error Handling

		if row['SOI_MAX_RUNTIME_IN_MINUTES'] is None:
			maxRunTimeInMinutes = 10
		else:
			maxRunTimeInMinutes = int(row['SOI_MAX_RUNTIME_IN_MINUTES'])

		if runAndWaitForImport(f,row['SOI_IMPORT_ID'],row['SOI_ACTION'],maxRunTimeInMinutes):
			if row['SOI_EXTRA_SFTP_COMMAND'] is not None:
				extracmd = "sftp."+row['SOI_EXTRA_SFTP_COMMAND'].replace('{filename}',f)
				print(extracmd)
				exec(extracmd)
			elif row['SOI_SFTP_ARCHIVE_FOLDER'] is None or row['SOI_SFTP_ARCHIVE_FOLDER'] == '':
				sftp.remove(row['SOI_SFTP_FOLDER']+f)
			else:
				try:
					sftp.remove(row['SOI_SFTP_ARCHIVE_FOLDER']+f)
				except:
					None
				sftp.rename(row['SOI_SFTP_FOLDER']+f,row['SOI_SFTP_ARCHIVE_FOLDER']+f)
				Message("successfully imported {filename}".format(filename=f))

			try:
				os.remove(f)
			except:
				None
		else:
			try:
				os.remove(f)
			except:
				None
			quit(1)

	if row['SOI_PREPROCESSOR_SCRIPT']['file_name'] is not None:
		os.remove(row['SOI_PREPROCESSOR_SCRIPT']['file_name'])