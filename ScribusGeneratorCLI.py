#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Scribus Generator will
# - read CSV Data
# - convert a given Scribus File to a
# - specified Output Format (for each row of data) and
# - save the Output File as well as the generated Scribus File (which optional)
#
# For further information (manual, description, etc.) please visit:
# https://github.com/berteh/ScribusGenerator/
#
# v1.9 (2015-08-03): command-line support, missing pdf (how to launch + init scribus?)
#
"""
The MIT License
Copyright (c) 2014 Berteh (https://github.com/berteh/)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import argparse, sys, os, traceback
import ScribusGeneratorBackend
from ScribusGeneratorBackend import CONST, ScribusGenerator, GeneratorDataObject

#defaults
outDir = os.getcwd()

#parse options
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
    description=''' Generate Scribus and pdf documents automatically from external (csv) data.
 Mail-Merge-like extension to Scribus.''',  
    usage="%(prog)s [options] infiles+",
    epilog='''requirements
    This program requires Python 2.7+

examples:
    
  %(prog)s my-template.sla  --noPdf
    generates Scribus and PDF files for each line of 'my-template.csv'
    by subsituting the provides values into 'my-template.sla' to the 
    current directory.

  %(prog)s --verbose --fast --outDir "/home/user/tmp" example/Business_Card.sla 
    generates Scribus files for each line of example/Business_Card.csv
    in the "/home/user/tmp" subdirectory.

  %(prog)s --verbose --fast --outName "card_%%VAR_email%%"  */*.sla 
    generates Scribus files for each sla file in any subdirectory
    that has a csv file with a similar name in the same directory.
    Generated files will have a name constructed from the "email" field
    data, and are stored in their respective sla file directory.

  %(prog)s --single -c translations.csv -vfn doc_  lang/*.sla 
    generates a single Scribus file for each sla file in the lang/ subdirectory
    using all rows of the translations.csv data file.
    Generated files will have a name constructed from the "doc_" prefix
    and the input sla file name.


 more information: https://github.com/berteh/ScribusGenerator/
 ''')
parser.add_argument('infiles', nargs='+', 
    help='SLA file(s) to use as template(s) for the generation, wildcards are supported')
parser.add_argument('-c', '--csvFile', default=None, 
    help='CSV file containing the data to substitute in each template during generation. Default is scribus source file(s) name with "csv" extension instead of "sla". If csv file is not found, generation from this particular template is skipped.')
parser.add_argument('-d', '--csvDelimiter', default=CONST.CSV_SEP, 
    help='CSV field delimiter character. Default is comma: ","')
parser.add_argument('-f', '--fast', '--noPdf', action='store_true', default=False,
    help='no PDF generation, scribus SLA only (much faster)')
parser.add_argument('-n', '--outName', default=CONST.EMPTY, 
    help='name of the generated files, with no extension. Default is a simple incremental index.')
parser.add_argument('-o', '--outDir', default=None, 
    help='directory were generated files are stored. Default is the directory of the scribus source file. outputDir will be created if it does not exist.')
parser.add_argument('-p', '--pdfOnly', '--noSla', action='store_true', default=False,
    help='discard Scribus SLA, generate PDF only. This option is not used when --fast or --noPdf is used.')
parser.add_argument('-s', '--single', action='store_true', default=False,
    help='generate a single output (SLA and/or PDF) file that combines all data rows, for each source file.')
parser.add_argument('-v', '--verbose', action='store_true', default=False,
    help='print detailed progress information on the command line.')
parser.add_argument('-from', '--firstrow', default=None, type=int, dest='firstRow',
    help='Starting row of data to merge (not counting the header row), first row by default.')
parser.add_argument('-to', '--lastrow', default=None, type=int, dest='lastRow',
    help='Last row of data to merge (not counting the header row), last row by default.')


def message(*msg):
    """ Utility "print" function that handles verbosity of messages
    """
    if (args.verbose):
        print (''.join(msg))
    return

def ife(test, if_result, else_result):
    """ Utility if-then-else syntactic sugar
    """
    if(test):
        return if_result
    return else_result

#handle arguments
args = parser.parse_args()

if(args.pdfOnly or (not args.fast)):
    print ("PDF generation is currently not available from command line, but SLA is. Simply add the '--noPdf' option to your command and it will run just fine. ")
    sys.exit()

# create outDir if needed
if ((not(args.outDir is None)) and (not os.path.exists(args.outDir))):
    message('creating output directory: '+args.outDir)
    os.makedirs(args.outDir)

#generate
# Collect the settings made and build the Data Object
dataObject = GeneratorDataObject(   
    dataSourceFile = ife(not(args.csvFile is None), args.csvFile, CONST.EMPTY),
    outputDirectory = ife(not(args.outDir is None), args.outDir, CONST.EMPTY),
    outputFileName = args.outName,                                          # is CONST.EMPTY by default
    outputFormat = ife(args.fast, CONST.FORMAT_SLA, CONST.FORMAT_PDF),
    keepGeneratedScribusFiles = ife(args.pdfOnly, CONST.FALSE, CONST.TRUE), # not used if outputFormat is sla.
    csvSeparator = args.csvDelimiter,                                       # is CONST.CSV_SEP by default
    singleOutput = args.single,
    firstRow = args.firstRow,
    lastRow = args.lastRow)

generator = ScribusGenerator(dataObject)
message('ScribusGenerator is starting generation for '+str(len(args.infiles))+' template(s).')

for infile in args.infiles: 
    dataObject.setScribusSourceFile(infile)
    if(args.csvFile is None): # default data file is template-sla+csv
        dataObject.setDataSourceFile(os.path.splitext(infile)[0]+".csv") 
    if not(os.path.exists(dataObject.getDataSourceFile()) and os.path.isfile(dataObject.getDataSourceFile())):
        message('found no data file for '+os.path.split(infile)[1]+'. skipped.   was looking for '+dataObject.getDataSourceFile())
        continue #skip current template for lack of matching data.
    if(args.outDir is None): # default outDir is template dir
        dataObject.setOutputDirectory(os.path.split(infile)[0])
        if not os.path.exists(dataObject.getOutputDirectory()):
            message('creating output directory: '+dataObject.getOutputDirectory())
            os.makedirs(dataObject.getOutputDirectory())
    if(args.single and (len(args.infiles)>1)):
        dataObject.setOutputFileName(args.outName+'__'+os.path.split(infile)[1])
    message('generating all files for '+os.path.split(infile)[1]+' in directory '+dataObject.getOutputDirectory())
    try:
        generator.run()
        message('... done')
        message('Scribus Generation completed. Congrats!')
    except ValueError as e:
        print ("\nerror: could likely not replace a variable with its value.\nplease check your CSV data and CSV separator.\n       moreover: "+e.message+"\n")
    except IndexError as e:
        print ("\nerror: could likely not find the value for one variable.\nplease check your CSV data and CSV separator.\n       moreover: "+e.message+"\n")
    except Exception:
        print ("\nerror: "+traceback.format_exc())
