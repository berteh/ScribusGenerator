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
# v1.9 (2015-08-03): initial command-line support (SLA only, use GUI version to generate PDF)


This script is the ScribusGenerator Engine

=================
The MIT License
=================

Copyright (c) 2010-2014 Ekkehard Will (www.ekkehardwill.de), 2014-2022
 Berteh (https://github.com/berteh/)

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
    # set to 0 to keep the separating element before an unused/empty variable, typically a linefeed (<para>) or list syntax token (,;-.)
    REMOVE_CLEANED_ELEMENT_PREFIX = 1
    # set to 0 to replace all tabs and linebreaks in csv data by simple spaces.
    KEEP_TAB_LINEBREAK = 1
    SG_VERSION = '3.0.0 python3'
    # set to any word you'd like to use to trigger a jump to the next data record. using a name similar to the variables %VAR_ ... % will ensure it is cleaned after generation, and not show in the final document(s).
    NEXT_RECORD = '%SG_NEXT-RECORD%'
    OUTPUTCOUNT_VAR = 'COUNT'
    # set to the minimum amount of numbers you want to force in the output files name counter. 3 leads to 001,002,...; default is 1, 
    OUTPUTCOUNT_FILL = 1

class ScribusGenerator:
    # Column headers (= keys of each data record)
    headers = []

    # The Generator Module has all the logic and will do all the work
    def __init__(self, dataObject):
        self.__dataObject = dataObject
        
        logging.config.fileConfig(os.path.join(os.path.abspath(
            os.path.dirname(__file__)), 'logging.conf'
        ))

        # TODO: Check if logging works, if not warn user to configure log file path and disable.
        logging.info('ScribusGenerator initialized')
        logging.debug('OS: %s - Python: %s - ScribusGenerator v%s' % (
            os.name, platform.python_version(), CONST.SG_VERSION
        ))


    def run(self):
        # Read CSV/JSON data and replace the variables in the Scribus File with the corresponding data. Finally export to the specified format.
        # may throw exceptions if errors are met, use traceback to get all error details

        # Log options
        options_text = self.__dataObject.toString()

        logging.debug('Active options: %s%s' % (
            options_text[:1], options_text[172:]
        ))

        # Load global configuration
        scribus_file = self.__dataObject.getScribusSourceFile()

        # (1) Output file name
        if self.__dataObject.getSingleOutput() and self.__dataObject.getOutputFileName() is CONST.EMPTY:
            self.__dataObject.setOutputFileName(os.path.split(
                os.path.splitext(scribus_file)[0])[1] + '__single'
            )

        # (2) Scribus source file (= SLA template file)
        logging.info('Parsing Scribus SLA template file %s' % scribus_file)

        try:
            tree = ET.parse(scribus_file)

        except IOError as exception:
            logging.error('Scribus SLA template file not found: %s' % scribus_file)

            raise

        # (3) SLA root element & template file version
        root = tree.getroot()
        version = root.get('Version')

        logging.debug('Scribus SLA template file version is %s' % version)

        # (4) Save settings
        if self.__dataObject.getSaveSettings():
            serial = self.__dataObject.toString()

            # TODO: as: %s' %serial)
            logging.debug('Saving current ScribusGenerator settings in your source file.')

            document = root.find('DOCUMENT')
            storage_element = document.find('./JAVA[@NAME="' + CONST.STORAGE_NAME + '"]')

            if storage_element is None:
                color_element = document.find('./COLOR[1]')
                script_position = list(document).index(color_element)

                logging.debug(
                    'Creating new storage element in SLA template at position %s' % script_position
                )

                storage_element = ET.Element('JAVA', {'NAME': CONST.STORAGE_NAME})
                document.insert(script_position, storage_element)

            storage_element.set('SCRIPT', serial)

            # TODO: bug race condition: check if scribus reloads (or overwrites :/ ) when doc is opened, opt use API to add a script if there's an open doc.
            tree.write(scribus_file)

        # Run core functions
        # (1) Parse data file & store its contents
        data = self.parse_data()

        # (2) Generate SLA file(s) from template, using parsed data
        output_filenames = self.generate_templates(root, data)

        # (3) Export them to PDF (if specified)
        if self.__dataObject.getOutputFormat() == CONST.FORMAT_PDF:
            for output_name in output_filenames:
                # Build absolute paths for ..
                # (1) .. SLA file
                sla_output_file = self.build_file_path(
                    self.__dataObject.getOutputDirectory(), output_name, CONST.FILE_EXTENSION_SCRIBUS
                )

                # (2) .. PDF file
                pdf_output_file = self.build_file_path(
                    self.__dataObject.getOutputDirectory(), output_name, CONST.FILE_EXTENSION_PDF
                )

                # Export template to PDF
                self.export_pdf(sla_output_file, pdf_output_file)

                logging.info('PDF file created: %s' % pdf_output_file)

        # (4) Remove them (if specified)
        if (not self.__dataObject.getOutputFormat() == CONST.FORMAT_SLA) and (self.__dataObject.getKeepGeneratedScribusFiles() == CONST.FALSE):
            for output_name in output_filenames:
                # Build absolute path for each SLA file
                sla_output_file = self.build_file_path(
                    self.__dataObject.getOutputDirectory(), output_name, CONST.FILE_EXTENSION_SCRIBUS
                )

                # Delete temporary files
                os.remove(sla_output_file)

        return 1


    # Part I : PARSING DATA

    def parse_data(self):
        # Parse data file
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
            data = self.load_json(data_file)

        # (3) Load data
        if extension == '.csv':
            # .. from CSV file
            data = self.load_csv(data_file)
            logging.debug(data)

            if len(data) < 1:
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
                        'Could not parse value of "first row" as an integer, ' +
                        'using default value instead.'
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
                        'Could not parse value of "last row" as an integer, ' +
                        'using default value instead.'
                    )

            # (3) Apply data range (if needed)
            if first_item != 1 or last_item != len(data):
                logging.debug(
                    'Custom data range is: %s - %s' % (first_item, last_item)
                )

                data = data[first_item:last_item]

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


    # Part II : GENERATING TEMPLATE FILES

    def generate_templates(self, root, data: list) -> list:
        # Define variables (for later use)
        merge_mode = self.__dataObject.getSingleOutput()

        # Check number of data records being consumed by Scribus source file
        # (1) Determine total of data records
        data_count = len(data)

        # (2) Store number of data records in template document
        root_string = ET.tostring(root, encoding=self.__dataObject.getCsvEncoding(), method='xml').decode()
        records_in_document = 1 + root_string.count(CONST.NEXT_RECORD)

        # (3) Inform about it
        logging.info('Source document consumes %s data record(s) from %s.' % (
            records_in_document, data_count
        ))

        # Overwrite attributes from their /*/ItemAttribute[Parameter=SGAttribute] sibling, when applicable
        # Initialize template element & document properties
        template_element = self.overwrite_with_sg_attributes(root)
        pages_count = page_height = vertical_gap = groups_count = objects_count = 0

        # Store keys of data items
        self.headers = list(data[0].keys())

        logging.info('Variables from data file(s): %s' % self.headers)

        # Create list for generated files & set index for current data record
        output_files = []
        index = 1

        # Create buffer & output variable
        buffer = []
        output = ''

        for item in data:
        # each iteration substitutions 1 x the template, consuming required 
        # data entries per active options.
        #
        # invariant: data has been substituted up to data[index-1], and
        # SLA code is stored accordingly in output,
        # SLA files have been generated up to index-1 entry as per generation
        # options and number of records consumed by the source template.

            # Add values to buffer
            buffer.append(item)

            # Check if ..
            # (1) .. done buffering data for current document OR
            # (2) .. last data record
            if index % records_in_document == 0 or index == data_count:
                logging.debug(
                    'Substitute, with data entry index being %s' % index
                )
                
                # Generate output
                output = self.substitute_data(self.headers,
                    self.encode_scribus_xml(buffer),
                    ET.tostring(template_element, method='xml').decode().split('\n'),
                    CONST.KEEP_TAB_LINEBREAK
                )
                
                # Check if merge-mode is selected ..
                if merge_mode:
                    # Update DOCUMENT properties on first substitution
                    if index == min(records_in_document, data_count):
                        logging.debug('Generating reference content from buffer at #%s' % index)
                        scribus_element= ET.fromstring(output)
                        document_element = scribus_element.find('DOCUMENT')
                        pages_count = int(document_element.get('ANZPAGES'))
                        page_height = float(document_element.get('PAGEHEIGHT'))
                        vertical_gap = float(document_element.get('GapVertical'))
                        groups_count = int(document_element.get('GROUPC'))
                        objects_count = len(scribus_element.findall('.//PAGEOBJECT'))
                        version = str(scribus_element.get('Version')) #str(document_element.get('DOCDATE'))

                        logging.debug('Current template has #%s page objects' % objects_count)

                        document_element.set('ANZPAGES',
                            str(math.ceil(pages_count * data_count // records_in_document))
                        )

                        document_element.set('DOCCONTRIB',
                            document_element.get('DOCCONTRIB') + CONST.CONTRIB_TEXT
                        )

                    # Append DOCUMENT content
                    logging.debug('Merging content from buffer up to entry index #%s' % index)

                    shifted_elements = self.shift_pages_and_objects(
                        ET.fromstring(output).find('DOCUMENT'),
                        pages_count,
                        page_height,
                        vertical_gap,
                        index - 1,
                        records_in_document,
                        groups_count,
                        objects_count,
                        version
                    )

                    if index > records_in_document:
                        document_element.extend(shifted_elements)

                # .. otherwise, write one of multiple SLA files
                else:
                    #logging.debug('writing one file with buffer %s' % item)
                    output_file = self.create_output_file(
                        index, self.__dataObject.getOutputFileName(), item, len(str(data_count))
                    )

                    self.write_sla_file(ET.fromstring(output), output_file)
                    output_files.append(output_file)

                buffer = []

            index += 1

        # Clean & write single SLA file (merge-mode only)
        if merge_mode:
            var_names_dic = dict(list(zip(self.headers,self.headers)))
            #logging.debug('writing merged file with dic %s' % var_names_dic)
            output_file = self.create_output_file(
                index-1, self.__dataObject.getOutputFileName(), var_names_dic, len(str(data_count))
            )

            self.write_sla_file(scribus_element, output_file)
            output_files.append(output_file)

        return output_files


    def overwrite_with_sg_attributes(self, root):
        # modifies root such that
        # attributes have been rewritten from their /*/ItemAttribute[Parameter=SGAttribute] sibling, when applicable.
        #
        # allows to use %VAR_<var-name>% in Item Attribute to overwrite internal attributes (eg FONT)

        for page_object in root.findall('.//ItemAttribute[@Parameter="SGAttribute"]/../..'):
            for sga in page_object.findall('.//ItemAttribute[@Parameter="SGAttribute"]'):
                reference = sga.get('RelationshipTo')

                # Cannot use 'default' on .get() as it is '' (empty string) by default in SLA file
                if reference == '':
                    # target is page_object by default. Cannot use ".|*" as not supported by ET
                    reference = '.'

                # ET cannot use absolute path on element
                elif reference.startswith('/'):
                    reference = '.' + reference

                attribute = sga.get('Name')
                value = sga.get('Value')

                try:
                    targets = page_object.findall(reference)

                    if targets:
                        for target in targets:
                            logging.debug('Overwriting value of %s in %s with "%s"' % (
                                attribute, target.tag, value
                            ))

                            target.set(attribute, value)
                    else:
                        # TODO: Message to user
                        logging.error(
                            'Target "%s" could be parsed but designated no node. ' +
                            'Check it out as it is probably not what you expected to replace %s.' % (
                                reference, attribute
                            )
                        )

                except SyntaxError:
                    # TODO: Message to user
                    logging.error(
                        'XPATH expression "%s" could not be parsed ' +
                        'by ElementTree to overwrite %s. Skipping.' % (
                            reference, attribute
                        )
                    )

        return root


    def multiple_replace(self, string: str, replacements: dict) -> str:
        # multiple simultaneous string replacements, per http://stackoverflow.com/a/15448887/1694411)
        # combine with dictionary = dict(zip(keys, values)) to use on arrays
        pattern = re.compile("|".join([re.escape(k) for k in replacements.keys()]), re.M)

        return pattern.sub(lambda x: replacements[x.group(0)], str(string))


    def encode_scribus_xml(self, data: list) -> list:
        # Encode some characters that can be found in CSV into XML entities
        # not all are needed as Scribus handles most UTF8 characters just fine.
        replacements = {'&': '&amp;', '"': '&quot;', '<': '&lt;'}

        result = []

        for item in data:
            result.append([
                self.multiple_replace(value, replacements) for value in item.values()
            ])

        return result


    def substitute_data(self, var_names: list, data: list, template: list, keep_tabs_lf=0, clean=CONST.CLEAN_UNUSED_EMPTY_VARS):
        # for each list of *data* array, substitute all %VAR_*var_names*% placeholders in 
        # *template* array with the *data* value at the same index. Return concatenated
        # substituted template.
        
        # done in string instead of XML for lack of efficient
        # attribute-value-based substring-search in ElementTree
        # but that makes NEXT-RECORD token position in XML critical.
        
        result = ''
        index = 0
        replacements_outdated = 1

        for line in template:
            
            # Skip redundant computations & preserve colors declarations
            if re.search('%VAR_|' + CONST.NEXT_RECORD, line) == None or re.search('\s*<COLOR\s+', line) != None:
                result = result + line
                # logging.debug("  keeping intact %s"%line[:30])
                continue

            # Initialize data record replacements
            if replacements_outdated:
                if index < len(data):
                    replaced_strings = data[index]                
                else:
                    replaced_strings = [""] * len(var_names)
                logging.debug('Replacements updated: %s' % replaced_strings)
                replacements_outdated = 0
            
            if index < len(data):
                replacements = dict(list(zip(
                    ['%VAR_' + n + '%' for n in var_names],
                    replaced_strings
                )))
            
            # Look for 'NEXT_RECORD' entry
            if CONST.NEXT_RECORD in line:
                index += 1
                replacements_outdated = 1
                
            # Replace placeholders with actual data
            #logging.debug("replacing VARS_* in %s" % line[:30].strip())
            line = self.multiple_replace(line, replacements)
            #logging.debug("replaced in line: %s" % line)

            # Remove (& trim) any (unused) %VAR_\w*% like string
            if clean:
                # TODO: is there a way to input warning
                # "data not found for variable named XX"
                # instead of the number
                if CONST.REMOVE_CLEANED_ELEMENT_PREFIX:
                    (line, count) = re.subn('\s*[,;-]*\s*%VAR_\w*%\s*', '', line)

                # TODO: is there a way to input warning
                # "data not found for variable named XX"
                # instead of the number
                else:
                    (line, count) = re.subn('\s*%VAR_\w*%\s*', '', line)

                if (count > 0):
                    logging.debug("cleaned %d empty variable(s)" % count)

                (line, count) = re.subn('\s*%s\w*\s*' % CONST.NEXT_RECORD, '', line)

            # convert \t and \n into scribus <tab/> and <linebreak/>
            if keep_tabs_lf == 1 and re.search('[\t\n]+', line, flags=re.MULTILINE):
                matches = re.search(
                    '(<ITEXT.* CH=")([^"]+)(".*/>)', line, flags=re.MULTILINE | re.DOTALL)

                if matches:
                    matches_start = matches.group(1)
                    matches_stop = matches.group(3)
                    # logging.debug("converting tabs and linebreaks in line: %s"%(line))

                    line = re.sub(
                        '([\t\n]+)', matches_stop + '\g<1>' + matches_start, line, flags=re.MULTILINE
                    )

                    # Replace \t and \n
                    line = re.sub('\t', '<tab />', line)
                    line = re.sub('\n', '<breakline />', line, flags=re.MULTILINE)

                    logging.debug('Converted tabs and linebreaks in line: %s' % line)

                else:
                    logging.warning(
                        'Could not convert tabs and linebreaks in this line, ' +
                        'kindly report this to the developers: %s' % line
                    )

            result = result + line

        return result


    def shift_pages_and_objects(self,
        document_element,
        pages_count,
        page_height,
        vertical_gap,
        index,
        records_in_document,
        groups_count,
        objects_count, version
    ):
        vertical_offset = (float(page_height)+float(vertical_gap)) * \
            (index // records_in_document)

        #logging.debug("shifting to vertical_offset %s " % (vertical_offset))

        shifted = []

        for page in document_element.findall('PAGE'):
            page.set('PAGEYPOS', str(float(page.get('PAGEYPOS')) + vertical_offset))
            page.set('NUM', str(int(page.get('NUM')) + pages_count))

            shifted.append(page)

        for page_object in document_element.findall('PAGEOBJECT'):
            y_position = page_object.get('YPOS')

            if y_position == '':
                y_position = 0

            #logging.debug("original YPOS is %s " % (y_position))

            page_object.set('YPOS', str(float(y_position) + vertical_offset))
            page_object.set('OwnPage', str(int(page_object.get('OwnPage')) + pages_count))

            # Update ID and links
            if version.startswith('1.4'):
                #                if not (int(page_object.get('NUMGROUP')) == 0):
                #                    page_object.set('NUMGROUP', str(int(page_object.get('NUMGROUP')) + groups_count * index))
                # next linked frame by position

                if (page_object.get('NEXTITEM') != None and (str(page_object.get('NEXTITEM')) != "-1")):
                    page_object.set('NEXTITEM', str(
                        int(page_object.get('NEXTITEM')) + (objects_count * index))
                    )

                # previous linked frame by position
                if (page_object.get('BACKITEM') != None and (str(page_object.get('BACKITEM')) != "-1")):
                    page_object.set('BACKITEM', str(
                        int(page_object.get('BACKITEM')) + (objects_count * index))
                    )

            # Version 1.5 / 1.6
            else:
                logging.debug("version is %s shifting object %s (#%s)" %
                              (version, page_object.tag, page_object.get('ItemID')))
                logging.debug("index is %s" %(index))

                # TODO: Update ID with something unlikely allocated
                # TODO: Ensure unique ID instead of 6:, issue #101
                page_object.set('ItemID',
                    str(objects_count * index) + str(int(page_object.get('ItemID')))[7:]
                )

                # next linked frame by ItemID
                if (page_object.get('NEXTITEM') != None and (str(page_object.get('NEXTITEM')) != '-1')):
                    page_object.set('NEXTITEM',
                        str(objects_count * index) + str(int(page_object.get('NEXTITEM')))[7:]
                    )

                # previous linked frame by ItemID
                if (page_object.get('BACKITEM') != None and (str(page_object.get('BACKITEM')) != '-1')):
                    page_object.set('BACKITEM',
                        str(objects_count * index) + str(int(page_object.get('BACKITEM')))[7:]
                    )

            shifted.append(page_object)

        logging.debug("shifted page %s element of %s" % (index, vertical_offset))

        return shifted


    def create_output_file(self, index, filename, dico, fill_count):
        # If the User has not set an Output File Name, an internal unique file name
        # will be generated which is the index of the loop.
        result = str(index).zfill(max(fill_count, CONST.OUTPUTCOUNT_FILL))

        # Following characters are not allowed for File-Names on WINDOWS: < > ? " : | \ / *
        # Note / is still allowed in filename as it allows dynamic subdirectory in Linux (issue 102);
        # TODO: Check & fix for Windows
        if filename != CONST.EMPTY:
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
            
            list_vars = list(dico.keys())
            list_vars.append(CONST.OUTPUTCOUNT_VAR)
            list_values = list(dico.values())
            list_values.append(result)
            logging.debug('computing output file name from %s (count is %s)'%(filename,result))
            result = self.substitute_data(list_vars, [list_values], [filename])

            # TODO: check for utf8 characters support in windows filesystem
            result = result.translate(table)
            logging.debug('output file name is %s' % result)

        return result


    def write_sla_file(self, sla_element, output_file, clean=CONST.CLEAN_UNUSED_EMPTY_VARS, sla_indent=CONST.INDENT_SLA):
        # write SLA to filepath computed from given elements, optionally cleaning empty ITEXT elements and their empty PAGEOBJECTS
        sla_file = self.build_file_path(
            self.__dataObject.getOutputDirectory(), output_file, CONST.FILE_EXTENSION_SCRIBUS
        )

        directory = os.path.dirname(sla_file)

        if not os.path.exists(directory):
            os.makedirs(directory)

        output_tree = ET.ElementTree(sla_element)

        if (clean):
            self.remove_empty_texts(output_tree.getroot())

        if (sla_indent):
            from xml.dom import minidom

            xml_string = minidom.parseString(ET.tostring(output_tree.getroot())).toprettyxml(indent="   ")

            with open(sla_file, 'w', encoding='utf-8') as file:
                file.write(xml_string)

        else:
            output_tree.write(sla_file, encoding='utf-8')

        logging.info('Scribus file created: %s' % sla_file)

        return sla_file


    def remove_empty_texts(self, root):
        # *modifies* root `ElementTree` by removing empty text elements and their empty placeholders.
        # returns number of ITEXT elements deleted.
        #   1. clean text in which some variable-like text is not substituted (ie: known or unknown variable):
        #      <ITEXT CH="empty %VAR_empty% variable should not show" FONT="Arial Regular" />
        #   2. remove <ITEXT> with empty @CH and precedings <para/> if any
        #   3. remove any <PAGEOBJECT> that has no <ITEXT> child left
        empty_xpath = "ITEXT[@CH='']"
        removal_count = 0

        # little obscure because its parent is needed to remove an element, and `ElementTree` has no parent() method.
        for page in root.findall('.//%s/../..' % empty_xpath):
            # Collect empty_xpath and preceding <para> for removal
            # Iteration is needed due to lack of sibling-previous navigation in `ElementTree`
            for page_object in page.findall('.//%s/..' % empty_xpath):
                # Initialize trash bin
                trash = []

                for position, item in enumerate(page_object):
                    if (item.tag == 'ITEXT') and (item.get('CH') == ''):
                        logging.debug('Cleaning 1 empty ITEXT and preceding linefeed (opt.)')
                        if (CONST.REMOVE_CLEANED_ELEMENT_PREFIX and page_object[position-1].tag == 'para'):
                            trash.append(position - 1)

                        trash.append(position)

                        removal_count += 1

                trash.reverse()

                # Remove trashed elements as stack (lifo order), to preserve positions validity
                for removed_position in trash:
                    page_object.remove(page_object[removed_position])

                if len(page_object.findall('ITEXT')) == 0:
                    logging.debug('Cleaning 1 empty PAGEOBJECT')
                    page.remove(page_object)

        logging.debug('Removed %d empty texts items' % removal_count)

        return removal_count


    # Part III : PDF EXPORT & CLEANUP

    def export_pdf(self, sla_file: str, pdf_file: str):
        import scribus

        # Create filepath (if needed)
        directory = os.path.dirname(pdf_file)

        if not os.path.exists(directory):
            os.makedirs(directory)

        # Export PDF using Scribus API
        # (1) Open template file
        scribus.openDoc(sla_file)

        # (2) Determine pages
        i = 0
        pages_count = []

        while (i < scribus.pageCount()):
            i += 1
            pages_count.append(i)

        # (3) Setup PDF exporter
        pdf_exporter = scribus.PDFfile()
        pdf_exporter.info = CONST.APP_NAME
        pdf_exporter.file = str(pdf_file)
        pdf_exporter.pages = pages_count

        # (4) Save PDF file
        pdf_exporter.save()

        # (5) Close document
        scribus.closeDoc()


    # UTILITIES

    def build_file_path(self, directory: str, filename: str, extension: str):
        # Build an absolute path
        # Examples:
        # "C:/tmp/template.sla" on Windows
        # "/tmp/template.sla" on macOS & Unix-like OS
        return directory + CONST.SEP_PATH + filename + CONST.SEP_EXT + extension


    def get_log(self):
        return logging


    def get_saved_settings(self):
        logging.debug('Parsing Scribus source file %s for user settings' % (
            self.__dataObject.getScribusSourceFile()
        ))

        try:
            tree = ET.parse(self.__dataObject.getScribusSourceFile())
            root = tree.getroot()

            doc = root.find('DOCUMENT')
            storage = doc.find('./JAVA[@NAME="' + CONST.STORAGE_NAME + '"]')

            return storage.get('SCRIPT')

        except SyntaxError as exception:
            logging.error(
                'Loading settings is only possible with Python 2.7 and later, ' +
                'please update your system: %s' % exception
            )

            return None

        except Exception as exception:
            logging.debug('Could not load the user settings: %s' % exception)

            return None


class GeneratorDataObject:
    # Data Object for transferring the settings made by the user on the UI / CLI
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
            'datafile': self.__dataSourceFile,
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


    # TODO: Add validity/plausibility checks on all values?
    def loadFromString(self, string):
        j = json.loads(string)
        for k, v in j.items():
            if v == None:
                j[k] = CONST.EMPTY
        # self.__scribusSourceFile NOT loaded
        self.__dataSourceFile = j['datafile']
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
