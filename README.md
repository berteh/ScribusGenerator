ScribusGenerator
================

Template and "Mail Merge"-like engine, to generate beautiful documents automatically from your spreadsheet content, in PDF or Scribus OpenSource PAO format.

[<img alt="Scribus Generator. Generate beautiful documents from data." src="https://github.com/berteh/ScribusGenerator/raw/master/pic/ScribusGenerator_logo.png" width="60px" align="top"> Scribus Generator: Create beautiful documents with data](https://github.com/berteh/ScribusGenerator/). Open source high-quality PDF template and mail-merge alternative. Your imagination is the limit for creating beautiful yearbooks, personalised weddings invitations, game card decks, club rosters, art or work portfolio and [many more](https://github.com/berteh/ScribusGenerator/wiki#gallery-of-examples--some-templates).

What is Scribus Generator?
-------

[**ScribusGenerator**](https://github.com/berteh/ScribusGenerator/) turns any beautiful document into a template to create an original set based on your data, built on top of the [Scribus](http://www.scribus.net/) open-source PAO studio. Use it to create card decks, business cards, personalized letters, leaflets... just like „Mail Merge“ in your preferred office application, but beautiful and flexible.

[**ScribusGenerator**](https://github.com/berteh/ScribusGenerator/) allows you to:

- replace texts and images dynamically
- change object colors, positions, font or size dynamically
- generate separate PDF (or Scribus) files for each data entry, or a single file from all your data
- work directly in Scribus with a nice user interface, or from the command line
- use any data source (Excel, Libre/OpenOffice, MySQL, Notepad, ...) that can export to CSV
- and much more...

Generally speaking, **ScribusGenerator** replaces text with data to automatically generate files (e.g. SLA, PDF). It was originally written by [Ekkehard Will](http://www.ekkehardwill.de/sg/) and further extended by [Berteh](https://github.com/berteh/).

A [short *how to* video](https://www.youtube.com/watch/kMsRn38TOiQ) gives an introduction to ScribusGenerator. The first 6 minutes give a basic overview, the latter 12 cover some more advanced features.

[![Scribus Generator how to - high quality pdf generation](pic/screencast.png)](https://www.youtube.com/watch/kMsRn38TOiQ)

How to install ScribusGenerator?
-------

For Scribus 1.4.x to 1.5.5: [Download](https://github.com/berteh/ScribusGenerator/archive/master.zip) the script and uncompress it anywhere on the local machine in a folder your user can write to. **ScribusGenerator** can then be started by choosing the script (``ScribusGenerator.py``) within the dialog: _«Scribus → Script → Execute Script»_, or from the [command line](#running-scribus-generator-from-the-command-line).

For Scribus 1.5.6+, please [download the (more recent) ScribusGenerator for Python3](https://github.com/berteh/ScribusGenerator/archive/python3.zip) version. A few small features and syntactic updates were added for the more recent Python3 engine.


### MacOSX issues

We recommend running ScribusGenerator in MacOSX from the [command line](#running-scribus-generator-from-the-command-line), since the graphical interface of ScribusGenerator requires Tkinter to be installed in your Python setup, which may be difficult under MacOSX.

How to use ScribusGenerator 
------

### Create your Scribus "template" file

Create and design your Scribus file as any other. At the positions where you need to replace text with data, just add ``%VAR_name%`` where ``name`` is the column name your data file. Check out our [gallery of examples](https://github.com/berteh/ScribusGenerator/wiki#gallery-of-examples--some-templates) to see what others did. [Any existing Scribus file](https://www.scribus-templates.net/) can be used as template.

You can place the variable at any position within a Text Frame. Apply all format and styles to the variable that you wish the final text to have.

![Illustration: Scribus File for Generator](pic/SG-01.png)

If you wish to generate one page for each data entry (or however many one data entry gets you), you're done, congratulations! If you would rather display many data records on a single page, simply add the text ``%SG_NEXT-RECORD%`` **before each entry except the first**: ScribusGenerator will automatically load the new data record as soon as it detects this token. For more information see the [dedicated documentation page](https://github.com/berteh/ScribusGenerator/wiki/How-to-use-%25SG_NEXT-RECORD%25).


### Create your (CSV) data File

**ScribusGenerator** expects a CSV file (_Comma Separated Values_), which is very simple to create with a standard spreadsheet editor (such as [LibreOffice](http://www.libreoffice.org/), Excel or Google Sheets): enter the data and save/export as CSV. Just make sure your CSV file is encoded in UTF-8 to have a full character set (accents, braille, math, cyrillic, symbols, ...).

Each row is considered as one data record and used to generate a separate copy based on the template.

![Illustration: Data File for Generator](pic/SG-05.png)

It is important to make sure the columns have the same ``name`` as the variables (``%VAR_name%``) you used in the Scribus template file you designed.

We recommend saving in UTF-8 encoding to enable the full set of accented characters, non-Latin scripts, math symbols, arrows, braille, symbols and [many more](http://csbruce.com/software/utf-8.html). Simply copy & paste those for which you lack a keyboard combination.

To export well-formatted CSVs in UTF-8 encoding is easy as pie with OpenOffice or LibreOffice Calc, less so with Excel. If you are using Microsoft Excel, you may be interested in this free add-in that provides good export/import features: http://www.csvio.net/

CSV files can easily be generated from many existing data sources (incl. enterprise-grade ETL platforms, most databases like MySQL, PostgreSQL, SQLite3 and more), see our wiki page for using [other data sources](https://github.com/berteh/ScribusGenerator/wiki/Other-data-sources)

Run the Generator Script - Settings
---------

Run the script via the menu: ``Script > execute Script`` and launch ``ScribusGenerator.py``.

In the script dialog you can configure the input and output settings for **ScribusGenerator**.

![Illustration: Input and Output Settings](pic/SG-10.png)

| Input Setting | explanation |
| ---- | ---- |
| **Scribus File** | Choose the Scribus File containing the variables to replace. Click ⏏ to open a file explorer, and ↺ to load the ScribusGenerator settings from that file. |
| **Data File** | Choose the Data File containing the comma separated values. Click ⏏ to open a file explorer. |
| **Data Field Separator** | Character that delimitates data field in your CSV file, comma (,) by default. |
| **From - To** | To run ScribusGenerator on a subset of your data, mention the starting and/or last lines of this subset, not counting the header line. Simply leave empty to generate from the first (and to the last) row of data.|

| Output Setting | explanation |
| ---- | ---- |
| **Output Directory** | Choose the path to an existing directory where to save the result. Click ⏏ to open a file explorer. |
| **Output File Name** | You can use the same variables as defined in the Scribus File/Data File. You can also mix the variables with other characters. If you leave the field empty, an index will be used. The index/resulting files will be sorted according to the order of rows in the Data File. |
| **Save Settings** | Store the current ScribusGenerator settings in the source SLA file, for future use. |
| **Merge in Single File** | Select to generate a single output (SLA and/or PDF) file that combines all data rows. |
| **Ouput Format** | Choose the Output Format of the generated files, either PDF or Scribus. |
| **Keep Scribus Files** | Select to keep the generated Scribus Files. Otherwise they will be deleted after PDF generation. This option has no effect if you choose Scribus output format.|

Additional (more technical) options can be set to tailor the automatic recording of Scribus Generators actions in your system by editing the ```logging.conf``` file. You may, for instance, want to move the location of the log file (```scribusGenerator.log``` by default) to a directory that does not need admin rights to edit in Windows  (```C:\tmp\scribusGenerator.log```), or replace file-logging with your default system logger (SysLogHandler in Linux, NTEventLogHandler on Windows). All settings (and more) are described in the [Python logging documentation](https://docs.python.org/2/howto/logging.html).


Dynamic Images
------------

Images references can also be dynamically modified with **ScribusGenerator**. See the [screencast video @6:10](https://www.youtube.com/watch?feature=player_detailpage&v=kMsRn38TOiQ#t=370).

All images supported by **Scribus** can be used. However, to work with ScribusGenerator, they must all be located in a single folder containing all images. This folder can be located anywhere on your PC. Duplicate any image in this folder and rename it ``%VAR_pic%`` (and similarly for any other variable name you would like to use, e.g. ``%VAR_pic2%, %VAR_photo%``). 

Add an Image Frame anywhere in the Scribus file (_«Scribus → Insert → Insert Image Frame»_) and open the dialog for getting an image (e.g. right-click _Image Frame → Get Image..._ on selected frame). Select the required "placeholder" picture.

![Illustration: Insert variable instead of image](pic/SG-15-1.png)

The images file can be defined just like any other variable described in earlier, i.e. there has to be a column with a column name corresponding to the variable name used in the Scribus template file. Just make sure to handle the file extension either in the file name, or in the CSV data, but not in both.

![Illustration: Data file referencing images](pic/SG-15-3.png)

Importing vector images (SVG, PDF or other) as Image Frames does work in ScribusGenerator, just as with PNG or JPG images; just make sure your (relative or absolute) SVG *file path matches the generator **output directory***, as that is the place Scribus will be looking from when transforming the SLA into your PDF format.

Scribus sometimes renders the included image in really low resolution, so you should check out the resolution (dpi) (and or size) or your source material. To quickly batch export SVG objects in multiple resolutions you may be interested in this [Inkscape object export script](https://github.com/berteh/svg-objects-export).

There is unfortunately no way to dynamically include vector files (pdf or svg) with ScribusGenerator, because of the way Scribus imports them (from the menu _File > Import > Vector_) by converting them on-the-fly to Scribus objects. Which is great for direct editing in Scribus, but not for including external files by reference.

Dynamic Colors
---------------

Colors can be dynamically replaced just like text. See the [screencast video @8:31](https://www.youtube.com/watch?feature=player_detailpage&v=kMsRn38TOiQ#t=512), or simply 

1. edit the colors of your Scribus file (``edit > colours``) and rename the colors you want to replace with variable names (typically replace ``FromSVG#whatever`` with the now well known form ``%VAR_name%``).
1. define the colors you want to use in the final document, and use their Scribus names as values in your color data field. 

![Illustration: Replace colors dynamically](pic/SG-16.png)

Use this together with the many color palettes directly included in Scribus to make your documents design rich and appealing!

Dynamic Links
--------------

A clickable (web)link can be inserted on nearly any scribus object in 2 steps:

1. ``right-click > PDF Options``, activate ``Is PDF Annotation``
1. ``right-click > PDF Options > Annotation Properties``, select type ``External Web-Link`` and enter the target url, where you can obviously use variables to be substituted too, as illustrated below.

![Illustration: Include dynamic clickable (web)links](pic/weblink_pdfannotation.png)


Merged output - single document
------------
Instead of generating a single (SLA or PDF) file for each data row, you can generate a single file that merges all of them. Simply select the option accordingly to get the result shown below in a single Scribus (and/or PDF) file. If your document layout has multiple pages (double-sided, or folded leaflet), it is important that your template has the same number of pages (or a multiple thereof) for ScribusGenerator to be able to merge the files. For instance, for a 3-fold document, your source SLA should have 3, 6, or 9 pages (or any other multiple of 3).

![Illustration: Single ouput to merge all generated files](pic/mergedSLA.png)


Multiple records on a single page
-----------
[**Scribus Generator**](https://github.com/berteh/ScribusGenerator/) allows you to display mupliple data records in a single document. Great to generate your own listings, team charts, game cards, "Who's who" posters and more.

Simply drop the text ``%SG_NEXT-RECORD%`` in your document _before each data entry except the first_ record, following our [example document](https://github.com/berteh/ScribusGenerator/blob/master/example/Next-Record.sla). Kindly note this token is case-sensitive and must be _upper-case_. ScribusGenerator will automatically load the next record as soon as it detects ``%SG_NEXT-RECORD%``, and when it reaches the end of your template.

The feature to include several data records on a single page (or document) works great, but is error-prone, please read (and improve) our [dedicated wiki page for multiple records, SG_NEXT-RECORD](https://github.com/berteh/ScribusGenerator/wiki/How-to-use-%25SG_NEXT-RECORD%25).

[<img src="http://imgur.com/8yRVWOEl.png" alt="Multiple records how-to, example" height="250px">](https://github.com/berteh/ScribusGenerator/wiki/How-to-use-%25SG_NEXT-RECORD%25)
[<img src="https://github.com/berteh/ScribusGenerator/raw/master/pic/MonsterCards_partial.png" alt="Example card deck of monsters, by Dustin Andrew" height="250px">](https://github.com/berteh/ScribusGenerator/wiki/How-to-use-%25SG_NEXT-RECORD%25#other-examples)

Dynamic output file location
-----------
[**Scribus Generator**](https://github.com/berteh/ScribusGenerator/) allows you to customize the name (and location) of the generated document easily. Add the output file name you wish in your data, and use the corresponding variable (or combination of multiple variables) in the field "Output File Name". Kindly note this file name is always relative to the output directory, and has *no extension*.

Have a look at the combination of values of ``parent`` and ``outfile`` in our [example dataset](https://github.com/berteh/ScribusGenerator/blob/master/example/DynamicOutFile.csv) and related [example template](https://github.com/berteh/ScribusGenerator/blob/master/example/DynamicOutFile.csv)..

![Illustration: Name your generated documents as like](pic/DynamicOutFile.png)


More advanced uses
-----------
ScribusGenerator allows more tech-savvy users to customize the generated documents even more, changing virtually any attribute of any object, such as fill or outline color of a line, text color, line thickness, object position, ... See the [screencast video @13:13](https://www.youtube.com/watch?feature=player_detailpage&v=kMsRn38TOiQ#t=793).

For instance, to change the *font* of an object dynamically, add an *attribute* to it (_«right-click on object → Attributes → Add »_). The **Parameter** attribute must be set to [``SGAttribute``][1], its **name** to the [object property][2] you want to change (in this case ``FONT``) and its **value** to the desired dynamic value (typically some ``%VAR_name%``).  Your data (CSV) file should then contain the font name to use in the column of the given variable, such as "Arial Regular" or "Courier New Bold".

![Illustration: Use Attributes to modify advanced object properties](pic/SG-20-new.png "Use Attributes to modify advanced object properties")

To change the properties of a sub-element (such as one particular text line in a text frame), you may use the **RelationshipTo** field to define which sub-elements should receive the new property. Use ``*`` to modify all direct children, or any other [simplified XPATH expression][3] to modify only a subset.

### Selected examples of SGAttributes:

| Name | Value | Parameter | RelationshipTo | Explanation 
| --- | --- | --- | --- | --- |
| ``FONT`` | ``%VAR_font%`` | ``SGAttribute`` | ``//ITEXT[2]`` | Font of the 2D text line in a frame, e.g. "Arial Regular"
| ``FONTSIZE`` | ``%VAR_size%`` | ``SGAttribute`` | ``//ITEXT`` | Text size of all text lines in a frame, e.g. "14" 
| ``LINESP`` | ``%VAR_spacing%`` | ``SGAttribute`` | ``//para[last()]`` | Fixed line spacing of the last paragraph in a frame, e.g. "9.5"
| ``YPOS`` | ``%VAR_top%`` | ``SGAttribute`` |  | Margin from the top for vertical element position, e.g. "22.04"
| ``ROT`` | ``%VAR_degrees%`` | ``SGAttribute`` |   | Rotation of the current object in degrees, [0 , 359]

Please note ScribusGenerator does not create the attribute, but only updates its value. So you may need to slightly rotate the object (just put any value but 0 in the rotation box, it will be replaced anyway) to ensure the ``ROT`` attribute is indeed used by Scribus when saving the file.


[1]: # "SGAttribute is short for 'Scribus Generator Attribute'"
[2]: http://wiki.scribus.net/canvas/File_Format_Specification_for_Scribus_1.4#Tags "Object property is expressed in the exact SLA syntax"
[3]: https://docs.python.org/2/library/xml.etree.elementtree.html#supported-xpath-syntax "The reduced set of XPATH expressions valid in the 'parameter' field is defined in the ElementTree XPath support documentation."

### Changes in SGAttribute syntax

Since ScribusGenerator v2.7 (released in April 2018), the syntax of the SGAttributes has been slightly changed to support Scribus 1.5.3. 
If you had templates written for an older version of the script, kindly update your templates according to the documentation above.

This can be done using the classical Scribus Editor windows, simply moving your values of ``Parameter`` to ``RelationshipTo``, and setting ``Parameter`` to ``SGAttribute``.

If you have a large number of such files or attributes, a script is provided to make this update automatically. Run it from the command line as follows (a backup of your old files is created automatically):
 
    python ./ConvertSGAttributesToSG27.py *.sla


Running ScribusGenerator from the command line
---------
It is possible to run ScribusGenerator from the command line, and it's fast! Great to automate your workflow or integrate with other tools.

Please note only the SLA generation works from the command line. PDF generation is not suppoted from the ScribusGenerator command line at the moment.

Find all required information from the script help: ``./ScribusGeneratorCLI.py --help``

```
positional arguments:
  infiles               SLA file(s) to use as template(s) for the generation,
                        wildcards are supported

optional arguments:
  -h, --help            Show this help message and exit
  -c CSVFILE, --csvFile CSVFILE
                        CSV file containing the data to substitute in each
                        template during generation. Default is Scribus source
                        file(s) name with "csv" extension instead of "sla". If
                        CSV file is not found, generation from this particular
                        template is skipped.
  -d CSVDELIMITER, --csvDelimiter CSVDELIMITER
                        CSV field delimiter character. Default is comma: ","
  -n OUTNAME, --outName OUTNAME
                        Name of the generated files, with no extension.
                        Default is a simple incremental index. Using SG variables
                        is allowed to define the name of generated documents.
  -o OUTDIR, --outDir OUTDIR
                        Directory where generated files are stored. Default is
                        the directory of the scribus source file. outputDir
                        will be created if it does not exist.
  -m, --merge, --single
                        Generate a single output (SLA) file that combines all
                        data records for each source file.
  -from FIRSTROW, --firstrow FIRSTROW
                        Starting row of data to merge (not counting the header
                        row), first row by default.
  -to LASTROW, --lastrow LASTROW
                        Last row of data to merge (not counting the header
                        row), last row by default.
  -s, --save            Save current generator settings in (each) Scribus
                        input file(s).
  -l, --load            Load generator settings from (each) Scribus input
                        file(s). Overwrites all default values not provided
                        command line arguments.

requirements
    This program requires Python 2.7+

examples:
    
  ScribusGeneratorCLI.py my-template.sla
    Generates Scribus (SLA) files for each row of 'my-template.csv'
    by substituting the provided values into 'my-template.sla' in the 
    current directory.

  ScribusGeneratorCLI.py --outDir "/home/user/tmp" example/Business_Card.sla 
    Generates Scribus files for each row of example/Business_Card.csv
    in the "/home/user/tmp" subdirectory.

  ScribusGeneratorCLI.py --outName "card_%VAR_email%"  */*.sla 
    Generates Scribus files for each SLA file in any subdirectory
    that has a CSV file with a similar name in the same directory.
    Generated files will have a name constructed from the "email" field
    data, and are stored in their respective SLA file directory.

  ScribusGeneratorCLI.py --single -c translations.csv -n doc_  lang/*.sla 
    Generates a single Scribus file for each SLA file in the lang/ subdirectory
    using all records of the translations.csv data file.
    Generated files will have a name constructed from the "doc_" prefix
    and the input SLA file name.

 more information: https://github.com/berteh/ScribusGenerator/
```

More details
-------

### Clean output

ScribusGenerator will remove unused variables from the generated documents, along with the Text Frame that contains them, if that Text Frame contained nothing but variable(s).

![Illustration: Variables not substituted are removed](pic/SG_unusedVariables.png)

If you want to keep these unused variables and empty Text Frames, simply change the default setting accordingly in ```ScribusGeneratorBackend.py``` (setting ```CLEAN_UNUSED_EMPTY_VARS``` to 0).

Similarly, if these unused variables or empty texts were _preceded_ by a simple text (such as a single linefeed, or a character like any of ```,;-```), these list-like separators will be removed, so you can have a clean enumaration by appending your variables in a simple manner such as ```%VAR_n1%, %VAR_n2%, %VAR_n3%, %VAR_n4%.```, or in a more tabular layout using (single) linefeeds:
```
The following will turn out nicely even if some variable is empty or missing:
%VAR_n1%
%VAR_n2%
%VAR_n3%
%VAR_n4%
```

If you want to keep these separators, simply change the default setting accordingly in ```ScribusGeneratorBackend.py``` (setting ```REMOVE_CLEANED_ELEMENT_PREFIX``` to 0).

**Line breaks** and **tabulators** in your CSV data are replaced by the Scribus equivalent (new lines and tabulators). To remove them and turn them into simple spaces set the setting ```KEEP_TAB_LINEBREAK``` to 0.

### Logging and debugging

ScribusGenerator records all its actions in a log file located (by default) **in your user (home) directory**. If you encounter unexpected behaviour, check out the content of ```.scribusGenerator.log``` to find out more. You can change the logging settings in logging.conf (see [Python log configuration](https://docs.python.org/2/howto/logging.html#configuring-logging) for more options).

Kindly copy and paste the relevant (usually last) lines of your ```.scribusGenerator.log``` if you want to [report an issue](https://github.com/berteh/ScribusGenerator/issues).

### Variable Names

Try to use plain word characters (``A-Za-a0-9_``) for variable names, with no whitespaces or other special characters (like '&'). E.g. use ``%VAR_first_name%`` and ``%VAR_zip_code%`` instead of ``%VAR_first name%`` and ``%VAR_&zip#code%``. The columns of the data file (CSV) then would be ``first_name`` and ``zip_code``.  

This is only important for variable *names* in the Scribus file and *column names* of the data file. The data FIELDS (the rows of the CVS) may of course contain ANY characters that your character set supports.

### Database source

To use data from a database instead a (manual) spreadsheet you can simply export the related query result to a CSV file. Some examples below for common database engines. Find out more about using external data sources in our [wiki](https://github.com/berteh/ScribusGenerator/wiki) .

#### MySQL:

```mysql --delimiter="," -u myuser -p mydb -e "select f1,f2 from mytable" > /tmp/mydata.txt```

or

    mysql  -u myuser -p  mydatabase -e 
    "select field1 , field2 FROM mytable INTO OUTFILE 
    '/tmp/myfilename.csv' FIELDS TERMINATED BY ','
    ENCLOSED BY '\"' LINES TERMINATED BY '\n' "
    
More about INTO OUTFILE at http://dev.mysql.com/doc/refman/5.1/en/select.html

#### PostgreSQL

toggle unaligned output with the ```\a``` switch, activate a comma as a separator with ```\f ,```. Send output to a file with ```\o myfile.csv```, then query your database.
 
#### SQLite3

You can use ```sqlite3 -csv``` in command line or ```.mode csv``` in SQLite's interactive shell

#### Scripts

Various scripts are available in the ``utils`` folder to facilitate your use of ScribusGenerator.
Check out the [related README](https://github.com/berteh/ScribusGenerator/blob/master/utils/README.md) !

Known Issues
-------
### Mac OSX troubleshooting

Some installs of Python on Mac OSX do not ship a working Tkinter package, which is required for the ScribusGenerator GUI. Either find a way to set up a working TCL/Tk environment, or simply use the [Scribus Generator command line interface](#running-scribus-generator-from-the-command-line).

If you would like to contribute another GUI to ScribusGenerator that works under Mac OSX don't hesitate! Simply [fork, branch, code and pull a request](https://guides.github.com/activities/contributing-to-open-source/#contributing) to get your contribution reviewed!

Support
--------
Check out the [wiki](https://github.com/berteh/ScribusGenerator/wiki) for more ideas, look at the [solved](https://github.com/berteh/ScribusGenerator/issues?q=is%3Aissue+is%3Aclosed) and [open issues](https://github.com/berteh/ScribusGenerator/issues), and then kindly report an [issue](https://github.com/berteh/ScribusGenerator/issues) online, and paste the few last lines of your log file in there (it's ```.scribusGenerator.log``` inside your user (home) directory) to help find the reason of the unexpected behavior, along with a short explanation of your problem.


Licence
--------

The MIT License<br/>
Copyright <br/>
(c) 2011, Ekkehard Will (www.ekkehardwill.de)<br/>
(c) 2014-2021, Berteh (https://github.com/berteh/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: 

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. 

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealing in the software.
