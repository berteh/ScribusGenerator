#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

=================
Automatic document generation for Scribus.
=================

For further information (manual, description, etc.) please visit:
http://berteh.github.io/ScribusGenerator/

# v3.0 (2022-01-12): port to Python3 for Scribut 1.5.6+, some features (count, fill)
# v2.0 (2015-12-02): added features (merge, range, clean, save/load)
# v1.9 (2015-08-03): initial command-line support (SLA only, use GUI version to generate PDF)

This script is the Command Line ScribusGenerator

=================
The MIT License
=================

Copyright (c) 2010-2014 Ekkehard Will (www.ekkehardwill.de), 2014-2022 Berteh (https://github.com/berteh/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
import sys
import os
import traceback
import ScribusGeneratorBackend
from ScribusGeneratorBackend import CONST, ScribusGenerator, GeneratorDataObject

# defaults
outDir = os.getcwd()

# parse options
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=''' Generate Scribus (SLA) documents automatically from external (csv) data.
 Mail-Merge-like extension to Scribus.''',
                                 usage="%(prog)s [options] infiles+",
                                 epilog='''requirements
    This program requires Python 3.0+

examples:

  %(prog)s my-template.sla
    generates Scribus (SLA) files for each line of 'my-template.csv'
    by substituting the provides values into 'my-template.sla' to the 
    current directory.

  %(prog)s --outDir "/home/user/tmp" example/Business_Card.sla
    generates Scribus files for each line of example/Business_Card.csv
    in the "/home/user/tmp" subdirectory.

  %(prog)s --outName "card-%%VAR_COUNT%%-%%VAR_email%%"  */*.sla
    generates Scribus files for each sla file in any subdirectory
    that has a csv file with a similar name in the same directory.
    Generated files will have a name constructed from the entry position
    and "email" field, and are stored in their respective sla file directory.

  %(prog)s --single -c translations.csv -n doc_  lang/*.sla
    generates a single Scribus file for each sla file in the lang/ subdirectory
    using all rows of the translations.csv data file.
    Generated files will have a name constructed from the "doc_" prefix
    and the input sla file name.


 more information: https://github.com/berteh/ScribusGenerator/
 ''')
parser.add_argument('infiles', nargs='+',
                    help='SLA file(s) to use as template(s) for the generation, wildcards are supported')
parser.add_argument('-c', '--dataFile', default=None,
                    help='CSV/JSON data file containing the data to substitute in each template during generation. Default is scribus source file(s) name with "csv" extension instead of "sla". If csv file is not found, generation from this particular template is skipped.')
parser.add_argument('-d', '--csvDelimiter', default=CONST.CSV_SEP,
                    help='CSV field delimiter character. Default is comma: ","')
parser.add_argument('-e', '--csvEncoding', default=CONST.CSV_ENCODING,
                    help='Encoding of the CSV file (default: utf-8)')
# parser.add_argument('-f', '--fast', '--noPdf', action='store_true', default=False, # commented utile Scribus allows pdf generation from command line
#    help='no PDF generation, scribus SLA only (much faster)')
parser.add_argument('-n', '--outName', default=CONST.EMPTY,
                    help='name of the generated files, with no extension. Default is a simple incremental index. Using SG variables is allowed to define the name of generated documents. Use %VAR_COUNT% as a unique counter defined automatically from the data entry position.')
parser.add_argument('-o', '--outDir', default=None,
                    help='directory were generated files are stored. Default is the directory of the scribus source file. outputDir will be created if it does not exist.')
# parser.add_argument('-p', '--pdfOnly', '--noSla', action='store_true', default=False, # for pdf from CLI
#    help='discard Scribus SLA, generate PDF only. This option is not used when --fast or --noPdf is used.')
parser.add_argument('-m', '--merge', '--single', action='store_true', default=False,
                    help='generate a single output (SLA) file that combines all data rows, for each source file.')
parser.add_argument('-from', '--firstrow', default=CONST.EMPTY, dest='firstRow',
                    help='Starting row of data to merge (not counting the header row), first row by default.')
parser.add_argument('-to', '--lastrow', default=CONST.EMPTY, dest='lastRow',
                    help='Last row of data to merge (not counting the header row), last row by default.')
parser.add_argument('-s', '--save', action='store_true', default=False,
                    help='Save current generator settings in (each) Scribus input file(s).')
parser.add_argument('-l', '--load', action='store_true', default=False,
                    help='Load generator settings from (each) Scribus input file(s). Overloads all options (but -h).')


def ife(test, if_result, else_result):
    """ Utility if-then-else syntactic sugar
    """
    if(test):
        return if_result
    return else_result


# handle arguments
args = parser.parse_args()

# if(args.pdfOnly or (not args.fast)): # for pdf from CLI
#     print("\nPDF generation is currently not available from command line, but SLA is. \nSimply add the '--noPdf' option to your command and it will run just fine.\n")
#    sys.exit()

# create outDir if needed
if ((not(args.outDir is None)) and (not os.path.exists(args.outDir))):
    #print('creating output directory: '+args.outDir)
    os.makedirs(args.outDir)

# generate
# Collect the settings made and build the Data Object
dataObject = GeneratorDataObject(
    dataSourceFile=ife(not(args.dataFile is None), args.dataFile, CONST.EMPTY),
    outputDirectory=ife(not(args.outDir is None), args.outDir, CONST.EMPTY),
    outputFileName=args.outName,    # is CONST.EMPTY by default
    # ife(args.fast, CONST.FORMAT_SLA, CONST.FORMAT_PDF),
    outputFormat=CONST.FORMAT_SLA,
    # ife(args.pdfOnly, CONST.FALSE, CONST.TRUE), # not used if outputFormat is sla.
    keepGeneratedScribusFiles=CONST.TRUE,
    csvSeparator=args.csvDelimiter,  # is CONST.CSV_SEP by default
    csvEncoding=args.csvEncoding, # is CONST.CSV_ENCODING by default
    singleOutput=args.merge,
    firstRow=args.firstRow,
    lastRow=args.lastRow,
    saveSettings=args.save)

generator = ScribusGenerator(dataObject)
log = generator.get_log()
log.debug("ScribusGenerator is starting generation for %s template(s)." %
          (str(len(args.infiles))))

for infile in args.infiles:
    dataObject.setScribusSourceFile(infile)

    if(args.load):
        saved = generator.get_saved_settings()

        if (saved):
            dataObject.loadFromString(saved)
            log.info("settings loaded from %s:" % (os.path.split(infile)[1]))

        else:
            log.warning("could not load settings from %s. using arguments and defaults instead" % (
                os.path.split(infile)[1]))

    if(dataObject.getDataSourceFile() is CONST.EMPTY):  # default data file is template-sla+csv
        dataObject.setDataSourceFile(os.path.splitext(infile)[0]+".csv")
    if not(os.path.exists(dataObject.getDataSourceFile()) and os.path.isfile(dataObject.getDataSourceFile())):
        log.warning("found no data file for %s. skipped.   was looking for %s" % (
            os.path.split(infile)[1], dataObject.getDataSourceFile()))
        continue  # skip current template for lack of matching data.
    if(dataObject.getOutputDirectory() is CONST.EMPTY):  # default outDir is template dir
        dataObject.setOutputDirectory(os.path.split(infile)[0])
        if not os.path.exists(dataObject.getOutputDirectory()):
            log.info("creating output directory: %s" %
                     (dataObject.getOutputDirectory()))
            os.makedirs(dataObject.getOutputDirectory())
    if(dataObject.getSingleOutput() and (len(args.infiles) > 1)):
        dataObject.setOutputFileName(
            args.outName+'__'+os.path.split(infile)[1])
    log.info("Generating all files for %s in directory %s" %
             (os.path.split(infile)[1], dataObject.getOutputDirectory()))
    try:
        generator.run()
        log.info("Scribus Generation completed. Congrats!")
    except ValueError as e:
        log.error("\nerror: could likely not replace a variable with its value.\nplease check your CSV data and CSV separator.       moreover: %s\n\n" % e)
        traceback.print_exc()
    except IndexError as e:
        log.error("\nerror: could likely not find the value for one variable.\nplease check your CSV data and CSV separator.\n       moreover: %s\n" % e)
        traceback.print_exc
    except Exception:
        log.error("\nerror: "+traceback.format_exc())
        traceback.print_exc
