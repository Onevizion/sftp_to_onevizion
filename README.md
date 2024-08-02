# sftp_to_onevizion
Load files from an sftp location and run as onevizion imports.

There are 2 implementations and it is your choice which to use.  sftp_to_onevizion_import uses trackors.  sfp_to_ov.py uses a json file as complete configuration.


## sftp_to_onevizion_import.py

This uses a trackor to complete configuration.  Use component import with the file components.xml to install the trackor type and it's associated applet.

Example settings file.
```json
{
	"OV": {
			"Url": "xxx.onevizion.com",
			"UserName": "usernameofserviceaccount",
			"Password": "passwordofserviceaccount"
	},
	"SFTP": {
		"ftp.onevizion.com": {
			"abc" : "abcpassword",
			"bbb" : "bbbpassword",
			"cde" : "cdepassword"
		}
	}
}
```

| Field | Description | Example |
| --- | --- | --- |
| SFTP Host | Fully qualified name or IP of sftp server | ftp.onevizion.com |
| SFTP User Name | User Name which is usually case sensitive | bbb |
| Order to Process | All files with "Order to Process" equal to 1 will be fully imported before proceeding to those with "Order to Process" equal to 2 | 1 |
| SFTP Folder | Path to files on SFTP.  Please include trailing "/" | /home/bbb/Inbound/ |
| File Mask | Part of the file name to identify target files. For JDE_PO_2021_10_13.csv | JDE_PO_20 |
| Import Name | Name of the import within OneVizion.  Make sure that the OneVizion service account for this integration has permissions to run the import | PO Default Import |
| Action | How to import the data.  Valid choices are INSERT, UPDATE and INSERT_UPDATE | INSERT_UPDATE |
| Max Runtime in Minutes | Once in a very rare while, an import might get stuck.  This allows the integration to continue on | 15 |
| Purpose | Place to document what the overall purpose of the import is for | Create and update PO information from JDE so that Managers can manage Vendor POs within OneVizion for a later export to JDE (see requirement 123) |
| Import ID | Read only field that is calculated when you choose an import above.  No input required | 1000134 |
| SFTP Archive Folder | Optional folder to store file on the SFTP server.  If not specified, the file will be deleted from SFTP after the import has successfully completed | /home/bbb/Inbound/Archive/ |
| Days to keep in archive | (Not yet implemented) Number of days to keep files in archive folder so the SFTP does not run out of space (optional) | 30 |
| Date Portion of File Name | Part of the filename that contains the date using regular expressions | PO_[0-9]* |
| Date Cruft to Remove | Extra part of date portion that is not actually part of the imbedded date | PO_ |
| Date Format | Format of the imbedded date which can be in either strftime date format (see [https://strftime.org](https://strftime.org)) or YYYY for year, MM for month, HH for 24 hour time, MI for minutes, SS for seconds | %Y_%m_%d |
| Extra SFTP Command | (TDB) |  |
| Preprocessor Command | Command to execute before the import.  An example might to remove all double quotes from the file. {filename} will get replaced with actual filename | sed -i 's/"//d' {filename} |
| Preprocessor Script | This can be a script or executable to be used in the preprocessor command.  An example might be using the drop_duplicates.py script to take a csv with purchase orders and purchase order lines to an easier to import file that does not have purchase order information repeated | (ex TDB) |


Note that SFTP section of the setting file will be where the password is retrieved based on SFTP Host and SFTP User Name.


## sftp_to_onevizion_import_mult.py

This uses a trackor to complete configuration.  Use component import with the file components.xml to install the trackor type and it's associated applet.  It uses the same configuration as in the sftp_to_onevizion_import.py section.

This runs multiple imports simultaneously, waits for all of a particular kind to finish (example PO files), then proceeds to the next kind (example PO Line files).  It does this because sometimes a PO Line import is dependant on the PO imports having finished properly.  During the window that the imports are to be processed the internal needs to be smaller than the default such as every 2 or 3 minutes (example below) since it should take many module runs to fully process as it is more of a polling process.
```
0/3 0 0 * * ?
```

Example settings file.  Please note that the MaxImports is dependant on the size (# of CPUs) of your database.
```json
{
	"OV": {
			"Url": "xxx.onevizion.com",
			"UserName": "usernameofserviceaccount",
			"Password": "passwordofserviceaccount",
			"MaxImports": 3
	},
	"SFTP": {
		"ftp.onevizion.com": {
			"abc" : "abcpassword",
			"bbb" : "bbbpassword",
			"cde" : "cdepassword"
		}
	}
}
```


## sftp_to_ov.py

This uses a json file as complete configuration.  Since everything is in the json, you can install it more than once each utilizing a different service accounts within onevizion.

This will use the IMPORT_ORDER section of the settings file to determine the order to run the imports.  Then it will process the files in SFTP folder that match the criterion in the matching IMPORTS section (details below).  For each import section, each matching file will be imported and the integration will wait on the import to finish before proceeding to next matching file.  When all files have been processed, it will proceed to the next IMPORT section based on the IMPORT_ORDER section.

Example settings file.
```json
{
	"abc.onevizion.com": {
			"url": "abc.onevizion.com",
			"UserName": "usernameofserviceaccount",
			"Password": "passwordofserviceaccount"
	},
	"SFTP": {
		"url" : "ftp.onevizion.com",
		"UserName" : "abc",
		"Password" : "qwe",
		"Directory" : "/home/abc/imports/Inbound/"
	},
	"IMPORTS": {
		"ring" : {
			"prefix" : "ring_[0-9]*_export_202.*",
			"dateprefix" : "export_[0-9]{12}",
			"datecruft" : "export_",
			"datefmt" : "%Y%m%d",
			"impspec" : 100006284,
			"impname" : "Ring Default Data Import",
			"action" : "INSERT_UPDATE"
		}
		,"site" : {
			"prefix" : "site_[0-9]*_export_202.*",
			"dateprefix" : "export_[0-9]{12}",
			"datecruft" : "export_",
			"datefmt" : "%Y%m%d",
			"impspec" : 100006285,
			"impname" : "Site Default Data Import",
			"action" : "INSERT_UPDATE"
		},
		"project" : {
			"prefix" : "project_[0-9]*_export_202.*",
			"dateprefix" : "export_[0-9]{12}",
			"datecruft" : "export_",
			"datefmt" : "%Y%m%d",
			"impspec" : 100006286,
			"impname" : "Project Default Data Import",
			"action" : "INSERT_UPDATE"
		}
	},
	"IMPORT_ORDER" : [
		"ring",
		"site",
		"project"
	]
}
```

Imports Section

Example.  filename = ring_1234_export_202012312312.csv
The Table below describes how the IMPORT section would be configued for this example.

| Column | Description | Example |
| --- | --- | --- |
| prefix | front part of filename with regex | ring_1234_export_202.* |
| dateprefix | part of the filename that contain the date (optional) | export_202012312312 |
| datecruft | part of the dateprefix that needs to be removed to leave only the date | export_ |
| datefmt | strftime date format - see [https://strftime.org](https://strftime.org) for reference | %Y%m%d |
| impspec | ID of the import from the Build Import page | 100006284 |
| impname | Name of the import from the Build Import page | Ring Default Data Import |
| action | How to import the data.  Valid choices are INSERT, UPDATE and INSERT_UPDATE | INSERT_UPDATE |


