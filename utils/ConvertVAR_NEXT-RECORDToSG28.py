import fileinput
import re
#
# convert old syntax of %VAR_NEXT-RECORD% to new syntax of %SG_NEXT-RECORD% in your SLA files (ScribusGenerator version 2.8+). Creates a backup of all modified files (.bak)
# run, for instance:
#    python ./ConvertVAR_NEXT-RECORDToSG28.py examples/old-template-with-VAR_NEXT-RECORD.sla
# 	 python ./ConvertVAR_NEXT-RECORDToSG28.py ~/ScribusProjects/*/*.sla

for line in fileinput.input(inplace=1, backup='.bak'):
    line = re.sub(r'VAR_NEXT-RECORD',
                  r'SG_NEXT-RECORD', line.rstrip())
    print(line)
