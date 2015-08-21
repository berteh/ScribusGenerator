ScribusGenerator
================

Mail-Merge-like extension to Scribus, to generate Scribus and pdf documents automatically from external data.


What about Scribus?
--------

[Scribus](http://www.scribus.net/) is a desktop publishing (DTP) application, which is free software and released under the GNU General Public License ([http://www.scribus.net](http://www.scribus.net/)).

It is available for Linux, Unix-like, Mac OS X, OS/2, and Microsoft Windows. Known for its broad set of page layout features, it is comparable to leading non-free applications such as Adobe PageMaker, PagePlus, QuarkXPress or Adobe InDesign.

Scribus is designed for flexible layout and typesetting and the ability to prepare files for professional quality image setting equipment. It can also create animated and interactive PDF presentations and forms. Example uses include writing small newspapers, brochures, newsletters, posters and books.

What is Scribus Generator?
-------

Scribus comes with a broad set of page layout features and functionality. One feature missing is to replace text with data dynamically. This kind of feature you may already know as the typical __mail merge__ functionality in your preferred office application.

**Scribus Generator** fills this lack of functionality. **Scribus Generator** in general is an extension to replace text with data to automatic generated files (e.g. SLA, PDF). It has been written by [Ekkehard Will](http://www.ekkehardwill.de/sg/) and further extended by [Berteh](https://github.com/berteh/).

**Scribus Generator** is implemented as a Python script. It simply can be started by choosing the script (``ScribusGenerator.py``) within the dialog: _«Scribus → Script → Execute Script»_.

[Download](https://github.com/berteh/ScribusGenerator/archive/master.zip) the script and uncompress it anywhere on the local machine. It can be placed with  the standard extension scripts. On Windows platform this location would be ``SCRIBUS_INSTALL_DIRECTORY\share\scripts\``, on Ubuntu ``/usr/share/scribus/scripts/``.

A [short *how to* video](https://www.youtube.com/embed/kMsRn38TOiQ) introduces this Scribus Generator. 6 first minutes for the basic overview, 12 last for more advanced features.


[![Scribus Generator how to - high quality pdf generatio](pic/screencast.png)](https://www.youtube.com/embed/kMsRn38TOiQ)


The Scribus "template" file
------

Create and design your Scribus file as any other. At the positions where you need to replace text with data, just add ``%VAR_name%`` where ``name`` is the column in the data table.

You can place the variable at any position within a Text Frame. Apply all format and style to the variable that you wish to apply to the final text.

![Illustration: Scribus File for Generator](pic/SG-01.png)


The (csv) Data File
--------

**Scribus Generator** expects a CSV file (_Comma Separated Values_), which is very simple to create. Open a spread sheet editor (such as [LibreOffice](http://www.libreoffice.org/) or Excel), enter the data and save/export as CSV. UTF-8 encoding is recommended.

![Illustration: Data File for Generator](pic/SG-05.png)

As you can see, the columns have the same ``name`` as variables (``%VAR_name%``) referenced in the Sribus file you have designed.


Run the Generator Script - Settings
---------

Run the script via the menu: ``Script > execute Script`` and launch ``ScribusGenerator.py``.

In the script dialog you can configure the input and output settings for **Scribus Generator**.

![Illustration: Input and Output Settings](pic/SG-10.png)

| Setting | explanation |
| ---- | ---- |
| **Scribus File** | Choose the Scribus File containing the variables to replace. |
| **Data File** | Choose the Data File containing the comma separated values. |
| **Output Directory** | Choose the path to an existing directory where to save the result. |
| **Output File Name** | You can use the same variables as defined in the Scribus File/Data File. You can also mix the variables with other characters. If you leave the field empty an index will be used. The index/resulting files will be sorted according to the occurrence of rows in the Data File. |
| **Ouput Format** | Choose the Output Format of the generated files, either PDF or Scribus. |
| **Keep Scribus Files** | Select to keep the generated Scribus Files. Otherwise they will be deleted after pdf generation. This option has no effect if you choose Scribus output format.|
| **Merge Output in Single File** | Select to  generate a single output (SLA and/or PDF) file that combines all data rows. |


Dynamic Images
------------

Images references can also be dynamically modified with **Scribus Generator**. See the [screencast video @6:10](https://www.youtube.com/watch?feature=player_detailpage&v=kMsRn38TOiQ#t=370).

All images supported by **Scribus** can be used. However, to work with ScribusGeneratr, they must all be located in a single folder containing all images. This folder can be located anywhere on your PC.

Add an Image Frame anywhere in the Scribus file (_«Scribus → Insert → Insert Image Frame»_) and open the dialog for getting an image (_e.g. right click Image Frame → Get Image..._ on selected frame). Within the dialog navigate to the folder containing the images, though there won't be any images selected. Instead, the variable will be inserted into the value field of the _File name_.

![Illustration: Insert variable instead of image](pic/SG-15-1.png)

After confirming the dialog, no image is displayed in the Image Frame any longer, however the variable name can be seen.

![Illustration: Image Frame containing variable](pic/SG-15-2.png)

The images file can be defined just like any other variable described in earlier. There just has to be a column with a column-name corresponding to the variable-name in the Scribus template file.

![Illustration: Data file referencing images](pic/SG-15-3.png)

Dynamic Colors
---------------

Colors can be dynamically replaced just like text. See the [screencast video @8:31](https://www.youtube.com/watch?feature=player_detailpage&v=kMsRn38TOiQ#t=512), or simply 

1. edit the colors of your Scribus file (``edit > colours``) and rename the colors you want to replace with variable names (typically replace ``FromSVG#whatever`` with the now well known form ``%VAR_name%``).
1. define the colors you want to use in the final document, and use their Scribus names as values in your color data field. 

![Illustration: Replace colors dynamically](pic/SG-16.png)

Merged output - single document
------------
Instead of generating a single (sla or pdf) file for each data row, you can generate a single file that merges all these. Simply select the option accordingly to get the result illustrated below in a single Scribus (and/or pdf) file.

![Illustration: Single ouput to merge all generated files](pic/mergedSLA.png)

More advanced uses
-----------
Scribus Generator allows more tech-savvy users you to customize the generated documents even more, changing virtually any attribute of any object, such as the fill or outline color of a line, the color of some text, a line thickness, an object position,... See the [screencast video @13:13](https://www.youtube.com/watch?feature=player_detailpage&v=kMsRn38TOiQ#t=793).

To change the color of an object, add an *attribute* to it (_«righ-click on object → Attributes → Add »_). The **type** attribute must be set to [``SGAttribute``][1], it's **name** to the [object property][2] you want to change and its **value** to the desired dynamic value (typically ``%VAR_name%``).

![Illustration: Use Attributes to modify advanced object properties](pic/SG-20.png "Use Attributes to modify advanced object properties")

To change the properties of a sub-element (such as the text lines in a text frame), you may use the **parameter** field to define which sub-elements should receive the new property. Use ``*`` to modify all direct children, or any other [simplified XPATH expression][3] to modify only a subset.

### Selected examples of SGAttributes:

| Name | Type | Value | Parameter | Explanation 
| --- | --- | --- | --- | --- |
| ``FONT`` | ``SGAttribute`` | ``%VAR_font%`` | ``//ITEXT[2]`` | Font of the 2d text line in a frame, like "Arial Regular"
| ``FONTSIZE`` | ``SGAttribute`` | ``%VAR_size%`` | ``//ITEXT`` | Text size all text lines in a frame, like "14" 
| ``YPOS`` | ``SGAttribute`` | ``%VAR_top%`` |  | Margin from the top for vertical element position, like "22.04"


[1]: # "SGAttribute is short for 'Scribus Generator Attribute'"
[2]: http://wiki.scribus.net/canvas/File_Format_Specification_for_Scribus_1.4#Tags "Object property is expressed in the exact SLA syntax"
[3]: https://docs.python.org/2/library/xml.etree.elementtree.html#supported-xpath-syntax "The reduced set of XPATH expressions valid in the 'parameter' field is defined in the ElementTree XPath support documentation."
[4]: simply use the color name as defined in your Scribus file colours (``edit > Colours``).

Running Scribus Generator from the command line
---------
It is possible to run Scribus Generator from the command line. Great to automate your workflow or integrate with other tools!
Note only the SLA generation works from the command line. PDF generation is at the moment impossible (from the Scribus Generator command line) due to Scribus limitations.

Find all needed information from the script help: ``./ScribusGeneratorCLI.py --help``

    positional arguments:
      infiles               SLA file(s) to use as template(s) for the generation,
                            wildcards are supported

    optional arguments:
      -h, --help            show this help message and exit
      -c CSVFILE, --csvFile CSVFILE
                            CSV file containing the data to substitute in each
                            template during generation. Default is scribus source
                            file(s) name with "csv" extension instead of "sla". If
                            csv file is not found, generation from this particular
                            template is skipped.
      -d CSVDELIMITER, --csvDelimiter CSVDELIMITER
                            CSV field delimiter character. Default is comma: ","
      -f, --fast, --noPdf   no PDF generation, scribus SLA only (much faster)
      -n OUTNAME, --outName OUTNAME
                            name of the generated files, with no extension.
                            Default is a simple incremental index.
      -o OUTDIR, --outDir OUTDIR
                            directory were generated files are stored. Default is
                            the directory of the scribus source file. outputDir
                            will be created if it does not exist.
      -p, --pdfOnly, --noSla
                            discard Scribus SLA, generate PDF only. This option is
                            not used when --fast or --noPdf is used.
      -s, --Single          generate a single output (SLA and/or PDF) file that
                            combines all data rows, for each source file.
      -v, --verbose         print detailed progress information on the command
                            line.

    requirements
    	This program requires Python 2.7+, and Scribus 1.4.+ for PDF generation only.

    examples:
    	
      ScribusGeneratorCLI.py my-template.sla
     	generates Scribus and PDF files for each line of 'my-template.csv'
     	by subsituting the provides values into 'my-template.sla' to the 
     	current directory.

      ScribusGeneratorCLI.py --verbose --fast --outDir "/home/user/tmp" example/Business_Card.sla 
      	generates Scribus files for each line of example/Business_Card.csv
      	in the "/home/user/tmp" subdirectory.

      ScribusGeneratorCLI.py --verbose --fast --outName "card_%VAR_email%"  */*.sla 
    	generates Scribus files for each sla file in any subdirectory
    	that has a csv file with a similar name in the same directory.
    	Generated files will have a name constructed from the "email" field
    	data, and are stored in their respective sla file directory.



Known Issues
-------

### MacOS/X troubleshooting

Some install of Python on MacOS/X do not ship Tk, that is required for ScribusGenerator GUI. Either find a way to setup a compliant Tk environment, or simply use the Scribus Generator command line interface.

If you would like to contribute another GUI to Scribus Generator that works in MacOS/X don't hesitate!

### Variable Names

If possible, use plain characters (ASCII) for variable names and do not use whitespaces and other special characters (like '&'). E.g. use ``%VAR_first_name%`` and ``%VAR_zip_code%`` instead of ``%VAR_first name%`` and ``%VAR_&zip#code%``.
The columns of the data file (CSV) then would be ``first_name`` and ``zip_code``.		

**Note**: This is only important for variable names in the scribus file and column names of the data file. The data FIELDS (the rows of the CVS) of course may contain ANY characters.



Licence
--------

The MIT License<br/>
Copyright <br/>
(c) 2011, Ekkehard Will (www.ekkehardwill.de)<br/>
(c) 2014, Berteh (https://github.com/berteh/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: 

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. 

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealing in the software.
