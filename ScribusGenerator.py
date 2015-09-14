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
# v2.0 (2015-08-03): command-line support
# v1.1 (2014-10-01): Add support for overwriting attributes from data (eg text/area color)
# v1.0 (2012-01-07): Fixed problems when using an ampersand as values within CSV-data.
# v2011-01-18: Changed run() so that scribus- and pdf file creation an deletion works without problems.
# v2011-01-17: Fixed the ampersand ('&') problem. It now can be used within variables.
# v2011-01-01: Initial Release.
#
"""
The MIT License
Copyright (c) 2010-2014 Ekkehard Will (www.ekkehardwill.de), 2014 Berteh (https://github.com/berteh/)
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import ScribusGeneratorBackend
from ScribusGeneratorBackend import CONST, ScribusGenerator, GeneratorDataObject
import Tkinter
from Tkinter import Frame, LabelFrame, Label, Entry, Button, StringVar, OptionMenu, Checkbutton, IntVar
import os
import traceback
import scribus
import sys
import tkMessageBox
import tkFileDialog


class GeneratorControl:
    # Controler being the bridge between UI and Logic.
    def __init__(self, root):
        self.__dataSourceFileEntryVariable = StringVar()
        self.__scribusSourceFileEntryVariable = StringVar()
        self.__dataSeparatorEntryVariable = StringVar()
        self.__dataSeparatorEntryVariable.set(CONST.CSV_SEP)
        self.__outputDirectoryEntryVariable = StringVar()
        self.__outputFileNameEntryVariable = StringVar()
        self.__outputFormatList = [CONST.FORMAT_PDF, CONST.FORMAT_SLA] # SLA & PDF are valid output format
        self.__selectedOutputFormat = StringVar()
        self.__selectedOutputFormat.set(CONST.FORMAT_PDF)
        self.__keepGeneratedScribusFilesCheckboxVariable = IntVar()
        self.__mergeOutputCheckboxVariable = IntVar()
        self.__fromVariable = StringVar()
        self.__fromVariable.set(CONST.EMPTY)
        self.__toVariable = StringVar()
        self.__toVariable.set(CONST.EMPTY)
        self.__root = root
        if scribus.haveDoc():
            doc = scribus.getDocName()
            self.__scribusSourceFileEntryVariable.set(doc)
            self.__outputDirectoryEntryVariable.set(os.path.split(doc)[0])
            self.__dataSourceFileEntryVariable.set(os.path.splitext(doc)[0]+".csv")
        
    
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

    def getDataSeparatorEntryVariable(self):
        return self.__dataSeparatorEntryVariable
        
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
    
    def getMergeOutputCheckboxVariable(self):
        return self.__mergeOutputCheckboxVariable
  
    def getFromVariable(self):
        return self.__fromVariable
  
    def getToVariable(self):
        return self.__toVariable

    def allValuesSet(self):
        # Simple check whether input fields are NOT EMPTY.
        # The user could fill in crap into the input fields. This would lead to an error, but crap in crap out!
        result = 0
        if((self.__scribusSourceFileEntryVariable.get() != CONST.EMPTY) and 
            (self.__dataSourceFileEntryVariable.get() != CONST.EMPTY) and 
            (self.__outputDirectoryEntryVariable.get() != CONST.EMPTY) and
            (len(self.__dataSeparatorEntryVariable.get()) == 1)):
            result = 1
        return result
    
    def createGeneratorDataObject(self):
        # Collect the settings the user has made and build the Data Object
        result = GeneratorDataObject(
            scribusSourceFile = self.__scribusSourceFileEntryVariable.get(),
            dataSourceFile = self.__dataSourceFileEntryVariable.get(),
            outputDirectory = self.__outputDirectoryEntryVariable.get(),
            outputFileName = self.__outputFileNameEntryVariable.get(),
            outputFormat = self.__selectedOutputFormat.get(),
            keepGeneratedScribusFiles = self.__keepGeneratedScribusFilesCheckboxVariable.get(),
            csvSeparator = self.__dataSeparatorEntryVariable.get(), 
            singleOutput = self.__mergeOutputCheckboxVariable.get(),
            firstRow = self.__fromVariable.get(),
            lastRow = self.__toVariable.get()
            )
        return result
    
    def buttonCancelHandler(self):
        self.__root.destroy()
    
    def buttonOkHandler(self):
        if (CONST.TRUE == self.allValuesSet()):
            dataObject = self.createGeneratorDataObject()
            generator = ScribusGenerator(dataObject)
            try:
                generator.run() 
                tkMessageBox.showinfo('Scribus Generator', message='Done. Generated files are in '+dataObject.getOutputDirectory())
            except ValueError as e:
                tkMessageBox.showerror(title='Error Scribus Generator', message="Could likely not replace a variable with its value,\nplease check your Data File and Data Separator settings.\n moreover: "+e.message+"\n")
            except IndexError as e:
                tkMessageBox.showerror(title='Error Scribus Generator', message="Could not find the value for one variable.\nplease check your Data File and Data Separator settings.\n moreover: "+e.message+"\n")
            except Exception:
                tkMessageBox.showerror(title='Error Scribus Generator', message="Something went wrong\nRead the log file for more\n."+traceback.format_exc())

        else:
            tkMessageBox.showerror(title='Validation failed', message='Please check if all settings have been set correctly!')
    
    def helpButtonHandler(self):
        tkMessageBox.showinfo('Help', message="More information at :\nhttps://github.com/berteh/ScribusGenerator/")
 
class GeneratorDialog:
    # The UI to configure the settings by the user
    def __init__(self, root, ctrl):
        self.__root = root
        self.__ctrl = ctrl

    #    def updateDisabled(self, value, label, button):
    #        if (value is CONST.FORMAT_SLA) :
    #            label.configure(state='disabled')
    #            button.configure(state='disabled')
    #        else :
    #            label.configure(state='normal')
    #            button.configure(state='normal')

    
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
        scribusSourceFileEntry = Entry(inputFrame, textvariable=self.__ctrl.getScribusSourceFileEntryVariable())
        scribusSourceFileEntry.grid(column=1, columnspan=4, row=0, padx=5, pady=5, sticky='ew')
        scribusSourceFileButton = Button(inputFrame, text='...', command=self.__ctrl.scribusSourceFileEntryVariableHandler)
        scribusSourceFileButton.grid(column=5, row=0, padx=5, pady=5, sticky='e')
        
        dataSourceFileLabel = Label(inputFrame, text='Data File:', width=15, anchor='w')
        dataSourceFileLabel.grid(column=0, row=1, padx=5, pady=5, sticky='w')
        dataSourceFileEntry = Entry(inputFrame, textvariable=self.__ctrl.getDataSourceFileEntryVariable())
        dataSourceFileEntry.grid(column=1, columnspan=4, row=1, padx=5, pady=5, sticky='ew')
        dataSourceFileButton = Button(inputFrame, text='...', command=self.__ctrl.dataSourceFileEntryVariableHandler)
        dataSourceFileButton.grid(column=5, row=1, padx=5, pady=5, sticky='e')
        
        dataSeparatorLabel = Label(inputFrame, text='Data Field Separator:', width=15, anchor='w')
        dataSeparatorLabel.grid(column=0, row=2, padx=5, pady=5, sticky='w')
        dataSeparatorEntry = Entry(inputFrame, width=3, textvariable=self.__ctrl.getDataSeparatorEntryVariable())
        dataSeparatorEntry.grid(column=1, row=2, padx=5, pady=5, sticky='w')

        fromLabel = Label(inputFrame, text='(opt.) use partial data, only from:', anchor='e')
        fromLabel.grid(column=2, row=2, padx=5, pady=5, sticky='e')
        fromEntry = Entry(inputFrame, width=3, textvariable=self.__ctrl.getFromVariable())
        fromEntry.grid(column=3, row=2, padx=5, pady=5, sticky='w')

        toLabel = Label(inputFrame, text='to:', width=3, anchor='e')
        toLabel.grid(column=4, row=2, padx=5, pady=5, sticky='e')
        toEntry = Entry(inputFrame, width=3, textvariable=self.__ctrl.getToVariable())
        toEntry.grid(column=5, row=2, padx=5, pady=5, sticky='w')

        #rangeHelp = Label(inputFrame, text='(set to 0 to neglect)', width=30, anchor='w')
        #rangeHelp.grid(column=4, columnspan=2,  row=4, padx=5, pady=5, sticky='w')
   


        # Output-Settings
        outputDirectoryLabel = Label(outputFrame, text='Output Directory:', width=15, anchor='w')
        outputDirectoryLabel.grid(column=0, row=0, padx=5, pady=5, sticky='w')
        outputDirectoryEntry = Entry(outputFrame, textvariable=self.__ctrl.getOutputDirectoryEntryVariable())
        outputDirectoryEntry.grid(column=1, columnspan=4, row=0, padx=5, pady=5, sticky='ew')
        outputDirectoryButton = Button(outputFrame, text='...', command=self.__ctrl.outputDirectoryEntryVariableHandler)
        outputDirectoryButton.grid(column=5, row=0, padx=5, pady=5, sticky='e')
        
        outputFileNameLabel = Label(outputFrame, text='Output File Name:', width=15, anchor='w')
        outputFileNameLabel.grid(column=0, row=1, padx=5, pady=5, sticky='w')
        outputFileNameEntry = Entry(outputFrame, textvariable=self.__ctrl.getOutputFileNameEntryVariable())
        outputFileNameEntry.grid(column=1, columnspan=4, row=1, padx=5, pady=5, sticky='ew')
         
        mergeOutputLabel = Label(outputFrame, text='Merge in Single File:', width=15, anchor='w')
        mergeOutputLabel.grid(column=0, row=2, padx=5, pady=5, sticky='w')
        mergeOutputCheckbox = Checkbutton(outputFrame, variable=self.__ctrl.getMergeOutputCheckboxVariable())
        mergeOutputCheckbox.grid(column=1, row=2, padx=5, pady=5, sticky='w')  

        outputFormatLabel = Label(outputFrame, text='Output Format:', anchor='e')
        outputFormatLabel.grid(column=2, row=2, padx=5, pady=5, sticky='e')
        outputFormatListBox = OptionMenu(outputFrame, self.__ctrl.getSelectedOutputFormat(), *self.__ctrl.getOutputFormatList()) #,
            #command=lambda l=keepGeneratedScribusFilesLabel, c=keepGeneratedScribusFilesCheckbox, v=self.__ctrl.getSelectedOutputFormat(): self.updateDisabled(v, l,c))
        outputFormatListBox.grid(column=3, row=2, padx=5, pady=5, sticky='w')
      
        keepGeneratedScribusFilesLabel = Label(outputFrame, text='Keep Scribus Files:', width=15, anchor='e')
        keepGeneratedScribusFilesLabel.grid(column=4, row=2, padx=5, pady=5, sticky='e')
        keepGeneratedScribusFilesCheckbox = Checkbutton(outputFrame, variable=self.__ctrl.getKeepGeneratedScribusFilesCheckboxVariable(), anchor='w')
        keepGeneratedScribusFilesCheckbox.grid(column=5, row=2, padx=5, pady=5, sticky='w')

       

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