import fileinput
import re
#
# convert old syntax of SGAttribute to new syntax in your SLA files (ScribusGenerator version 2.7+). Creates a backup of all modified files (.bak)
# run, for instance:
#    python ./ConvertSGAttributesToSG27.py examples/old-template-with-SGAttributes.sla
# 	 python ./ConvertSGAttributesToSG27.py ~/ScribusProjects/*/*.sla
#
# replaces ItemAttribute Name="YPOS" Type="SGAttribute" Value="%VAR_top%" Parameter="/" Relationship="none" RelationshipTo=""
# into     ItemAttribute Name="YPOS" Type="none" Value="%VAR_top%" Parameter="SGAttribute" Relationship="none" RelationshipTo="/"

for line in fileinput.input(inplace=1, backup='.bak'):
    line = re.sub(r'(<ItemAttribute .+?)Type="SGAttribute"(.+?)Parameter="([^"]*?)"(.+)?RelationshipTo=""',
                  r'\1Type="none"\2Parameter="SGAttribute"\4RelationshipTo="\3"', line.rstrip())
    print(line)
