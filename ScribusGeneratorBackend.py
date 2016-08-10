#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Mail-Merge for Scribus.
#
# For further information (manual, description, etc.) please visit:
# https://github.com/berteh/ScribusGenerator/
#
# v2.2 (2016-08-10): various bug fix (logging location in windows, dynamic colors in Scribus 1.5.2 and some more)
# v2.0 (2015-12-02): added features (merge, range, clean, save/load)
# v1.9 (2015-08-03): initial command-line support (SLA only, use GUI version to generate PDF)
# v1.1 (2014-10-01): Add support for overwriting attributes from data (eg text/area color)
# v1.0 (2012-01-07): Fixed problems when using an ampersand as values within CSV-data.
# v2011-01-18: Changed run() so that scribus- and pdf file creation and deletion works without problems.
# v2011-01-17: Fixed the ampersand ('&') problem. It now can be used within variables.
# v2011-01-01: Initial Release.
#
"""
The MIT License
Copyright (c) 2010-2014 Ekkehard Will (www.ekkehardwill.de), 2014-2015 Berteh (https://github.com/berteh/)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import csv
import os
import logging
import logging.config
#import traceback
import sys
import xml.etree.ElementTree as ET  # common Python xml implementation
import json
import re

class CONST:
    # Constants for general usage
    TRUE = 1
    FALSE = 0
    EMPTY = ''
    APP_NAME = 'Scribus Generator'
    FORMAT_PDF = 'PDF'
    FORMAT_SLA = 'Scribus'
    FILE_EXTENSION_PDF = 'pdf'
    FILE_EXTENSION_SCRIBUS = 'sla'
    SEP_PATH = '/'  # In any case we use '/' as path separator on any platform
    SEP_EXT = os.extsep    
    CSV_SEP = "," # CSV entry separator, comma by default; tab: "	" is also common if using Excel.
    CONTRIB_TEXT = "\npowered by ScribusGenerator - https://github.com/berteh/ScribusGenerator/"
    STORAGE_NAME = "ScribusGeneratorDefaultSettings"
    REMOVE_EMPTY_LINES = 1 # set to 0 to prevent removal of un-subsituted variables, along with their empty containing itext
    KEEP_TAB_LINEBREAK = 1 # set to 0 to replace all tabs and linebreaks in csv data by simple spaces.

    
class ScribusGenerator:
    # The Generator Module has all the logic and will do all the work
    def __init__(self, dataObject):
        self.__dataObject = dataObject
        logging.config.fileConfig(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.conf'))
        # todo: check if logging works, if not warn user to configure log file path and disable.
        logging.info("ScribusGenerator initialized")

    
    def run(self):
        # Read CSV data and replace the variables in the Scribus File with the cooresponding data. Finaly export to the specified format.
        # may throw exceptions if errors are met, use traceback to get all error details
        
        #defaults for missing info
        if(self.__dataObject.getSingleOutput() and (self.__dataObject.getOutputFileName() is CONST.EMPTY)):
            self.__dataObject.setOutputFileName(os.path.split(os.path.splitext(self.__dataObject.getScribusSourceFile())[0])[1] +'__single')    

        #parsing
        logging.info("parsing data source file %s"%(self.__dataObject.getDataSourceFile()))
        try:
            csvData = self.getCsvData(self.__dataObject.getDataSourceFile())
        except IOError as e:
            logging.error("CSV file not found: %s"%(self.__dataObject.getDataSourceFile()))
            raise             
        if(len(csvData) < 1):
            logging.error("Data file %s is empty. At least a header line and a line of data is needed. Halting."%(self.__dataObject.getDataSourceFile()))
            return -1
        if(len(csvData) < 2):
            logging.error("Data file %s has only one line. At least a header line and a line of data is needed. Halting."%(self.__dataObject.getDataSourceFile()))
            return -1

        #range
        firstElement = 1
        if(self.__dataObject.getFirstRow() != CONST.EMPTY):
            try:
                newFirstElementValue = int(self.__dataObject.getFirstRow())
                firstElement = max(newFirstElementValue, 1) # Guard against 0 or negative numbers
            except:
                logging.warning("Could not parse value of 'first row' as an integer, using default value instead")
        lastElement = len(csvData)
        if(self.__dataObject.getLastRow() != CONST.EMPTY):
            try:
                newLastElementValue = int(self.__dataObject.getLastRow())
                lastElement = min(newLastElementValue + 1, lastElement) # Guard against numbers higher than the length of csvData
            except:
                logging.warning("Could not parse value of 'last row' as an integer, using default value instead")       
        if ( (firstElement != 1) or (lastElement != len(csvData)) ):
            csvData = csvData[0:1] + csvData[firstElement : lastElement]

        #generation
        dataC = len(csvData)-1
        fillCount = len(str(dataC))
        template = [] # XML-Content/Text-Content of the Source Scribus File (List of Lines)
        outputFileNames = []
        index = 0
        # Generate the Scribus Files
        for row in csvData:
            if(index == 0): # first line is the Header-Row of the CSV-File                
                varNamesForFileName = row
                varNamesForReplacingVariables = self.handleAmpersand(row) # Header-Row contains the variable names
                logging.info("parsing scribus source file %s"%(self.__dataObject.getScribusSourceFile()))
                try:
                    tree = ET.parse(self.__dataObject.getScribusSourceFile())
                except IOError as e:
                    logging.error("Scribus file not found: %s"%(self.__dataObject.getScribusSourceFile()))
                    raise
                root = tree.getroot()                
                # overwrite attributes from their /*/ItemAttribute[Type=SGAttribute] sibling, when applicable.
                templateElt = self.overwriteAttributesFromSGAttributes(root)                 

                #save settings
                if (self.__dataObject.getSaveSettings()):                                    
                    serial=self.__dataObject.toString()
                    logging.debug("saving current Scribus Generator settings in your source file")# as: %s"%serial)
                    docElt = root.find('DOCUMENT')
                    storageElt = docElt.find('./JAVA[@NAME="'+CONST.STORAGE_NAME+'"]')
                    if (storageElt is None):
                        colorElt = docElt.find('./COLOR[1]')                     
                        scriptPos = docElt.getchildren().index(colorElt)
                        logging.debug("creating new storage element in SLA template at position %s"%scriptPos)
                        storageElt = ET.Element("JAVA", {"NAME":CONST.STORAGE_NAME})
                        docElt.insert(scriptPos, storageElt)
                    storageElt.set("SCRIPT",serial)
                    tree.write(self.__dataObject.getScribusSourceFile()) #todo check if scribus reloads (or overwrites :/ ) when doc is opened, opt use API to add a script if there's an open doc.

               
            else:
                outContent = self.replaceVariablesWithCsvData(varNamesForReplacingVariables, self.handleAmpersand(row), ET.tostring(templateElt, method='xml').split('\n'), keepTabsLF=CONST.KEEP_TAB_LINEBREAK)                
                # using capturing parenthesis in re.split pattern above to make sure the closing '>' is included in the splitted array.
                if (self.__dataObject.getSingleOutput()):
                    if (index == 1):
                        logging.debug("generating reference content from row #1")                        
                        outputElt = ET.fromstring(outContent)
                        docElt = outputElt.find('DOCUMENT')  
                        pagescount = int(docElt.get('ANZPAGES'))
                        pageheight = float(docElt.get('PAGEHEIGHT'))
                        vgap = float(docElt.get('GapVertical'))
                        groupscount = int(docElt.get('GROUPC'))
                        objscount = len(outputElt.findall('.//PAGEOBJECT'))
                        logging.debug("current template has #%s pageobjects"%(objscount))
                        version = outputElt.get('Version')
#                        if version.startswith('1.4'):
#                            docElt.set('GROUPC', str(groupscount*dataC))
                        docElt.set('ANZPAGES', str(pagescount*dataC))                        
                        docElt.set('DOCCONTRIB',docElt.get('DOCCONTRIB')+CONST.CONTRIB_TEXT)
                    else:
                        logging.debug("merging content from row #%s"%(index))
                        tmpElt = ET.fromstring(outContent).find('DOCUMENT')
                        shiftedElts = self.shiftPagesAndObjects(tmpElt, pagescount, pageheight, vgap, index-1, groupscount, objscount, version)                        
                        docElt.extend(shiftedElts)                                                
                else: # write one of multiple sla
                    outputFileName = self.createOutputFileName(index, self.__dataObject.getOutputFileName(), varNamesForFileName, row, fillCount)                    
                    self.writeSLA(ET.fromstring(outContent), outputFileName)
                    outputFileNames.append(outputFileName)                    
            index = index + 1
        
        # clean & write single sla
        if (self.__dataObject.getSingleOutput()):            
            self.writeSLA(outputElt, self.__dataObject.getOutputFileName())
            outputFileNames.append(self.__dataObject.getOutputFileName())        

        # Export the generated Scribus Files as PDF
        if(CONST.FORMAT_PDF == self.__dataObject.getOutputFormat()):
            for outputFileName in outputFileNames:
                pdfOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_PDF)
                scribusOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                self.exportPDF(scribusOutputFilePath, pdfOutputFilePath)
                logging.info("pdf file created: %s"%(pdfOutputFilePath))
        
        # Cleanup the generated Scribus Files
        if(not (CONST.FORMAT_SLA == self.__dataObject.getOutputFormat()) and CONST.FALSE == self.__dataObject.getKeepGeneratedScribusFiles()):
            for outputFileName in outputFileNames:
                scribusOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                self.deleteFile(scribusOutputFilePath)

        return 1;
      
            

    def exportPDF(self, scribusFilePath, pdfFilePath):
        import scribus
        
        d = os.path.dirname(pdfFilePath)
        if not os.path.exists(d):
            os.makedirs(d)
      
        # Export to PDF
        scribus.openDoc(scribusFilePath)
        listOfPages = []
        i = 0
        while (i < scribus.pageCount()):
            i = i + 1
            listOfPages.append(i)
            
        pdfExport = scribus.PDFfile()
        pdfExport.info = CONST.APP_NAME
        pdfExport.file = str(pdfFilePath)
        pdfExport.pages = listOfPages
        pdfExport.save()
        scribus.closeDoc()

    def writeSLA(self, slaET, outFileName, clean=CONST.REMOVE_EMPTY_LINES):
        # write SLA to filepath computed from given elements, optionnaly cleaning empty ITEXT elements and their empty PAGEOBJECTS
        scribusOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outFileName, CONST.FILE_EXTENSION_SCRIBUS)
        d = os.path.dirname(scribusOutputFilePath)
        if not os.path.exists(d):
            os.makedirs(d)
        outTree = ET.ElementTree(slaET) 
        if (clean):
            self.removeEmptyTexts(outTree.getroot())
        outTree.write(scribusOutputFilePath, encoding="UTF-8")
        logging.info("scribus file created: %s"%(scribusOutputFilePath)) 
        return scribusOutputFilePath


    def overwriteAttributesFromSGAttributes(self, root):
        # modifies root such that
        # attributes have been rewritten from their /*/ItemAttribute[Type=SGAttribute] sibling, when applicable.
        #
        # allows to use %VAR_<var-name>% in Item Attribute to overwrite internal attributes (eg FONT)   

        for pageobject in root.findall(".//ItemAttribute[@Type='SGAttribute']/../.."):
            sga = pageobject.find(".//ItemAttribute[@Type='SGAttribute']")            
            attribute = sga.get('Name')            
            value = sga.get('Value')  
            param = sga.get('Parameter')
                  
            if param is "": # Cannot use 'default' on .get() as it is "" by default in SLA file.
                param = "." # target is pageobject by default. Cannot use ".|*" as not supported by ET.
            elif param.startswith("/"): # ET cannot use absolute path on element 
                param = "."+param 

            try:
                targets = pageobject.findall(param)
                if targets :
                    for target in targets :
                        logging.debug('overwriting value of %s in %s with "%s"'%(attribute, target.tag, value))
                        target.set(attribute,value)
                else :
                    logging.error('Target "%s" could be parsed but designated no node. Check it out as it is probably not what you expected to replace %s.'%(param, attribute)) #todo message to user
                    
            except SyntaxError:
                logging.error('XPATH expression "%s" could not be parsed by ElementTree to overwrite %s. Skipping.'%(param, attribute)) #todo message to user

        return root


    def shiftPagesAndObjects(self, docElt, pagescount, pageheight, vgap, index, groupscount, objscount, version):
        shifted = []
        voffset = (float(pageheight)+float(vgap)) * index
        for page in docElt.findall('PAGE'):
            page.set('PAGEYPOS', str(float(page.get('PAGEYPOS')) + voffset))
            page.set('NUM', str(int(page.get('NUM')) + pagescount))
            shifted.append(page)
        for obj in docElt.findall('PAGEOBJECT'):
            obj.set('YPOS', str(float(obj.get('YPOS')) + voffset))
            obj.set('OwnPage', str(int(obj.get('OwnPage')) + pagescount))            
            #update ID and links
            if version.startswith('1.4'):
#                if not (int(obj.get('NUMGROUP')) == 0):
#                    obj.set('NUMGROUP', str(int(obj.get('NUMGROUP')) + groupscount * index))
                if (obj.get('NEXTITEM') != None and (str(obj.get('NEXTITEM')) != "-1")): # next linked frame by position                
                    obj.set('NEXTITEM', str(int(obj.get('NEXTITEM')) + (objscount * index)))
                if (obj.get('BACKITEM') != None and (str(obj.get('BACKITEM')) != "-1")): # previous linked frame by position
                    obj.set('BACKITEM', str(int(obj.get('BACKITEM')) + (objscount * index)))
            else : #1.5, 1.6
                logging.debug("shifting object %s (#%s)"%(obj.tag, obj.get('ItemID')))
                
                obj.set('ItemID', str(objscount * index) + str(int(obj.get('ItemID')))[3:] ) # update ID with something unlikely allocated, todo ensure unique ID.
                if (obj.get('NEXTITEM') != None and (str(obj.get('NEXTITEM')) != "-1")): # next linked frame by ItemID                       
                    obj.set('NEXTITEM', str(objscount * index) + str(int(obj.get('NEXTITEM')))[3:] )
                if (obj.get('BACKITEM') != None and (str(obj.get('BACKITEM')) != "-1")): # previous linked frame by ItemID    
                    obj.set('BACKITEM', str(objscount * index) + str(int(obj.get('BACKITEM')))[3:] )

            shifted.append(obj)
        logging.debug("shifted page %s element of %s"%(index,voffset))
        return shifted

    def removeEmptyTexts(self, root):
        # *modifies* root ElementTree by removing empty text elements and their empty placeholders.
        # returns number of ITEXT elements deleted.
        #   1. clean text in which some variable-like text is not substituted (ie: known or unknown variable):
        #      <ITEXT CH="empty %VAR_empty% variable should not show" FONT="Arial Regular" />
        #   2. remove <ITEXT> with empty @CH
        #   3. remove any <PAGEOBJECT> that has no <ITEXT> child left
        emptyXPath = "ITEXT[@CH='']"
        d = 0
        for page in root.findall(".//%s/../.." %emptyXPath): #little obscure because its parent is needed to remove an element, and ElementTree has no parent() method.
            for po in page.findall(".//%s/.." %emptyXPath):
                for emptyItext in po.findall("./%s" %emptyXPath):
                    logging.debug("cleaning 1 empty ITEXT")                    
                    po.remove(emptyItext)
                    d += 1
                if (len(po.findall("ITEXT")) is 0):
                    logging.debug("cleaning 1 empty PAGEOBJECT")
                    page.remove(po)                 
        logging.debug("removed %d empty ITEXTs"%d)
        return d
    
    def deleteFile(self, outputFilePath):
        # Delete the temporarily generated files from off the file system
        os.remove(outputFilePath)

    def createOutputFilePath(self, outputDirectory, outputFileName, fileExtension):
        # Build the absolute path, like C:/tmp/template.sla
        return outputDirectory + CONST.SEP_PATH + outputFileName + CONST.SEP_EXT + fileExtension
    
    def createOutputFileName(self, index, outputFileName, varNames, row, fillCount):
        # If the User has not set an Output File Name, an internal unique file name
        # will be generated which is the index of the loop.
        result = str(index)
        result = result.zfill(fillCount)
        # Following characters are not allowed for File-Names on WINDOWS: < > ? " : | \ / *
        if(CONST.EMPTY != outputFileName):
                table = {
                         #ord(u'ä'): u'ae',
                         #ord(u'Ä'): u'Ae',
                         #ord(u'ö'): u'oe',
                         #ord(u'Ö'): u'Oe',
                         #ord(u'ü'): u'ue',
                         #ord(u'Ü'): u'Ue',
                         #ord(u'ß'): u'ss',
                         ord(u'<'): u'_',
                         ord(u'>'): u'_',
                         ord(u'?'): u'_',
                         ord(u'"'): u'_',
                         ord(u':'): u'_',
                         ord(u'|'): u'_',
                         ord(u'\\'): u'_',
                         ord(u'/'): u'_',
                         ord(u'*'): u'_'
                     }
                result = self.replaceVariablesWithCsvData(varNames, [row], [outputFileName])
                result = result.decode('utf_8')
                result = result.translate(table)
        return result

    def copyScribusContent(self, src):
        # Returns a plain copy of src where src is expected to be a list (of text lines)
        result = []
        for line in src:
            result.append(line)
        return result

    def readFileContent(self, src):
        # Returns the list of lines (as strings) of the text-file
        tmp = open(src, 'r')
        result = tmp.readlines()
        tmp.close()
        return result
     
    def handleAmpersand(self, row):
        # If someone uses an '&' as variable (e.g. %VAR_&position%), this text will be saved
        # like %VAR_&amp;position% as the & is being converted by scribus to textual ampersand.
        # Therefore we have to check and convert. It will also be used to replace ampersand of
        # CSV rows, so that you can have values like e.g. "A & B Company".
        result = []
        for i in row:
            result.append(i.replace('&', '&amp;').replace('"','&quot;'))
        return result
    
    
    def replaceVariablesWithCsvData(self, varNames, row, lines, clean=CONST.REMOVE_EMPTY_LINES, keepTabsLF=0): # lines as list of strings
        result = ''
        for idx,line in enumerate(lines): # done in string instead of XML for lack of efficient attribute-value-based substring-search in ElementTree
            # logging.debug("replacing vars in (out of %s): %s"%(len(line), line[:25]))

            # skip un-needed computations
            if (re.search('%VAR_',line)==None) or (re.search('\s*<COLOR\s+',line)!=None):
                result = result + line
                # logging.debug("  keeping %s"%line[:25])
                continue
            
            # replace with data
            logging.debug("replacing VARS_ in %s"%line[:25])
            for i,cell in enumerate(row):
                tmp = ('%VAR_' + varNames[i] + '%')                     
                line = line.replace(tmp, cell)
            
            # remove (& trim) any (unused) %VAR_\w*% like string.                
            if (clean):  
                (line, d) = re.subn('\s*%VAR_\w*%\s*', '', line)
                if (d>0):
                    logging.debug("cleaned %d empty variable"%d)
            
            # convert \t and \n into scribus <tab/> and <linebreak/>
            if (keepTabsLF == 1) and (re.search('[\t\n]+', line, flags=re.MULTILINE)):
                m = re.search('(<ITEXT.* CH=")([^"]+)(".*/>)', line, flags=re.MULTILINE|re.DOTALL)
                if m:
                    begm = m.group(1)
                    endm = m.group(3)
                    # logging.debug("converting tabs and linebreaks in line: %s"%(line))
                    line = re.sub('([\t\n]+)', endm + '\g<1>' + begm, line, flags=re.MULTILINE)
                    #replace \t and \n
                    line = re.sub('\t','<tab />',line)
                    line = re.sub('\n','<breakline />',line, flags=re.MULTILINE)
                    logging.debug("converted tabs and linebreaks in line: %s"%line)
                else:
                    logging.warning("could not convert tabs and linebreaks in this line, kindly report this to the developppers: %s"%(line))
                    
            result = result + line
        return result
         
    def getCsvData(self, csvfile):
        # Read CSV file and return  2-dimensional list containing the data
        reader = csv.reader(file(csvfile), delimiter=self.__dataObject.getCsvSeparator(), skipinitialspace=True, doublequote=True)
        result = []
        for row in reader:
            rowlist = []
            for col in row:
                rowlist.append(col)
            result.append(rowlist)
        return result  

    def getLog(self):
        return logging

    def getSavedSettings(self):
        logging.debug("parsing scribus source file %s for user settings"%(self.__dataObject.getScribusSourceFile()))
        try:
            t = ET.parse(self.__dataObject.getScribusSourceFile())
            r = t.getroot()        
            doc = r.find('DOCUMENT')
            storage = doc.find('./JAVA[@NAME="'+CONST.STORAGE_NAME+'"]')                    
            return storage.get("SCRIPT")
        except Exception, e:
            logging.debug("could not load the user settings for Scribus Generator, skipping. more info:\n%s"%e.message)  
            return None
        
        

class GeneratorDataObject:
    # Data Object for transfering the settings made by the user on the UI / CLI
    def __init__(self,
        scribusSourceFile = CONST.EMPTY,
        dataSourceFile = CONST.EMPTY,
        outputDirectory = CONST.EMPTY,
        outputFileName = CONST.EMPTY,
        outputFormat = CONST.EMPTY,
        keepGeneratedScribusFiles = CONST.FALSE,
        csvSeparator = CONST.CSV_SEP,
        singleOutput = CONST.FALSE, 
        firstRow = CONST.EMPTY, 
        lastRow = CONST.EMPTY,
        saveSettings = CONST.TRUE):
        self.__scribusSourceFile = scribusSourceFile
        self.__dataSourceFile = dataSourceFile
        self.__outputDirectory = outputDirectory
        self.__outputFileName = outputFileName
        self.__outputFormat = outputFormat
        self.__keepGeneratedScribusFiles = keepGeneratedScribusFiles
        self.__csvSeparator = csvSeparator
        self.__singleOutput = singleOutput
        self.__firstRow = firstRow
        self.__lastRow = lastRow
        self.__saveSettings = saveSettings
    
    # Get
    def getScribusSourceFile(self):
        return self.__scribusSourceFile
    
    def getDataSourceFile(self):
        return self.__dataSourceFile
    
    def getOutputDirectory(self):
        return self.__outputDirectory
    
    def getOutputFileName(self):
        return self.__outputFileName
    
    def getOutputFormat(self):
        return self.__outputFormat
    
    def getKeepGeneratedScribusFiles(self):
        return self.__keepGeneratedScribusFiles

    def getCsvSeparator(self):
        return self.__csvSeparator

    def getSingleOutput(self):
        return self.__singleOutput

    def getFirstRow(self):
        return self.__firstRow

    def getLastRow(self):
        return self.__lastRow

    def getSaveSettings(self):
        return self.__saveSettings

    # Set
    def setScribusSourceFile(self, fileName):
        self.__scribusSourceFile = fileName
        
    def setDataSourceFile(self, fileName):
        self.__dataSourceFile = fileName
    
    def setOutputDirectory(self, directory):
        self.__outputDirectory = directory
        
    def setOutputFileName(self, fileName):
        self.__outputFileName = fileName
        
    def setOutputFormat(self, outputFormat):
        self.__outputFormat = outputFormat
        
    def setKeepGeneratedScribusFiles(self, value):
        self.__keepGeneratedScribusFiles = value

    def setCsvSeparator(self, value):
        self.__csvSeparator = value

    def setSingleOutput(self, value):
        self.__singleOutput = value

    def setFirstRow(self, value):
        self.__firstRow = value

    def setLastRow(self, value):
        self.__lastRow = value

    def setSaveSettings(self, value):
        self.__saveSettings = value

    # (de)Serialize all options but scribusSourceFile and saveSettings
    def toString(self):
        return json.dumps({
            '_comment':"this is an automated placeholder for ScribusGenerator default settings. more info at https://github.com/berteh/ScribusGenerator/. modify at your own risks.",
            #'scribusfile':self.__scribusSourceFile NOT saved
            'csvfile':self.__dataSourceFile,
            'outdir':self.__outputDirectory,
            'outname':self.__outputFileName,
            'outformat':self.__outputFormat,
            'keepsla':self.__keepGeneratedScribusFiles,
            'separator':self.__csvSeparator,
            'single':self.__singleOutput,
            'from':self.__firstRow,
            'to':self.__lastRow,
            #'savesettings':self.__saveSettings NOT saved
        }, sort_keys=True)

    def loadFromString(self, string): #todo add validity/plausibility checks on all values? 
        j = json.loads(string)
        for k,v in j.iteritems():
            if v == None:
                j[k] = CONST.EMPTY
        #self.__scribusSourceFile NOT loaded
        self.__dataSourceFile = j['csvfile']
        self.__outputDirectory = j['outdir']
        self.__outputFileName = j['outname']
        self.__outputFormat = j['outformat']
        self.__keepGeneratedScribusFiles = j['keepsla']
        self.__csvSeparator = str(j['separator']) #str()to prevent TypeError: : "delimiter" must be string, not unicode, in csv.reader() call
        self.__singleOutput = j["single"]
        self.__firstRow = j["from"]
        self.__lastRow = j["to"]
        # self.__saveSettings NOT loaded
        logging.debug("loaded %d user settings"%(len(j)-1)) #-1 for the artificial "comment"
        return j
