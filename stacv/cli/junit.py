'''
Generates a JUnit file from the rule results.
'''

import os
import xml.etree.ElementTree as ET


def generate_junit_file(sFilename, oPortResults):
    print(f'Creating JUnit file {sFilename}')

    oXmlFile = build_testsuites(oPortResults)
    write_file(sFilename, oXmlFile)
    return


def build_testsuites(oPortResults):
    iTests = str(oPortResults.get_number_of_rules())
    iFailures = str(oPortResults.get_number_of_failures())
    iSkipped = str(oPortResults.get_number_of_skips())
    return ET.Element('testsuites', name='stacv', tests=iTests, failures=iFailures, skipped=iSkipped)


def write_file(sFilename, oXml):
    oXmlTree = ET.ElementTree(oXml)
    with open(sFilename, 'wb') as oFile:
        oXmlTree.write(oFile, encoding="utf-8", xml_declaration=True)
