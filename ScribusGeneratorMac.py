#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

=================
Automatic document generation for Scribus.
=================

For further information (manual, description, etc.) please visit:
http://berteh.github.io/ScribusGenerator/

# v3.0 (2022-01-12): port to Python3 for Scribut 1.5.6+, some features (count, fill)
# v2.0 (2015-12-02): added features (merge, range, clean, save/load)
# v1.9 (2015-08-03): initial GUI version with PDF generation

This script is the GUI (Scribus API) ScribusGenerator that works on macOS
it should also work on any system that does not have TCL-tK installed

=================
The MIT License
=================

Copyright (c) 2010-2014 Ekkehard Will (www.ekkehardwill.de), 2014-2022 Berteh (https://github.com/berteh/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import scribus
import os
import sys
import inspect
import traceback

import ScribusGeneratorBackend
from ScribusGeneratorBackend import CONST, ScribusGenerator, GeneratorDataObject


class GeneratorControl:
    # Controller being the bridge between UI and Logic.
    def __init__(self):
        self.__dataSourceFileEntryVariable = ''
        self.__scribusSourceFileEntryVariable = ''
        self.__dataSeparatorEntryVariable = CONST.CSV_SEP
        self.__dataEncodingEntryVariable = CONST.CSV_ENCODING
        self.__outputDirectoryEntryVariable = ''
        self.__outputFileNameEntryVariable = ''
        # SLA & PDF are valid output format
        self.__outputFormatList = [CONST.FORMAT_PDF, CONST.FORMAT_SLA]
        self.__selectedOutputFormat = CONST.FORMAT_PDF
        self.__keepGeneratedScribusFilesVariable = 0
        self.__mergeOutputVariable = 0
        self.__saveSettingsVariable = 0
        self.__fromVariable = CONST.EMPTY
        self.__toVariable = CONST.EMPTY
        self.__closeDialogVariable = 0
        if scribus.haveDoc():
            doc = scribus.getDocName()
            self.__scribusSourceFileEntryVariable = doc
            self.__outputDirectoryEntryVariable = os.path.split(doc)[0]
            self.__dataSourceFileEntryVariable = os.path.splitext(doc)[0]+".csv"
        else:
            doc = ''

    def getDataSourceFileEntryVariable(self):
        return self.__dataSourceFileEntryVariable

    def setDataSourceFileEntryVariable(self, val):
        self.__dataSourceFileEntryVariable = val

    def getScribusSourceFileEntryVariable(self):
        return self.__scribusSourceFileEntryVariable

    def setScribusSourceFileEntryVariable(self, val):
        self.__scribusSourceFileEntryVariable = val

    def getDataSeparatorEntryVariable(self):
        return self.__dataSeparatorEntryVariable

    def setDataSeparatorEntryVariable(self, val):
        self.__dataSeparatorEntryVariable = val

    def getDataEncodingEntryVariable(self):
        return self.__dataEncodingEntryVariable

    def setDataEncodingEntryVariable(self, val):
        self.__dataEncodingEntryVariable = val

    def getOutputDirectoryEntryVariable(self):
        return self.__outputDirectoryEntryVariable

    def setOutputDirectoryEntryVariable(self, val):
        self.__outputDirectoryEntryVariable = val

    def getOutputFileNameEntryVariable(self):
        return self.__outputFileNameEntryVariable

    def setOutputFileNameEntryVariable(self, val):
        self.__outputFileNameEntryVariable = val

    def getOutputFormatList(self):
        return self.__outputFormatList

    def getSelectedOutputFormat(self):
        return self.__selectedOutputFormat

    def setSelectedOutputFormat(self, val):
        self.__selectedOutputFormat = val

    def getKeepGeneratedScribusFilesVariable(self):
        return self.__keepGeneratedScribusFilesVariable

    def setKeepGeneratedScribusFilesVariable(self, val):
        self.__keepGeneratedScribusFilesVariable = val

    def getMergeOutputVariable(self):
        return self.__mergeOutputVariable

    def setMergeOutputVariable(self, val):
        self.__mergeOutputVariable = val

    def getSaveSettingsVariable(self):
        return self.__saveSettingsVariable

    def setSaveSettingsVariable(self, val):
        self.__saveSettingsVariable = val

    def getFromVariable(self):
        return self.__fromVariable

    def setFromVariable(self, val):
        self.__fromVariable = val

    def getToVariable(self):
        return self.__toVariable

    def setToVariable(self, val):
        self.__toVariable = val

    def getCloseDialogVariable(self):
        return self.__closeDialogVariable

    def setCloseDialogVariable(self, val):
        self.__closeDialogVariable = val

    def allValuesSet(self):
        result = 0
        if ((self.__scribusSourceFileEntryVariable != CONST.EMPTY) and
            (self.__dataSourceFileEntryVariable != CONST.EMPTY) and
            (len(self.__dataEncodingEntryVariable) >= 4) and
            (len(self.__dataSeparatorEntryVariable) == 1)):
            result = 1
        return result


    def createGeneratorDataObject(self):
        # Collect the settings the user has made and build the Data Object
        result = GeneratorDataObject(
            scribusSourceFile=self.__scribusSourceFileEntryVariable,
            dataSourceFile=self.__dataSourceFileEntryVariable,
            outputDirectory=self.__outputDirectoryEntryVariable,
            outputFileName=self.__outputFileNameEntryVariable,
            outputFormat=self.__selectedOutputFormat,
            keepGeneratedScribusFiles=self.__keepGeneratedScribusFilesVariable,
            csvSeparator=self.__dataSeparatorEntryVariable,
            csvEncoding=self.__dataEncodingEntryVariable,
            singleOutput=self.__mergeOutputVariable,
            firstRow=self.__fromVariable,
            lastRow=self.__toVariable,
            saveSettings=self.__saveSettingsVariable,
            closeDialog=self.__closeDialogVariable
        )
        return result

    def buttonCancelHandler(self):
        scribus.messageBox('function','Scribus Generator operation aborted!', scribus.ICON_WARNING)
        sys.exit()

    def buttonOkHandler(self):
        if (CONST.TRUE == self.allValuesSet()):
            dataObject = self.createGeneratorDataObject()
            generator = ScribusGenerator(dataObject)
            try:
                generator.run()
                if(dataObject.getCloseDialog()):
                    scribus.messageBox('Scribus Generator', 'Done. Generated files are in\n'+dataObject.getOutputDirectory(), scribus.ICON_NONE, scribus.BUTTON_OK)
                    sys.exit()
                else:
                    result = scribus.messageBox('Scribus Generator', 'Done. Generated files are in:\n'+dataObject.getOutputDirectory()+'\nClick OK to Generate more data-driven documents.', scribus.ICON_NONE, scribus.BUTTON_OK, scribus.BUTTON_CANCEL)
                    if (result == scribus.BUTTON_OK):
                        main_wrapper(sys.argv) # user wants dialog kept open so wrap around and start again
                    else:
                        sys.exit()

            except IOError as e:  # except FileNotFoundError as e:
                scribus.messageBox('File Not Found', 'Could not find some input file, please verify your Scribus and Data file settings:\n\n'+str(e), scribus.ICON_WARNING, scribus.BUTTON_OK)
            except ValueError as e:
                scribus.messageBox('Variable Error', 'Could likely not replace a variable with its value,\nplease check your Data File and Data Separator settings:\n\n'+str(e), scribus.ICON_WARNING, scribus.BUTTON_OK)
            except IndexError as e:
                scribus.messageBox('Variable Error', 'Could not find the value for one variable.\nplease check your Data File and Data Separator settings.\n\n'+str(e), scribus.ICON_WARNING, scribus.BUTTON_OK)
            except Exception:
                scribus.messageBox('Error Scribus Generator',"Something went wrong.\n\nRead the log file for more (in your home directory)."+traceback.format_exc(), scribus.ICON_WARNING, scribus.BUTTON_OK)
        else:
            scribus.messageBox('Validation Failed', 'Please check if all settings have been set correctly!', scribus.ICON_WARNING, scribus.BUTTON_OK)


    def scribusLoadSettingsHandler(self):
        slaFile = GeneratorControl.getScribusSourceFileEntryVariable(self)

        if(slaFile is CONST.EMPTY):
            scribus.fileDialog('Choose a file', 'Set a valid Scribus *.sla input file prior to loading its settings')
            return
        dataObject = GeneratorDataObject(
            scribusSourceFile=slaFile
        )
        generator = ScribusGenerator(dataObject)
        saved = generator.get_saved_settings()
        if (saved):
            dataObject.loadFromString(saved)
            # self.__scribusSourceFileEntryVariable = StringVar() #not loaded
            GeneratorControl.setDataSourceFileEntryVariable(self, dataObject.getDataSourceFile())
            GeneratorControl.setDataSeparatorEntryVariable(self, dataObject.getCsvSeparator())
            GeneratorControl.setDataEncodingEntryVariable(self, dataObject.getCsvEncoding())
            GeneratorControl.setOutputDirectoryEntryVariable(self, dataObject.getOutputDirectory())
            GeneratorControl.setOutputFileNameEntryVariable(self, dataObject.getOutputFileName())
            GeneratorControl.setSelectedOutputFormat(self, dataObject.getOutputFormat())
            GeneratorControl.setKeepGeneratedScribusFilesVariable(self, dataObject.getKeepGeneratedScribusFiles())
            GeneratorControl.setMergeOutputVariable(self, dataObject.getSingleOutput())
            # GeneratorControl.saveCheckboxVariable = IntVar() #not loaded
            GeneratorControl.setFromVariable(self, dataObject.getFirstRow())
            GeneratorControl.setToVariable(self, dataObject.getLastRow())
            GeneratorControl.setCloseDialogVariable(self, dataObject.getCloseDialog())
        else:
            scribus.messageBox('No Settings', 'Input Scribus file contains no former saved settings.', scribus.ICON_WARNING, scribus.BUTTON_OK|BUTTON_DEFAULT)


class GeneratorDialog:
    # The UI to configure the settings by the user
    def __init__(self, ctrl):
        self.__root = self
        self.__ctrl = ctrl

    def show(self):
        scribus.messageBox("Scribus Generator","SCRIBUS GENERATOR\nYou will be asked in a series of dialogs for the Scribus template and data files, as well as what output format you would like.",scribus.ICON_NONE,scribus.BUTTON_OK)
        scribusFile = scribus.fileDialog('Select Scribus Template File:', 'Scribus(*.sla *.SLA)', defaultname=''+self.__ctrl.getScribusSourceFileEntryVariable()+'')
        if (scribusFile == ''):
            self.__ctrl.buttonCancelHandler()
        self.__ctrl.setScribusSourceFileEntryVariable(scribusFile)
        # check for Saved Settings
        storedSettings = 0
        dataObject = GeneratorDataObject(
            scribusSourceFile = scribusFile
        )
        generator = ScribusGenerator(dataObject)
        saved = generator.get_saved_settings()
        if (saved):
            result = scribus.messageBox('Load Settings', 'Saved Settings have been found for this template. Would you like to see them?', scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
            if (result == scribus.BUTTON_YES):
                dataObject.loadFromString(saved)
                # make some of it easier for humans to read
                if (dataObject.getFirstRow() != '' or dataObject.getLastRow() != ''):
                    fromrow = 'row '+str(dataObject.getFirstRow())
                    torow = 'row '+str(dataObject.getLastRow())
                else:
                    fromrow = 'FIRST row'
                    torow = 'LAST row'
                if (dataObject.getKeepGeneratedScribusFiles() == 1):
                    keep = 'Yes'
                else:
                    keep = 'No'
                if (dataObject.getSingleOutput() == 1):
                    merge = 'Yes'
                else:
                    merge = 'No'
                if (dataObject.getCloseDialog() == 1):
                    closegen = 'Yes'
                else:
                    closegen = 'No'
                loadthem = scribus.messageBox('Load Settings', 'SAVED SETTINGS:\n'+
                    'Data File: '+str(dataObject.getDataSourceFile())+'\n'+
                    'Separator: '+str(dataObject.getCsvSeparator())+'\n'+
                    'Data from '+fromrow+' to '+torow+'\n'+
                    'Encoding:  '+str(dataObject.getCsvEncoding())+'\n'+
                    'Save Dir:  '+str(dataObject.getOutputDirectory())+'\n'+
                    'Filename:  '+str(dataObject.getOutputFileName())+'\n'+
                    'Format:    '+str(dataObject.getOutputFormat())+'\n'+
                    'Keep Files: '+keep+'\n'+
                    'Merge Docs: '+merge+'\n'+
                    'Close Generator: '+closegen+'\n'+
                    '\nWould you like to LOAD and USE these settings?',scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
                if (loadthem == scribus.BUTTON_YES):
                    storedSettings = 1
                    self.__ctrl.scribusLoadSettingsHandler()
                    self.__ctrl.buttonOkHandler()
            else:
                storedSettings = 0
        # Either there are no Saved Settings OR the User did not want to use them.
        if (storedSettings == 0):
            dataFile = scribus.fileDialog('Select Data File:', 'Data(*.csv *.CSV *.tsv *.TSV *.txt *.TXT)', defaultname=''+self.__ctrl.getDataSourceFileEntryVariable()+'')
            if (dataFile == ''):
                self.__ctrl.buttonCancelHandler()
            self.__ctrl.setDataSourceFileEntryVariable(dataFile)
            dataSeparator = scribus.valueDialog('Data Field Separator:','comma, pipe, etc.', self.__ctrl.getDataSeparatorEntryVariable())
            if (dataSeparator == ''):
                self.__ctrl.buttonCancelHandler()
            self.__ctrl.setDataSeparatorEntryVariable(dataSeparator)
            dataEncoding = scribus.valueDialog('Data Encoding:', 'typically UTF-8', self.__ctrl.getDataEncodingEntryVariable())
            self.__ctrl.setDataEncodingEntryVariable(dataEncoding)
            result = scribus.messageBox('Use Partial Data? (optional)', 'If you select Yes you will be asked to enter from-to in the next dialogs', scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
            if (result == scribus.BUTTON_YES):
                fromEntry = scribus.valueDialog('Use Partial Data', 'FROM:', self.__ctrl.getFromVariable())
                toEntry = scribus.valueDialog('Use Partial Data', 'TO:', self.__ctrl.getToVariable())
            else:
                fromEntry = ''
                toEntry = ''
            self.__ctrl.setFromVariable(fromEntry)
            self.__ctrl.setToVariable(toEntry)
            outputDirectory = scribus.fileDialog('Select Output Directory', '', defaultname=self.__ctrl.getOutputDirectoryEntryVariable(), isdir=True)
            self.__ctrl.setOutputDirectoryEntryVariable(outputDirectory)
            outputFileName = scribus.valueDialog('Output File Name', 'Enter output file name without extension.\nYou can also include a %VAR_name% from your data file.\nIf you leave this blank file name will be an incremented number.', self.__ctrl.getOutputFileNameEntryVariable())
            # if output file name has no VAR from data file use VAR_COUNT to prevent multiple files overwriting each other
            if outputFileName != '' and "%VAR_" not in outputFileName:
                outputFileName = outputFileName + "%VAR_COUNT%"
            self.__ctrl.setOutputFileNameEntryVariable(outputFileName)
            result = scribus.valueDialog('File Format','Set Output File Format (PDF or SLA)','PDF')
            if (result == 'SLA'):
                outputFormat = CONST.FORMAT_SLA
            else:
                outputFormat = CONST.FORMAT_PDF
            self.__ctrl.setSelectedOutputFormat(outputFormat)
            result = scribus.messageBox('Merge','Do you want to merge into a single file?',scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
            if (result == scribus.BUTTON_YES):
                mergeOutput = 1
            else:
                mergeOutput = 0
            self.__ctrl.setMergeOutputVariable(mergeOutput)
            result = scribus.messageBox('Keep Files', 'Do you want to keep the generated Scribus files?', scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
            if (result == scribus.BUTTON_YES):
                keepScribusFiles = 1
            else:
                keepScribusFiles = 0
            self.__ctrl.setKeepGeneratedScribusFilesVariable(keepScribusFiles)
            result = scribus.messageBox('Close Generator', 'Do you want to close Generator after this operation succeeds?\n', scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
            if (result == scribus.BUTTON_YES):
                closeDialog = 1
            else:
                closeDialog = 0
            self.__ctrl.setCloseDialogVariable(closeDialog)
            result = scribus.messageBox('Save Settings','Would you like to save these settings?', scribus.ICON_NONE, scribus.BUTTON_YES, scribus.BUTTON_NO)
            if (result == scribus.BUTTON_YES):
                saveSettings = 1
            else:
                saveSettings = 0
            self.__ctrl.setSaveSettingsVariable(saveSettings)
            result = scribus.messageBox('Scribus Generator','Generate new document(s) from template and data file?', scribus.ICON_NONE, scribus.BUTTON_OK, scribus.BUTTON_CANCEL)
            if (result == scribus.BUTTON_OK):
                self.__ctrl.buttonOkHandler()
            else:
                self.__ctrl.buttonCancelHandler()


def main(argv):
    ctrl = GeneratorControl()
    dlg = GeneratorDialog(ctrl)
    dlg.show()

def main_wrapper(argv):
    try:
        if(scribus.haveDoc()):
            scribus.setRedraw(False)
        scribus.statusMessage(CONST.APP_NAME)
        scribus.progressReset()
        main(argv)

    finally:
        # Exit neatly even if the script terminated with an exception,
        # so we leave the progress bar and status bar blank and make sure
        # drawing is enabled.
        if(scribus.haveDoc()):
            scribus.setRedraw(True)
        scribus.statusMessage('')
        scribus.progressReset()


if __name__ == '__main__':
    main_wrapper(sys.argv)
