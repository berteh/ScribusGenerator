#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
=================
Automatic document generation for Scribus.
=================

For further information (manual, description, etc.) please visit:
http://berteh.github.io/ScribusGenerator/

# v2.9.1 (2021-01-22): update port to Python3 for Scribut 1.5.6+, various DOC update

This script is the ScribusGenerator Engine

=================
The MIT License
=================

Copyright (c) 2010-2014 Ekkehard Will (www.ekkehardwill.de), 2014-2021 Berteh (https://github.com/berteh/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import csv
import os
import platform
import logging
import logging.config
import sys
import xml.etree.ElementTree as ET
import json
import re
import string, math


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
    # CSV entry separator, comma by default; tab: " " is also common if using Excel.
    CSV_SEP = ","
    CSV_ENCODING = 'utf-8'
    # indent the generated SLA code for more readability, aka "XML pretty print". set to 1 if you want to edit generated SLA manually.
    INDENT_SLA = 1
    CONTRIB_TEXT = "\npowered by ScribusGenerator - https://github.com/berteh/ScribusGenerator/"
    STORAGE_NAME = "ScribusGeneratorDefaultSettings"
    # set to 0 to prevent removal of un-subsituted variables, along with their empty containing itext
    CLEAN_UNUSED_EMPTY_VARS = 1
    # set to 0 to keep the separating element before an unused/empty variable, typicaly a linefeed (<para>) or list syntax token (,;-.)
    REMOVE_CLEANED_ELEMENT_PREFIX = 1
    # set to 0 to replace all tabs and linebreaks in csv data by simple spaces.
    KEEP_TAB_LINEBREAK = 1
    SG_VERSION = '2.9.2 python3'
    # set to any word you'd like to use to trigger a jump to the next data record. using a name similar to the variables %VAR_ ... % will ensure it is cleaned after generation, and not show in the final document(s).
    NEXT_RECORD = '%SG_NEXT-RECORD%'


class ScribusGenerator:
    # The Generator Module has all the logic and will do all the work
    def __init__(self, dataObject):
        self.__dataObject = dataObject
        logging.config.fileConfig(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.conf'))
        # todo: check if logging works, if not warn user to configure log file path and disable.
        logging.info("ScribusGenerator initialized")
        logging.debug("OS: %s - Python: %s - ScribusGenerator v%s" %
                      (os.name, platform.python_version(), CONST.SG_VERSION))

    def run(self):
        # Read CSV/JSON data and replace the variables in the Scribus File with the corresponding data. Finally export to the specified format.
        # may throw exceptions if errors are met, use traceback to get all error details

        # log options
        optionsTxt = self.__dataObject.toString()
        logging.debug("active options: %s%s" %
                      (optionsTxt[:1], optionsTxt[172:]))

        # output file name
        if(self.__dataObject.getSingleOutput() and (self.__dataObject.getOutputFileName() is CONST.EMPTY)):
            self.__dataObject.setOutputFileName(os.path.split(os.path.splitext(
                self.__dataObject.getScribusSourceFile())[0])[1] + '__single')

        # source sla
        logging.info("parsing scribus SLA file %s" %
                     (self.__dataObject.getScribusSourceFile()))
        try:
            tree = ET.parse(self.__dataObject.getScribusSourceFile())
        except IOError as exception:
            logging.error("Scribus file not found: %s" %
                          (self.__dataObject.getScribusSourceFile()))
            raise
        root = tree.getroot()
        version = root.get('Version')
        logging.debug("Scribus SLA template version is %s" % (version))

        # save settings
        if (self.__dataObject.getSaveSettings()):
            serial = self.__dataObject.toString()
            logging.debug(
                "saving current Scribus Generator settings in your source file") # as: %s"%serial)
            docElt = root.find('DOCUMENT')
            storageElt = docElt.find('./JAVA[@NAME="'+CONST.STORAGE_NAME+'"]')
            if (storageElt is None):
                colorElt = docElt.find('./COLOR[1]')
                scriptPos = list(docElt).index(colorElt)
                logging.debug(
                    "creating new storage element in SLA template at position %s" % scriptPos)
                storageElt = ET.Element("JAVA", {"NAME": CONST.STORAGE_NAME})
                docElt.insert(scriptPos, storageElt)
            storageElt.set("SCRIPT", serial)
            # todo BUG race condition: check if scribus reloads (or overwrites :/ ) when doc is opened, opt use API to add a script if there's an open doc.
            tree.write(self.__dataObject.getScribusSourceFile())


        # Parse data file
        data = self.parse_data()

        # Generate SLA file(s) from data
        dataC = len(data)
        fillCount = len(str(dataC))
        # XML-Content/Text-Content of the Source Scribus File (List of Lines)
        template = []
        outputFileNames = []
        index = 1  # current data record
        rootStr = ET.tostring(root, encoding=self.__dataObject.getCsvEncoding(), method='xml').decode()
        # number of data records consumed by source document
        recordsInDocument = 1 + rootStr.count(CONST.NEXT_RECORD)
        logging.info("source document consumes %s data record(s) from %s." %
                     (recordsInDocument, dataC))

        # global vars
        dataBuffer = []
        templateElt = self.overwriteAttributesFromSGAttributes(root)

        pagescount = pageheight = vgap = groupscount = objscount = 0
        outContent = ''
        varNamesForReplacingVariables = self.encodeScribusXML([data[0]])[0]

        for row in data:
        # invariant: data has been substituded up to data[index-1], and
        # SLA code is stored accordingly in outContent,
        # SLA files have been generated up to index-1 entry as per generation
        # options and numer of records consumed by the source template.

            if(index == 1):  # initialization, get vars names from frow keys
                varNamesForFileName = list(row.keys())
                logging.info("variables from data files: %s" % (varNamesForReplacingVariables))
                # overwrite attributes from their /*/ItemAttribute[Parameter=SGAttribute] sibling, when applicable.
                templateElt = self.overwriteAttributesFromSGAttributes(root)

            # handle row data
            dataBuffer.append(row)

            # done buffering data for current document OR reached last data record
            if (index % recordsInDocument == 0) or index == dataC:
                logging.debug("subsitute, with data entry index being %s" % (index))
                outContent = self.substituteData(
                  varNamesForReplacingVariables,
                  self.encodeScribusXML(dataBuffer),
                  ET.tostring(templateElt, method='xml').decode().split('\n'),
                  keepTabsLF=CONST.KEEP_TAB_LINEBREAK)

                if (self.__dataObject.getSingleOutput()): # merge mode
                    # first substitution, update DOCUMENT properties
                    if (index == min(recordsInDocument,dataC)):
                        logging.debug(
                            "generating reference content from dataBuffer at #%s" % (index))
                        outputElt = ET.fromstring(outContent)
                        docElt = outputElt.find('DOCUMENT')
                        pagescount = int(docElt.get('ANZPAGES'))
                        pageheight = float(docElt.get('PAGEHEIGHT'))
                        vgap = float(docElt.get('GapVertical'))
                        groupscount = int(docElt.get('GROUPC'))
                        objscount = len(outputElt.findall('.//PAGEOBJECT'))
                        logging.debug(
                            "current template has #%s pageobjects" % (objscount))
                        docElt.set('ANZPAGES', str(
                            math.ceil(pagescount*dataC//recordsInDocument)))
                        docElt.set('DOCCONTRIB', docElt.get(
                            'DOCCONTRIB')+CONST.CONTRIB_TEXT)
                    #append DOCUMENT content
                    logging.debug(
                        "merging content from dataBuffer up to entry index #%s" % (index))
                    tmpElt = ET.fromstring(outContent).find('DOCUMENT')
                    shiftedElts = self.shiftPagesAndObjects(
                        tmpElt, pagescount, pageheight, vgap, index-1, recordsInDocument, groupscount, objscount, version)
                    docElt.extend(shiftedElts)
                else:  # write one of multiple sla
                    outputFileName = self.createOutputFileName(
                        index, self.__dataObject.getOutputFileName(), dataBuffer, fillCount)
                    self.writeSLA(ET.fromstring(
                        outContent), outputFileName)
                    outputFileNames.append(outputFileName)
                dataBuffer = []
            index = index + 1

        # clean & write single sla
        if (self.__dataObject.getSingleOutput()):
            self.writeSLA(outputElt, self.__dataObject.getOutputFileName())
            outputFileNames.append(self.__dataObject.getOutputFileName())

        # Export the generated Scribus Files as PDF
        if(CONST.FORMAT_PDF == self.__dataObject.getOutputFormat()):
            for outputFileName in outputFileNames:
                pdfOutputFilePath = self.createOutputFilePath(
                    self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_PDF)
                scribusOutputFilePath = self.createOutputFilePath(
                    self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                self.exportPDF(scribusOutputFilePath, pdfOutputFilePath)
                logging.info("pdf file created: %s" % (pdfOutputFilePath))

        # Cleanup the generated Scribus Files
        if(not (CONST.FORMAT_SLA == self.__dataObject.getOutputFormat()) and CONST.FALSE == self.__dataObject.getKeepGeneratedScribusFiles()):
            for outputFileName in outputFileNames:
                scribusOutputFilePath = self.createOutputFilePath(
                    self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                self.deleteFile(scribusOutputFilePath)

        return 1

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

    def writeSLA(self, slaET, outFileName, clean=CONST.CLEAN_UNUSED_EMPTY_VARS, indentSLA=CONST.INDENT_SLA):
        # write SLA to filepath computed from given elements, optionnaly cleaning empty ITEXT elements and their empty PAGEOBJECTS
        scribusOutputFilePath = self.createOutputFilePath(
            self.__dataObject.getOutputDirectory(), outFileName, CONST.FILE_EXTENSION_SCRIBUS)
        d = os.path.dirname(scribusOutputFilePath)
        if not os.path.exists(d):
            os.makedirs(d)
        outTree = ET.ElementTree(slaET)
        if (clean):
            self.removeEmptyTexts(outTree.getroot())
        if (indentSLA):
            from xml.dom import minidom
            xmlstr = minidom.parseString(ET.tostring(outTree.getroot())).toprettyxml(indent="   ")
            with open(scribusOutputFilePath, "w", encoding='utf-8') as f:
                f.write(xmlstr)
        else:
            outTree.write(scribusOutputFilePath, encoding='utf-8')
        logging.info("scribus file created: %s" % (scribusOutputFilePath))
        return scribusOutputFilePath

    def overwriteAttributesFromSGAttributes(self, root):
        # modifies root such that
        # attributes have been rewritten from their /*/ItemAttribute[Parameter=SGAttribute] sibling, when applicable.
        #
        # allows to use %VAR_<var-name>% in Item Attribute to overwrite internal attributes (eg FONT)

        for pageobject in root.findall(".//ItemAttribute[@Parameter='SGAttribute']/../.."):
            for sga in pageobject.findall(".//ItemAttribute[@Parameter='SGAttribute']"):
                attribute = sga.get('Name')
                value = sga.get('Value')
                ref = sga.get('RelationshipTo')

                if ref == "":  # Cannot use 'default' on .get() as it is "" by default in SLA file.
                    # target is pageobject by default. Cannot use ".|*" as not supported by ET.
                    ref = "."
                elif ref.startswith("/"):  # ET cannot use absolute path on element
                    ref = "."+ref

                try:
                    targets = pageobject.findall(ref)
                    if targets:
                        for target in targets:
                            logging.debug('overwriting value of %s in %s with "%s"' % (
                                attribute, target.tag, value))
                            target.set(attribute, value)
                    else:
                        logging.error('Target "%s" could be parsed but designated no node. Check it out as it is probably not what you expected to replace %s.' % (
                            ref, attribute))  # todo message to user

                except SyntaxError:
                    logging.error('XPATH expression "%s" could not be parsed by ElementTree to overwrite %s. Skipping.' % (
                        ref, attribute))  # todo message to user

        return root

    def shiftPagesAndObjects(self, docElt, pagescount, pageheight, vgap, index, recordsInDocument, groupscount, objscount, version):
        shifted = []
        voffset = (float(pageheight)+float(vgap)) * \
            (index // recordsInDocument)
        #logging.debug("shifting to voffset %s " % (voffset))
        for page in docElt.findall('PAGE'):
            page.set('PAGEYPOS', str(float(page.get('PAGEYPOS')) + voffset))
            page.set('NUM', str(int(page.get('NUM')) + pagescount))
            shifted.append(page)
        for obj in docElt.findall('PAGEOBJECT'):
            ypos = obj.get('YPOS')
            if (ypos == "" ):
                ypos = 0
            #logging.debug("original YPOS is %s " % (ypos))
            obj.set('YPOS', str(float(ypos) + voffset))
            obj.set('OwnPage', str(int(obj.get('OwnPage')) + pagescount))
            # update ID and links
            if version.startswith('1.4'):
                #                if not (int(obj.get('NUMGROUP')) == 0):
                #                    obj.set('NUMGROUP', str(int(obj.get('NUMGROUP')) + groupscount * index))
                # next linked frame by position
                if (obj.get('NEXTITEM') != None and (str(obj.get('NEXTITEM')) != "-1")):
                    obj.set('NEXTITEM', str(
                        int(obj.get('NEXTITEM')) + (objscount * index)))
                # previous linked frame by position
                if (obj.get('BACKITEM') != None and (str(obj.get('BACKITEM')) != "-1")):
                    obj.set('BACKITEM', str(
                        int(obj.get('BACKITEM')) + (objscount * index)))
            else:  # 1.5, 1.6
                #logging.debug("version is %s shifting object %s (#%s)" %
                #              (version, obj.tag, obj.get('ItemID')))

                # todo update ID with something unlikely allocated, TODO ensure unique ID instead of 6:, issue #101
                obj.set('ItemID', str(objscount * index) +
                        str(int(obj.get('ItemID')))[7:])
                # next linked frame by ItemID
                if (obj.get('NEXTITEM') != None and (str(obj.get('NEXTITEM')) != "-1")):
                    obj.set('NEXTITEM', str(objscount * index) +
                            str(int(obj.get('NEXTITEM')))[7:])
                # previous linked frame by ItemID
                if (obj.get('BACKITEM') != None and (str(obj.get('BACKITEM')) != "-1")):
                    obj.set('BACKITEM', str(objscount * index) +
                            str(int(obj.get('BACKITEM')))[7:])

            shifted.append(obj)
        logging.debug("shifted page %s element of %s" % (index, voffset))
        return shifted

    def removeEmptyTexts(self, root):
        # *modifies* root ElementTree by removing empty text elements and their empty placeholders.
        # returns number of ITEXT elements deleted.
        #   1. clean text in which some variable-like text is not substituted (ie: known or unknown variable):
        #      <ITEXT CH="empty %VAR_empty% variable should not show" FONT="Arial Regular" />
        #   2. remove <ITEXT> with empty @CH and precedings <para/> if any
        #   3. remove any <PAGEOBJECT> that has no <ITEXT> child left
        emptyXPath = "ITEXT[@CH='']"
        d = 0
        # little obscure because its parent is needed to remove an element, and ElementTree has no parent() method.
        for page in root.findall(".//%s/../.." % emptyXPath):
            # collect emptyXPath and <para> that precede for removal, iter is need for lack of sibling-previous navigation in ElementTree
            for po in page.findall(".//%s/.." % emptyXPath):
                trash = []
                for pos, item in enumerate(po):
                    if (item.tag == "ITEXT") and (item.get("CH") == ""):
                        logging.debug(
                            "cleaning 1 empty ITEXT and preceding linefeed (opt.)")
                        if (CONST.REMOVE_CLEANED_ELEMENT_PREFIX and po[pos-1].tag == "para"):
                            trash.append(pos-1)
                        trash.append(pos)
                        d += 1
                trash.reverse()
                # remove trashed elements as stack (lifo order), to preserve positions validity
                for i in trash:
                    po.remove(po[i])
                if (len(po.findall("ITEXT")) == 0):
                    logging.debug("cleaning 1 empty PAGEOBJECT")
                    page.remove(po)
        logging.info("removed %d empty texts items" % d)
        return d

    def deleteFile(self, outputFilePath):
        # Delete the temporarily generated files from off the file system
        os.remove(outputFilePath)

    def createOutputFilePath(self, outputDirectory, outputFileName, fileExtension):
        # Build the absolute path, like C:/tmp/template.sla
        return outputDirectory + CONST.SEP_PATH + outputFileName + CONST.SEP_EXT + fileExtension

    def createOutputFileName(self, index, outputFileName, rows, fillCount):
        # If the User has not set an Output File Name, an internal unique file name
        # will be generated which is the index of the loop.
        result = str(index)
        result = result.zfill(fillCount)
        # Following characters are not allowed for File-Names on WINDOWS: < > ? " : | \ / *
        # Note / is still allowed in filename as it allows dynamic subdirectory in Linux (issue 102); todo check & fix for Windows
        if(CONST.EMPTY != outputFileName):
            table = {
                # ord(u'ä'): u'ae',
                # ord(u'Ä'): u'Ae',
                # ord(u'ö'): u'oe',
                # ord(u'Ö'): u'Oe',
                # ord(u'ü'): u'ue',
                # ord(u'Ü'): u'Ue',
                # ord(u'ß'): u'ss',
                ord('<'): '_',
                ord('>'): '_',
                ord('?'): '_',
                ord('"'): '_',
                ord(':'): '_',
                ord('|'): '_',
                ord('\\'): '_',
                # ord(u'/'): u'_',
                ord('*'): '_'
            }
            result = self.substituteData([key for key in rows[0].keys()], rows, [outputFileName])
            result = result
            result = result.translate(table)
            logging.debug("output file name is %s" % result)
        return result

    def copyScribusContent(self, src):
        # Returns a plain copy of src where src is expected to be a list (of text lines)
        result = []
        for line in src:
            result.append(line)
        return result

    def readFileContent(self, src):
        # Returns the list of lines (as strings) of the text-file
        tmp = open(src, 'r', encoding=self.__dataObject.getCsvEncoding())
        result = tmp.readlines()
        tmp.close()
        return result

    def encodeScribusXML(self, rows):
        # Encode some characters that can be found in CSV into XML entities
        # not all are needed as Scribus handles most UTF8 characters just fine.
        result = []
        replacements = {'&':'&amp;', '"':'&quot;', '<':'&lt;'}

        for row in rows:
            result.append({key: self.multiple_replace(value, replacements) for key, value in row.items()})

            # res1 = []
            # for i in row:
            #     res1.append(self.multiple_replace(i, replacements))
            # result.append(res1)
        return result

    def multiple_replace(self, string, rep_dict):
        # multiple simultaneous string replacements, per http://stackoverflow.com/a/15448887/1694411)
        # combine with dictionary = dict(zip(keys, values)) to use on arrays
        pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)

        return pattern.sub(lambda x: rep_dict[x.group(0)], str(string))

    # lines as list of strings
    def substituteData(self, varNames, rows, lines, clean=CONST.CLEAN_UNUSED_EMPTY_VARS, keepTabsLF=0):
        result = ''
        currentRecord = 0
        # replacements = dict(
        #     list(zip(['%VAR_'+i+'%' for i in varNames], rows[currentRecord])))
        varNames = [key for key in rows[0].keys()]

        replacements = {'%VAR_'+ key +'%': value for key, value in rows[0].items()}

        logging.debug("replacements is: %s"%replacements)

        # done in string instead of XML for lack of efficient attribute-value-based substring-search in ElementTree
        for idx, line in enumerate(lines):
            # logging.debug("replacing vars in (out of %s): %s"%(len(line), line[:30]))

            # skip un-needed computations and preserve colors declarations
            if (re.search('%VAR_|'+CONST.NEXT_RECORD, line) == None) or (re.search('\s*<COLOR\s+', line) != None):
                result = result + line
                # logging.debug("  keeping intact %s"%line[:30])
                continue

            # detect NEXT_RECORD
            if CONST.NEXT_RECORD in line:
                currentRecord += 1
                if currentRecord < len(rows):
                    logging.debug("loading next record")
                    replacements = dict(
                        list(zip(['%VAR_'+i+'%' for i in varNames], rows[currentRecord])))
                else:  # last record reach, leave remaing variables to be cleaned
                    replacements = {
                        "END-OF-REPLACEMENTS": "END-OF-REPLACEMENTS"}
                    logging.debug("next record reached last data entry")

            # replace with data
            #logging.debug("replacing VARS_* in %s" % line[:30].strip())
            line = self.multiple_replace(line, replacements)
            #logging.debug("replaced in line: %s" % line)

            # remove (& trim) any (unused) %VAR_\w*% like string.
            if (clean):
                if (CONST.REMOVE_CLEANED_ELEMENT_PREFIX):  ## TODO is there a way to input warning "data not found for variable named XX" instead of the number
                    (line, d) = re.subn('\s*[,;-]*\s*%VAR_\w*%\s*', '', line)
                else: ## TODO is there a way to input warning "data not found for variable named XX" instead of the number
                    (line, d) = re.subn('\s*%VAR_\w*%\s*', '', line)
                if (d > 0):
                    logging.debug("cleaned %d empty variable" % d)
                (line, d) = re.subn('\s*%s\w*\s*' %
                                    CONST.NEXT_RECORD, '', line)

            # convert \t and \n into scribus <tab/> and <linebreak/>
            if (keepTabsLF == 1) and (re.search('[\t\n]+', line, flags=re.MULTILINE)):
                m = re.search(
                    '(<ITEXT.* CH=")([^"]+)(".*/>)', line, flags=re.MULTILINE | re.DOTALL)
                if m:
                    begm = m.group(1)
                    endm = m.group(3)
                    # logging.debug("converting tabs and linebreaks in line: %s"%(line))
                    line = re.sub('([\t\n]+)', endm + '\g<1>' +
                                  begm, line, flags=re.MULTILINE)
                    # replace \t and \n
                    line = re.sub('\t', '<tab />', line)
                    line = re.sub('\n', '<breakline />',
                                  line, flags=re.MULTILINE)
                    logging.debug(
                        "converted tabs and linebreaks in line: %s" % line)
                else:
                    logging.warning(
                        "could not convert tabs and linebreaks in this line, kindly report this to the developppers: %s" % (line))

            result = result + line
        return result


    # Part I : PARSING DATA

    def parse_data(self):
        data_file = self.__dataObject.getDataSourceFile()

        # (1) Check if data file exists
        if not os.path.exists(data_file):
        # .. otherwise, log error & raise exception
            logging.error('Data file not found: %s' % (data_file))
            raise

        logging.debug('Parsing data file %s' % (data_file))

        # (2) Process data
        data = []

        # .. depending on file type
        extension = os.path.splitext(data_file)[1]

        if extension == '.json':
            # .. from JSON file
            data = load_json(data_file)

        # (3) Load data
        if extension == '.csv':
            # .. from CSV file
            data = self.load_csv(data_file)

            if len(data) <= 1:
                logging.error(
                    'Data file %s has only one line or is empty. ' +
                    'At least a header line and a line of data is needed. Halting.' % (
                        data_file
                    )
                )

                return -1

            # Determine data range
            # (1) First item
            first_item = 1
            first_row = self.__dataObject.getFirstRow()

            if first_row != CONST.EMPTY:
                try:
                    new_first_item_value = int(first_row)

                    # Guard against 0 or negative numbers
                    first_item = max(new_first_item_value, 1)

                except:
                    logging.warning(
                        'Could not parse value of "first row" as an integer, using default value instead.'
                    )

            # (2) Last item
            last_item = len(data)
            last_row = self.__dataObject.getLastRow()

            if last_row != CONST.EMPTY:
                try:
                    new_last_item_value = int(last_row)

                    # Guard against numbers higher than the length of data
                    last_item = min(new_last_item_value, last_item)

                except:
                    logging.warning(
                        'Could not parse value of "last row" as an integer, using default value instead.')

            # (3) Apply data range (if needed)
            if first_item != 1 or last_item != len(data):
                data = data[first_item:last_item]
                logging.debug('Custom data range is: %s - %s' % (first_item, last_item))

            else:
                logging.debug('Full data range will be used.')

        return data


    def load_json(self, json_file: str) -> list:
        try:
            with open(json_file, 'r') as file:
                return json.load(file)

        except json.decoder.JSONDecodeError:
            raise

        return []


    def load_csv(self, csv_file: str) -> list:
        # Determine CSV options
        encoding = self.__dataObject.getCsvEncoding()
        delimiter = self.__dataObject.getCsvSeparator()

        # Load file contents
        with open(csv_file, newline='', encoding=encoding) as file:
            # Parse CSV data
            reader = csv.DictReader(file, delimiter=delimiter, skipinitialspace=True, doublequote=True)

            # Filter empty lines
            return [item for item in list(reader) if item]


    def getLog(self):
        return logging

    def getSavedSettings(self):
        logging.debug("parsing scribus source file %s for user settings" % (
            self.__dataObject.getScribusSourceFile()))
        try:
            t = ET.parse(self.__dataObject.getScribusSourceFile())
            r = t.getroot()
            doc = r.find('DOCUMENT')
            storage = doc.find('./JAVA[@NAME="'+CONST.STORAGE_NAME+'"]')
            return storage.get("SCRIPT")
        except SyntaxError as exception:
            logging.error(
                "Loading settings is only possible with Python 2.7 and later, please update your system: %s" % exception)
            return None
        except Exception as exception:
            logging.debug("could not load the user settings: %s" % exception)
            return None


class GeneratorDataObject:
    # Data Object for transfering the settings made by the user on the UI / CLI
    def __init__(self,
        scribusSourceFile=CONST.EMPTY,
        dataSourceFile=CONST.EMPTY,
        outputDirectory=CONST.EMPTY,
        outputFileName=CONST.EMPTY,
        outputFormat=CONST.EMPTY,
        keepGeneratedScribusFiles=CONST.FALSE,
        csvSeparator=CONST.CSV_SEP,
        csvEncoding=CONST.CSV_ENCODING,
        singleOutput=CONST.FALSE,
        firstRow=CONST.EMPTY,
        lastRow=CONST.EMPTY,
        saveSettings=CONST.TRUE,
        closeDialog=CONST.FALSE
    ):
        self.__scribusSourceFile = scribusSourceFile
        self.__dataSourceFile = dataSourceFile
        self.__outputDirectory = outputDirectory
        self.__outputFileName = outputFileName
        self.__outputFormat = outputFormat
        self.__keepGeneratedScribusFiles = keepGeneratedScribusFiles
        self.__csvSeparator = csvSeparator
        self.__csvEncoding = csvEncoding
        self.__singleOutput = singleOutput
        self.__firstRow = firstRow
        self.__lastRow = lastRow
        self.__saveSettings = saveSettings
        self.__closeDialog = closeDialog


    # Getters

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

    def getCsvEncoding(self):
        return self.__csvEncoding

    def getSingleOutput(self):
        return self.__singleOutput

    def getFirstRow(self):
        return self.__firstRow

    def getLastRow(self):
        return self.__lastRow

    def getSaveSettings(self):
        return self.__saveSettings

    def getCloseDialog(self):
        return self.__closeDialog


    # Setters

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

    def setCsvEncoding(self, value):
        self.__csvEncoding = value

    def setSingleOutput(self, value):
        self.__singleOutput = value

    def setFirstRow(self, value):
        self.__firstRow = value

    def setLastRow(self, value):
        self.__lastRow = value

    def setSaveSettings(self, value):
        self.__saveSettings = value

    def setCloseDialog(self, value):
        self.__closeDialog = value

    # (de)Serialize all options but scribusSourceFile and saveSettings
    def toString(self):
        return json.dumps({
            '_comment': "this is an automated placeholder for ScribusGenerator default settings. more info at https://github.com/berteh/ScribusGenerator/. modify at your own risks.",
            # 'scribusfile':self.__scribusSourceFile NOT saved
            'csvfile': self.__dataSourceFile,
            'outdir': self.__outputDirectory,
            'outname': self.__outputFileName,
            'outformat': self.__outputFormat,
            'keepsla': self.__keepGeneratedScribusFiles,
            'separator': self.__csvSeparator,
            'csvencoding': self.__csvEncoding,
            'single': self.__singleOutput,
            'from': self.__firstRow,
            'to': self.__lastRow,
            'close': self.__closeDialog
            # 'savesettings':self.__saveSettings NOT saved
        }, sort_keys=True)

    # todo add validity/plausibility checks on all values?
    def loadFromString(self, string):
        j = json.loads(string)
        for k, v in j.items():
            if v == None:
                j[k] = CONST.EMPTY
        # self.__scribusSourceFile NOT loaded
        self.__dataSourceFile = j['csvfile']
        self.__outputDirectory = j['outdir']
        self.__outputFileName = j['outname']
        self.__outputFormat = j['outformat']
        self.__keepGeneratedScribusFiles = j['keepsla']
        # str()to prevent TypeError: : "delimiter" must be string, not unicode, in csv.reader() call
        self.__csvSeparator = str(j['separator'])
        self.__csvEncoding = str(j['csvencoding'])
        self.__singleOutput = j["single"]
        self.__firstRow = j["from"]
        self.__lastRow = j["to"]
        self.__closeDialog = j["close"]
        # self.__saveSettings NOT loaded
        logging.debug("loaded %d user settings" %
                      (len(j)-1))  # -1 for the artificial "comment"
        return j
