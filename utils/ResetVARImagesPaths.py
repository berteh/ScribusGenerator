## Resets the default path for all %VAR images
## Default is on C:\, obviously can be changed
## Make sure to add the remainder of the path in the CSV file!!!

## contribution from jvr14115, https://github.com/berteh/ScribusGenerator/issues/102
## run from within Scribus > Script > run Script

import os
import re
import scribus

DefaultPath='C:/' ### change

Edoc=scribus.getDocName()
objL = scribus.getAllObjects()
for obj in objL:
	objT=scribus.getObjectType(obj)
	Evar=''
	if objT=='ImageFrame':
		Etype='image'
		Evar=scribus.getImageFile(obj)
		if '%VAR_' in Evar:
			Evar=re.search(r'(.*)/(.*)',Evar).group(2)
			Evar=DefaultPath+Evar
			scribus.loadImage(Evar,obj)
