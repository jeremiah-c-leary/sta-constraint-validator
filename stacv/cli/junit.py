'''
Generates a JUnit file from the rule results.
'''

import os
import xml.etree.ElementTree as ET


def generate_junit_file(sFilename, oPortResults):
    print(f'Creating JUnit file {sFilename}')

    oXmlFile = ET.Element('testsuites', name='stacv', tests='24', failures='2', skipped='6')
    write_file(sFilename, oXmlFile)
    return


def write_file(sFilename, oXml):
    oXmlTree = ET.ElementTree(oXml)
    with open(sFilename, 'wb') as oFile:
        oXmlTree.write(oFile, encoding="utf-8", xml_declaration=True)
