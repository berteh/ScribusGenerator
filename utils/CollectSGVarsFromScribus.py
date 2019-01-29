
## CSV list for Scribus Generator
## Finds all objects with '%VAR' and lists in a csv (Filename, Variable and type: text/image
## CSV is stored in same folder with the suffix 'Elements'

## contribution from jvr14115, https://github.com/berteh/ScribusGenerator/issues/116
## run from within Scribus > Script > run Script

import os
import re
import scribus

Edoc = scribus.getDocName()
Edoc = Edoc.replace('.sla', '')
file_name = Edoc + 'Elements.csv'
Edoc = Edoc.replace('Elements.csv', '')
Edoc = re.search(r'(.*)/(.*)', Edoc).group(2)
f = open(file_name, 'w+')
f.write('Template,Element,ElementType')
f.write('\n')
objL = scribus.getAllObjects()
for obj in objL:
    objT = scribus.getObjectType(obj)
    Evar = ''
    if objT == 'ImageFrame':
        Etype = 'image'
        Evar = scribus.getImageFile(obj)
    if objT == 'TextFrame':
        Etype = 'text'
        Evar = scribus.getAllText(obj)
    if '%VAR_' in Evar:
        Evar = re.sub('^[^%VAR_]*%VAR_', '', Evar)
        Evar = Evar[:-1]
        f.write(Edoc + ';"' + Evar + '";' + Etype + '\n')
f.close
