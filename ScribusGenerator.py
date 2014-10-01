#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Scribus Generator will
# - read CSV Data
# - convert a given Scribus File to a
# - specified Output Format (for each row of data) and
# - save the Output File as well as the generated Scribus File (which optional)
#
# For further information (manual, description, etc.) please visit:
# www.ekkehardwill.de/sg
#
# Version v2012-01-07: Fixed problems when using an ampersand as values within CSV-data.
# Version v2011-01-18: Changed run() so that scribus- and pdf file creation an deletion works without problems.
# Version v2011-01-17: Fixed the ampersand ('&') problem. It now can be used within variables.
# Version v2011-01-01: Initial Release.

import Tkinter
from Tkinter import Frame, LabelFrame, Label, Entry, Button, StringVar, OptionMenu, Checkbutton, IntVar
import csv
import os
import logging
import traceback
import scribus
import sys
import tkMessageBox
import tkFileDialog

class CONST:
    # Constants for general usage
    TRUE = 1
    FALSE = 0
    EMPTY = ''
    APP_NAME = 'Scribus Generator'
    FORMAT_PDF = 'PDF'
    FILE_EXTENSION_PDF = 'pdf'
    FILE_EXTENSION_SCRIBUS = 'sla'
    SEP_PATH = '/'  # In any case we use '/' as path separator on any platform
    SEP_EXT = os.extsep
    LOG_LEVEL = logging.INFO # Use logging.DEBUG for loggin any problems occured 
    
class ScribusGenerator:
    # The Generator Module has all the logic and will do all the work
    def __init__(self, dataObject):
        self.__dataObject = dataObject
        #logging.basicConfig(level=CONST.LOG_LEVEL, filename='ScribusGenerator.log', format='%(asctime)s - %(name)s - %(levelname)s - Function: %(funcName)s - Line: %(lineno)d Msg: %(message)s')

    
    def run(self):
        # Read CSV data and replace the variables in the Scribus File with the cooresponding data. Finaly export to the specified format.
        try:
            csvData = self.getCsvData(self.__dataObject.getDataSourceFile())
            template = [] # XML-Content/Text-Content of the Source Scribus File (List of Lines)
            outputFileNames = []
            index = 0
            # Generate the Scribus Files
            for row in csvData:
                if(index == 0): # Do this only for the first line which is the Header-Row of the CSV-File
                    headerRowForFileName = row
                    #logging.debug('Before conversion: ' + str(row))
                    headerRowForReplacingVariables = self.handleAmpersand(row) # Header-Row contains the variable names
                    #logging.debug('After conversion: ' + str(headerRowForReplacingVariables))
                    # Copy the original/given Scribus file to a temporary file which acts as a template
                    template = self.copyScribusContent(self.readFileContent(self.__dataObject.getScribusSourceFile()))
                else:
                    outContent = self.replaceVariablesWithCsvData(headerRowForReplacingVariables, self.handleAmpersand(row), self.copyScribusContent(template))
                    #logging.debug('Replaced Variables With Csv Data')
                    outputFileName = self.createOutputFileName(index, self.__dataObject.getOutputFileName(), headerRowForFileName, row)
                    scribusOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                    self.exportSLA(scribusOutputFilePath, outContent)
                    outputFileNames.append(outputFileName)
                    #logging.debug('Scribus File CREATED: ' + str(scribusOutputFilePath))
                index = index + 1
            
            # Export the generated Scribus Files as PDF
            if(CONST.FORMAT_PDF == self.__dataObject.getOutputFormat()):
                for outputFileName in outputFileNames:
                    pdfOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_PDF)
                    scribusOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                    self.exportPDF(scribusOutputFilePath, pdfOutputFilePath)
            
            # Cleanup the generated Scribus Files
            if(CONST.FALSE == self.__dataObject.getKeepGeneratedScribusFiles()):
                for outputFileName in outputFileNames:
                    scribusOutputFilePath = self.createOutputFilePath(self.__dataObject.getOutputDirectory(), outputFileName, CONST.FILE_EXTENSION_SCRIBUS)
                    self.deleteFile(scribusOutputFilePath)
                        
        except Exception:
            tkMessageBox.showerror(message=traceback.format_exc())
            

    def exportPDF(self, scribusFilePath, pdfFilePath):
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

    def exportSLA(self, outputFilePath, content):
        # Export to SLA (Scribus Format)
        result = open(outputFilePath, 'w')
        result.writelines(content)
        result.flush()
        os.fsync(result.fileno())
        result.close()
    
    def deleteFile(self, outputFilePath):
        # Delete the temporarily generated files from off the file system
        os.remove(outputFilePath)

    def createOutputFilePath(self, outputDirectory, outputFileName, fileExtension):
        # Build the absolute path, like C:/tmp/template.sla
        return outputDirectory + CONST.SEP_PATH + outputFileName + CONST.SEP_EXT + fileExtension
    
    def createOutputFileName(self, index, outputFileName, headerRow, row):
        # If the User has not set an Output File Name, an internal unique file name
        # will be generated which is the index of the loop.
        result = str(index)
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
                result = self.replaceVariablesWithCsvData(headerRow, row, [outputFileName])
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
            result.append(i.replace('&', '&amp;'))
        return result
    
    
    def replaceVariablesWithCsvData(self, headerRow, row, lines): # lines as list of strings
        result = ''
        for line in lines:
            i = 0
            for cell in row:
                tmp = ('%VAR_' + headerRow[i] + '%')
                line = line.replace(tmp, cell) # string.replace(old, new)
                i = i + 1
            result = result + line
        return result
         
    def getCsvData(self, csvfile):
        # Read CSV file and return  2-dimensional list containing the data
        reader = csv.reader(file(csvfile))
        result = []
        for row in reader:
            rowlist = []
            for col in row:
                rowlist.append(col)
            result.append(rowlist)
        return result

class GeneratorDataObject:
    # Data Object for transfering the settings made by the user on the UI
    def __init__(self):
        self.__sribusSourceFile = CONST.EMPTY
        self.__dataSourceFile = CONST.EMPTY
        self.__outputDirectory = CONST.EMPTY
        self.__outputFileName = CONST.EMPTY
        self.__outputFormat = CONST.EMPTY
        self.__keepGeneratedScribusFiles = CONST.FALSE
    
    # Get
    def getScribusSourceFile(self):
        return self.__sribusSourceFile
    
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
    
    # Set
    def setScribusSourceFile(self, fileName):
        self.__sribusSourceFile = fileName
        
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
        
class GeneratorControl:
    # Controler being the bridge between UI and Logic.
    def __init__(self, root):
        self.__dataSourceFileEntryVariable = StringVar()
        self.__scribusSourceFileEntryVariable = StringVar()
        self.__outputDirectoryEntryVariable = StringVar()
        self.__outputFileNameEntryVariable = StringVar()
        self.__outputFormatList = (CONST.FORMAT_PDF) # at the moment only PDF is a valid output format
        self.__selectedOutputFormat = StringVar()
        self.__selectedOutputFormat.set(self.__outputFormatList)
        self.__keepGeneratedScribusFilesCheckboxVariable = IntVar()
        self.__root = root
    
    def getDataSourceFileEntryVariable(self):
        return self.__dataSourceFileEntryVariable
    
    def dataSourceFileEntryVariableHandler(self):
        result = tkFileDialog.askopenfilename(title='Choose...', defaultextension='.csv', filetypes=[('CSV', '*.csv *.CSV')])
        if result:
            self.__dataSourceFileEntryVariable.set(result)
        
    def getScribusSourceFileEntryVariable(self):
        return self.__scribusSourceFileEntryVariable
    
    def scribusSourceFileEntryVariableHandler(self):
        # Important: Only sla should be allowed as this is plain XML.
        # E.g. zipped sla.gz files will lead to an error.
        result = tkFileDialog.askopenfilename(title='Choose...', defaultextension='.sla', filetypes=[('SLA', '*.sla *.SLA')])
        if result:
            self.__scribusSourceFileEntryVariable.set(result)
        
    def getOutputDirectoryEntryVariable(self):
        return self.__outputDirectoryEntryVariable
    
    def outputDirectoryEntryVariableHandler(self):
        result = tkFileDialog.askdirectory()
        if result:
            self.__outputDirectoryEntryVariable.set(result)
        
    def getOutputFileNameEntryVariable(self):
        return self.__outputFileNameEntryVariable
        
    def getOutputFormatList(self):
        return self.__outputFormatList
    
    def getSelectedOutputFormat(self):
        return self.__selectedOutputFormat
    
    def getKeepGeneratedScribusFilesCheckboxVariable(self):
        return self.__keepGeneratedScribusFilesCheckboxVariable
    
    def allValuesSet(self):
        # Simple check whether input fields are NOT EMPTY.
        # The user could fill in crap into the input fields. This would lead to an error, but crap in crap out!
        result = 0
        if((self.__scribusSourceFileEntryVariable.get() != CONST.EMPTY) and (self.__dataSourceFileEntryVariable.get() != CONST.EMPTY) and (self.__outputDirectoryEntryVariable.get() != CONST.EMPTY)):
            result = 1
        return result
    
    def createGeneratorDataObject(self):
        # Collect the settings the user has made and build the Data Object
        result = GeneratorDataObject()
        result.setScribusSourceFile(self.__scribusSourceFileEntryVariable.get())
        result.setDataSourceFile(self.__dataSourceFileEntryVariable.get())
        result.setOutputDirectory(self.__outputDirectoryEntryVariable.get())
        result.setOutputFileName(self.__outputFileNameEntryVariable.get())
        result.setOutputFormat(self.__selectedOutputFormat.get())
        result.setKeepGeneratedScribusFiles(self.__keepGeneratedScribusFilesCheckboxVariable.get())
        return result
    
    def buttonCancelHandler(self):
        self.__root.destroy()
    
    def buttonOkHandler(self):
        if (CONST.TRUE == self.allValuesSet()):
            dataObject = self.createGeneratorDataObject()
            generator = ScribusGenerator(dataObject)
            generator.run()
        else:
            tkMessageBox.showerror(title='Validation failed', message='Please check if all settings have been set correctly!')
    
    def helpButtonHandler(self):
        tkMessageBox.showinfo('Help', message='For any information please visit: www.ekkehardwill.de/sg')
 
class GeneratorDialog:
    # The UI to configure the settings by the user
    def __init__(self, root, ctrl):
        self.__root = root
        self.__ctrl = ctrl
    
    def show(self):
        self.__root.title(CONST.APP_NAME)
        mainFrame = Frame(self.__root)
        # Make Dialog stretchable (to EAST and WEST)
        top = mainFrame.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        mainFrame.rowconfigure(0, weight=1)
        mainFrame.columnconfigure(0, weight=1)
        mainFrame.grid(sticky='ew')
        
        # Three Sections: Input-Settings, Output-Settings and Buttons
        inputFrame = LabelFrame(mainFrame, text='Input Settings')
        inputFrame.columnconfigure(1, weight=1)
        inputFrame.grid(column=0, row=0, padx=5, pady=5, sticky='ew')
        outputFrame = LabelFrame(mainFrame, text='Output Settings')
        outputFrame.columnconfigure(1, weight=1)
        outputFrame.grid(column=0, row=1, padx=5, pady=5, sticky='ew')
        buttonFrame = Frame(mainFrame)
        buttonFrame.grid(column=0, row=2, padx=5, pady=5, sticky='e')
        
        # Input-Settings
        scribusSourceFileLabel = Label(inputFrame, text='Scribus File:', width=15, anchor='w')
        scribusSourceFileLabel.grid(column=0, row=0, padx=5, pady=5, sticky='w')
        scribusSourceFileEntry = Entry(inputFrame, width=70, textvariable=self.__ctrl.getScribusSourceFileEntryVariable())
        scribusSourceFileEntry.grid(column=1, row=0, padx=5, pady=5, sticky='ew')
        scribusSourceFileButton = Button(inputFrame, text='...', command=self.__ctrl.scribusSourceFileEntryVariableHandler)
        scribusSourceFileButton.grid(column=2, row=0, padx=5, pady=5, sticky='e')
        
        dataSourceFileLabel = Label(inputFrame, text='Data File:', width=15, anchor='w')
        dataSourceFileLabel.grid(column=0, row=1, padx=5, pady=5, sticky='w')
        dataSourceFileEntry = Entry(inputFrame, width=70, textvariable=self.__ctrl.getDataSourceFileEntryVariable())
        dataSourceFileEntry.grid(column=1, row=1, padx=5, pady=5, sticky='ew')
        dataSourceFileButton = Button(inputFrame, text='...', command=self.__ctrl.dataSourceFileEntryVariableHandler)
        dataSourceFileButton.grid(column=2, row=1, padx=5, pady=5, sticky='e')
        
        # Output-Settings
        outputDirectoryLabel = Label(outputFrame, text='Output Directory:', width=15, anchor='w')
        outputDirectoryLabel.grid(column=0, row=0, padx=5, pady=5, sticky='w')
        outputDirectoryEntry = Entry(outputFrame, width=70, textvariable=self.__ctrl.getOutputDirectoryEntryVariable())
        outputDirectoryEntry.grid(column=1, row=0, padx=5, pady=5, sticky='ew')
        outputDirectoryButton = Button(outputFrame, text='...', command=self.__ctrl.outputDirectoryEntryVariableHandler)
        outputDirectoryButton.grid(column=2, row=0, padx=5, pady=5, sticky='e')
        
        outputFileNameLabel = Label(outputFrame, text='Output File Name:', width=15, anchor='w')
        outputFileNameLabel.grid(column=0, row=1, padx=5, pady=5, sticky='w')
        outputFileNameEntry = Entry(outputFrame, width=70, textvariable=self.__ctrl.getOutputFileNameEntryVariable())
        outputFileNameEntry.grid(column=1, row=1, padx=5, pady=5, sticky='ew')
        
        outputFormatLabel = Label(outputFrame, text='Output Format:', width=15, anchor='w')
        outputFormatLabel.grid(column=0, row=2, padx=5, pady=5, sticky='w')
        outputFormatListBox = OptionMenu(outputFrame, self.__ctrl.getSelectedOutputFormat(), self.__ctrl.getOutputFormatList())
        outputFormatListBox.grid(column=1, row=2, padx=5, pady=5, sticky='w')
        
        keepGeneratedScribusFilesLabel = Label(outputFrame, text='Keep Scribus Files:', width=15, anchor='w')
        keepGeneratedScribusFilesLabel.grid(column=0, row=3, padx=5, pady=5, sticky='w')
        keepGeneratedScribusFilesCheckbox = Checkbutton(outputFrame, variable=self.__ctrl.getKeepGeneratedScribusFilesCheckboxVariable())
        keepGeneratedScribusFilesCheckbox.grid(column=1, row=3, padx=5, pady=5, sticky='w')
        
        # Buttons to Cancel or to Run the Generator with the given Settings
        helpButton = Button(buttonFrame, text='Help', width=10, command=self.__ctrl.helpButtonHandler)
        helpButton.grid(column=0, row=0, padx=5, pady=5, sticky='e')
        cancelButton = Button(buttonFrame, text='Cancel', width=10, command=self.__ctrl.buttonCancelHandler)
        cancelButton.grid(column=1, row=0, padx=5, pady=5, sticky='e')
        generateButton = Button(buttonFrame, text='Generate', width=10, command=self.__ctrl.buttonOkHandler)
        generateButton.grid(column=2, row=0, padx=5, pady=5, sticky='e')
        
        # Finally show the Generator Dialog
        mainFrame.grid()
        self.__root.grid()
        self.__root.mainloop()

def main(argv):
    root = Tkinter.Tk()
    ctrl = GeneratorControl(root)
    dlg = GeneratorDialog(root, ctrl)
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
    
"""
The MIT License
Copyright (c) 2010 and beyond Ekkehard Will (www.ekkehardwill.de)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
