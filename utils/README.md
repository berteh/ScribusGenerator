Various Scripts
===========

Collect variables in template
-----------

To find all objects with '%VAR' and lists them in a csv (Filename, Variable and type: text/image), 
[jvr14115](https://github.com/berteh/ScribusGenerator/issues/116) provided a script you need
to run from within Scribus ``> Script > run Script``, pick ``utils/CollectSGVarsFromScribus.py``

Resulting CSV is stored in same folder with the suffix 'Elements'.

Improvement suggestions are welcome to handle multiple %VAR_%'s in single text frame.



Fixes to retro-compatibility issues
-----------

SG v2.7 (April 2018) changed the syntax of [Advanced Attributes](https://github.com/berteh/ScribusGenerator#more-advanced-uses),
to support Scribus 1.5 branch.

Update your older templates by calling, for instance:

    python ./ConvertSGAttributesToSG27.py ~/ScribusProjects/*/*.sla


SG v2.8 (January 2019) changed the syntax of the ["Next Record" feature](https://github.com/berteh/ScribusGenerator#multiple-records-on-a-single-page)
to a less confusing name, as per [suggestion #118](https://github.com/berteh/ScribusGenerator/issues/118)

Update your older templates by calling, for instance:
    
    python ./ConvertVAR_NEXT-RECORDToSG28.py ~/ScribusProjects/*/*.sla
