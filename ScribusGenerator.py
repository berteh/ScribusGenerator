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
from Tkinter import Frame, LabelFrame, Label, Entry, Button, StringVar, OptionMenu, Checkbutton, IntVar, DISABLED, NORMAL, PhotoImage
import tkMessageBox
import tkFileDialog

import scribus
import os
import sys
import inspect
import traceback


class GeneratorControl:
    # Controler being the bridge between UI and Logic.
    def __init__(self, root):
        self.__dataSourceFileEntryVariable = StringVar()
        self.__scribusSourceFileEntryVariable = StringVar()
        self.__dataSeparatorEntryVariable = StringVar()
        self.__dataSeparatorEntryVariable.set(CONST.CSV_SEP)
        self.__outputDirectoryEntryVariable = StringVar()
        self.__outputFileNameEntryVariable = StringVar()
        # SLA & PDF are valid output format
        self.__outputFormatList = [CONST.FORMAT_PDF, CONST.FORMAT_SLA]
        self.__selectedOutputFormat = StringVar()
        self.__selectedOutputFormat.set(CONST.FORMAT_PDF)
        self.__keepGeneratedScribusFilesCheckboxVariable = IntVar()
        self.__mergeOutputCheckboxVariable = IntVar()
        self.__saveCheckboxVariable = IntVar()
        self.__fromVariable = StringVar()
        self.__fromVariable.set(CONST.EMPTY)
        self.__toVariable = StringVar()
        self.__toVariable.set(CONST.EMPTY)
        self.__root = root
        if scribus.haveDoc():
            doc = scribus.getDocName()
            self.__scribusSourceFileEntryVariable.set(doc)
            self.__outputDirectoryEntryVariable.set(os.path.split(doc)[0])
            self.__dataSourceFileEntryVariable.set(
                os.path.splitext(doc)[0]+".csv")

    def getDataSourceFileEntryVariable(self):
        return self.__dataSourceFileEntryVariable

    def dataSourceFileEntryVariableHandler(self):
        result = tkFileDialog.askopenfilename(title='Choose...', defaultextension='.csv', filetypes=[(
            'CSV - comma separated values', '*.csv *.CSV'), ('TSV - tab separated values', '*.tsv *.TSV'), ('TXT - text', '*.txt *.TXT'), ('all', '*.*')], initialdir=os.path.dirname(self.__dataSourceFileEntryVariable.get()))
        if result:
            self.__dataSourceFileEntryVariable.set(result)
        # todo: opt update separator to tab if tsv is selected?

    def getScribusSourceFileEntryVariable(self):
        return self.__scribusSourceFileEntryVariable

    def scribusSourceFileEntryVariableHandler(self):
        # Important: Only sla should be allowed as this is plain XML.
        # E.g. zipped sla.gz files will lead to an error.
        result = tkFileDialog.askopenfilename(
            title='Choose...', defaultextension='.sla', filetypes=[('SLA', '*.sla *.SLA')], initialdir=os.path.dirname(self.__scribusSourceFileEntryVariable.get()))
        if result:
            self.__scribusSourceFileEntryVariable.set(result)

    def getDataSeparatorEntryVariable(self):
        return self.__dataSeparatorEntryVariable

    def getOutputDirectoryEntryVariable(self):
        return self.__outputDirectoryEntryVariable

    def outputDirectoryEntryVariableHandler(self):
        result = tkFileDialog.askdirectory(initialdir=self.__outputDirectoryEntryVariable.get())
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

    def getSaveCheckboxVariable(self):
        return self.__saveCheckboxVariable

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
            scribusSourceFile=self.__scribusSourceFileEntryVariable.get(),
            dataSourceFile=self.__dataSourceFileEntryVariable.get(),
            outputDirectory=self.__outputDirectoryEntryVariable.get(),
            outputFileName=self.__outputFileNameEntryVariable.get(),
            outputFormat=self.__selectedOutputFormat.get(),
            keepGeneratedScribusFiles=self.__keepGeneratedScribusFilesCheckboxVariable.get(),
            csvSeparator=self.__dataSeparatorEntryVariable.get(),
            singleOutput=self.__mergeOutputCheckboxVariable.get(),
            firstRow=self.__fromVariable.get(),
            lastRow=self.__toVariable.get(),
            saveSettings=self.__saveCheckboxVariable.get()
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
                tkMessageBox.showinfo(
                    'Scribus Generator', message='Done. Generated files are in '+dataObject.getOutputDirectory())
            except IOError as e:  # except FileNotFoundError as e:
                tkMessageBox.showerror(
                    title='File Not Found', message="Could not find some input file, please verify your Scribus and Data file settings:\n\n %s" % e)
            except ValueError as e:
                tkMessageBox.showerror(
                    title='Variable Error', message="Could likely not replace a variable with its value,\nplease check your Data File and Data Separator settings:\n\n %s" % e)
            except IndexError as e:
                tkMessageBox.showerror(
                    title='Variable Error', message="Could not find the value for one variable.\nplease check your Data File and Data Separator settings.\n\n %s" % e)
            except Exception:
                tkMessageBox.showerror(title='Error Scribus Generator',
                                       message="Something went wrong.\n\nRead the log file for more (in your home directory)."+traceback.format_exc())
        else:
            tkMessageBox.showerror(
                title='Validation failed', message='Please check if all settings have been set correctly!')

    def helpButtonHandler(self):
        tkMessageBox.showinfo(
            'Help', message="More information at :\nhttps://github.com/berteh/ScribusGenerator/")

    def scribusLoadSettingsHandler(self):
        slaFile = self.__scribusSourceFileEntryVariable.get()

        if(slaFile is CONST.EMPTY):
            tkMessageBox.showinfo(
                'Choose a file', message="Set a valid scribus input file prior to loading its settings.")
            return
        dataObject = GeneratorDataObject(
            scribusSourceFile=slaFile
        )
        generator = ScribusGenerator(dataObject)
        saved = generator.getSavedSettings()
        if (saved):
            dataObject.loadFromString(saved)
            # self.__scribusSourceFileEntryVariable = StringVar() #not loaded
            self.__dataSourceFileEntryVariable.set(
                dataObject.getDataSourceFile())
            self.__dataSeparatorEntryVariable.set(dataObject.getCsvSeparator())
            self.__outputDirectoryEntryVariable.set(
                dataObject.getOutputDirectory())
            self.__outputFileNameEntryVariable.set(
                dataObject.getOutputFileName())
            self.__selectedOutputFormat.set(dataObject.getOutputFormat())
            self.__keepGeneratedScribusFilesCheckboxVariable.set(
                dataObject.getKeepGeneratedScribusFiles())
            self.__mergeOutputCheckboxVariable.set(
                dataObject.getSingleOutput())
            # self.__saveCheckboxVariable = IntVar() #not loaded
            self.__fromVariable.set(dataObject.getFirstRow())
            self.__toVariable.set(dataObject.getLastRow())
        else:
            tkMessageBox.showinfo(
                'No Settings', message="Input scribus file contains no former saved settings.")


class GeneratorDialog:
    # The UI to configure the settings by the user
    def __init__(self, root, ctrl):
        self.__root = root
        self.__ctrl = ctrl
        self.__pluginDir = os.path.dirname(
            os.path.abspath(inspect.stack()[0][1]))
        for i in [self.__pluginDir + '/pic/ScribusGenerator_logo.gif', self.__pluginDir + '/ScribusGenerator_logo.gif']:
            if os.path.exists(i):
                try:
                    self.__ico = PhotoImage(file=i)
                    root.tk.call('wm', 'iconphoto', root._w, '-default', self.__ico)
                except Exception as e:
                    pass

    def show(self):
        self.__root.title(CONST.APP_NAME)
        mainFrame = Frame(self.__root)

        top = mainFrame.winfo_toplevel()
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        mainFrame.rowconfigure(0, weight=1)
        mainFrame.columnconfigure(0, weight=1)
        mainFrame.grid(sticky='ew')

        # Three Sections: Input-Settings, Output-Settings and Buttons
        inputFrame = LabelFrame(mainFrame, text='Input Settings')
        inputFrame.columnconfigure(2, weight=1)
        inputFrame.grid(column=0, row=0, padx=5, pady=5, sticky='ew')
        outputFrame = LabelFrame(mainFrame, text='Output Settings')
        outputFrame.columnconfigure(2, weight=1)
        outputFrame.grid(column=0, row=1, padx=5, pady=5, sticky='ew')
        buttonFrame = Frame(mainFrame)
        buttonFrame.columnconfigure(3, weight=1)
        buttonFrame.grid(column=0, row=2, padx=5, pady=5, sticky='ew')

        # Input-Settings
        scribusSourceFileLabel = Label(
            inputFrame, text='Scribus File:', width=15, anchor='w')
        scribusSourceFileLabel.grid(
            column=0, row=0, padx=5, pady=5, sticky='w')
        scribusSourceFileEntry = Entry(
            inputFrame, textvariable=self.__ctrl.getScribusSourceFileEntryVariable())
        scribusSourceFileEntry.grid(
            column=1, columnspan=3, row=0, padx=5, pady=5, sticky='ew')
        scribusSourceFileButton = Button(
            inputFrame, text='⏏', command=self.__ctrl.scribusSourceFileEntryVariableHandler)
        scribusSourceFileButton.grid(
            column=4, row=0, padx=5, pady=5, sticky='e')
        scribusLoadSettingsButton = Button(
            inputFrame, text='↺', command=self.__ctrl.scribusLoadSettingsHandler)  # ⟲ ⟳ ↻ ↺ ⌂ ⌘ ⎗
        scribusLoadSettingsButton.grid(
            column=5, row=0, padx=5, pady=5, sticky='e')

        dataSourceFileLabel = Label(
            inputFrame, text='Data File:', width=15, anchor='w')
        dataSourceFileLabel.grid(column=0, row=1, padx=5, pady=5, sticky='w')
        dataSourceFileEntry = Entry(
            inputFrame, textvariable=self.__ctrl.getDataSourceFileEntryVariable())
        dataSourceFileEntry.grid(
            column=1, columnspan=4, row=1, padx=5, pady=5, sticky='ew')
        dataSourceFileButton = Button(
            inputFrame, text='⏏', command=self.__ctrl.dataSourceFileEntryVariableHandler)
        dataSourceFileButton.grid(column=5, row=1, padx=5, pady=5, sticky='e')

        dataSeparatorLabel = Label(
            inputFrame, text='Data Field Separator:', width=15, anchor='w')
        dataSeparatorLabel.grid(column=0, row=2, padx=5, pady=5, sticky='w')
        dataSeparatorEntry = Entry(
            inputFrame, width=3, textvariable=self.__ctrl.getDataSeparatorEntryVariable())
        dataSeparatorEntry.grid(column=1, row=2, padx=5, pady=5, sticky='w')

        fromLabel = Label(
            inputFrame, text='(opt.) use partial data, only from:', anchor='e')
        fromLabel.grid(column=2, row=2, padx=5, pady=5, sticky='e')
        fromEntry = Entry(inputFrame, width=3,
                          textvariable=self.__ctrl.getFromVariable())
        fromEntry.grid(column=3, row=2, padx=5, pady=5, sticky='w')

        toLabel = Label(inputFrame, text='to:', width=3, anchor='e')
        toLabel.grid(column=4, row=2, padx=5, pady=5, sticky='e')
        toEntry = Entry(inputFrame, width=3,
                        textvariable=self.__ctrl.getToVariable())
        toEntry.grid(column=5, row=2, padx=5, pady=5, sticky='w')

        # Output-Settings
        outputDirectoryLabel = Label(
            outputFrame, text='Output Directory:', width=15, anchor='w')
        outputDirectoryLabel.grid(column=0, row=0, padx=5, pady=5, sticky='w')
        outputDirectoryEntry = Entry(
            outputFrame, textvariable=self.__ctrl.getOutputDirectoryEntryVariable())
        outputDirectoryEntry.grid(
            column=1, columnspan=4, row=0, padx=5, pady=5, sticky='ew')
        outputDirectoryButton = Button(
            outputFrame, text='⏏', command=self.__ctrl.outputDirectoryEntryVariableHandler)
        outputDirectoryButton.grid(column=5, row=0, padx=5, pady=5, sticky='e')

        outputFileNameLabel = Label(
            outputFrame, text='Output File Name:', width=15, anchor='w')
        outputFileNameLabel.grid(column=0, row=1, padx=5, pady=5, sticky='w')
        outputFileNameEntry = Entry(
            outputFrame, textvariable=self.__ctrl.getOutputFileNameEntryVariable())
        outputFileNameEntry.grid(
            column=1, columnspan=3, row=1, padx=5, pady=5, sticky='ew')

        saveLabel = Label(outputFrame, text='Save Settings:',
                          width=15, anchor='w')
        saveLabel.grid(column=4, row=1, padx=5, pady=5, sticky='w')
        saveCheckbox = Checkbutton(
            outputFrame, variable=self.__ctrl.getSaveCheckboxVariable())
        saveCheckbox.grid(column=5, row=1, padx=5, pady=5, sticky='w')

        mergeOutputLabel = Label(
            outputFrame, text='Merge in Single File:', width=15, anchor='w')
        mergeOutputLabel.grid(column=0, row=2, padx=5, pady=5, sticky='w')
        mergeOutputCheckbox = Checkbutton(
            outputFrame, variable=self.__ctrl.getMergeOutputCheckboxVariable())
        mergeOutputCheckbox.grid(column=1, row=2, padx=5, pady=5, sticky='w')

        self.keepGeneratedScribusFilesLabel = Label(
            outputFrame, text='Keep Scribus Files:', width=15, anchor='e')
        self.keepGeneratedScribusFilesLabel.grid(
            column=4, row=2, padx=5, pady=5, sticky='e')
        self.keepGeneratedScribusFilesCheckbox = Checkbutton(
            outputFrame, variable=self.__ctrl.getKeepGeneratedScribusFilesCheckboxVariable(), anchor='w')
        self.keepGeneratedScribusFilesCheckbox.grid(
            column=5, row=2, padx=5, pady=5, sticky='w')

        outputFormatLabel = Label(
            outputFrame, text='Output Format:', anchor='e')
        outputFormatLabel.grid(column=2, row=2, padx=5, pady=5, sticky='e')
        outputFormatListBox = OptionMenu(outputFrame, self.__ctrl.getSelectedOutputFormat(), *self.__ctrl.getOutputFormatList(),
                                         command=lambda v=self.__ctrl.getSelectedOutputFormat(): self.updateState(v))
        outputFormatListBox.grid(column=3, row=2, padx=5, pady=5, sticky='w')

        # Bottom Buttons
        generateButton = Button(
            buttonFrame, text='✔\nGenerate', width=10, command=self.__ctrl.buttonOkHandler)
        generateButton.grid(column=0, row=0, padx=5, pady=5, sticky='w')
        cancelButton = Button(buttonFrame, text='✘\nCancel',
                              width=10, command=self.__ctrl.buttonCancelHandler)
        cancelButton.grid(column=1, row=0, padx=5, pady=5, sticky='e')
        helpButton = Button(buttonFrame, text='❓\nHelp',
                            width=7, command=self.__ctrl.helpButtonHandler)
        helpButton.grid(column=3, row=0, padx=5, pady=5, sticky='e')

        # general layout
        mainFrame.grid()
        self.__root.grid()

    def updateState(self, value):
        if(value == CONST.FORMAT_PDF):
            self.keepGeneratedScribusFilesLabel.configure(state=NORMAL)
            self.keepGeneratedScribusFilesCheckbox.configure(state=NORMAL)
        else:
            self.keepGeneratedScribusFilesLabel.configure(state=DISABLED)
            self.keepGeneratedScribusFilesCheckbox.configure(state=DISABLED)


def main(argv):
    root = Tkinter.Tk()
    ctrl = GeneratorControl(root)
    dlg = GeneratorDialog(root, ctrl)
    dlg.show()
    root.mainloop()


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
