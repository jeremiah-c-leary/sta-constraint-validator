'''
Generates a JUnit file from the rule results.
'''

import os
import xml.etree.ElementTree as ET


def generate_junit_file(sFilename, oPortResults):
    print(f'Creating JUnit file {sFilename}')

    oXmlFile = build_testsuites(oPortResults)
    write_file(sFilename, oXmlFile)


def build_testsuites(oPortResults):
    iTests = str(oPortResults.get_number_of_rules())
    iFailures = str(oPortResults.get_number_of_failures())
    iSkipped = str(oPortResults.get_number_of_skips())
    oTestSuites = ET.Element('testsuites', name='stacv', tests=iTests, failures=iFailures, skipped=iSkipped)
    for oPortResult in oPortResults.results:
        build_testsuite(oTestSuites, oPortResult)
    return oTestSuites


def build_testsuite(oXmlFile, oPortResult):
    iTests = str(oPortResult.get_number_of_rules())
    iFailures = str(oPortResult.get_number_of_failures())
    iSkipped = str(oPortResult.get_number_of_skips())
    sName = build_testsuite_name(oPortResult)
    oTestsuite = ET.SubElement(oXmlFile, 'testsuite', name=sName, tests=iTests, failures=iFailures, skipped=iSkipped) 
    for oResult in oPortResult.get_results():
        oTestcase = build_testcase(oTestsuite, sName, oResult)
        if oResult.is_failed():
            add_failure(oTestcase, oResult)
        elif oResult.is_skipped():
            add_skipped(oTestcase, oResult)


def build_testsuite_name(oPortResult):
    return oPortResult.port.name + '.' + oPortResult.port.methodology


def build_testcase(oTestSuite, sClassName, oResult):
    return ET.SubElement(oTestSuite, 'testcase', name=oResult.rule_id, classname=sClassName)


def add_failure(oTestcase, oResult):
    oFailure = ET.SubElement(oTestcase, 'failure', message=oResult.failure_message)
    oFailure.text = '\n'.join(oResult.details)


def add_skipped(oTestcase, oResult):
    sMessage = '\n'.join(oResult.details)
    ET.SubElement(oTestcase, 'skipped', message=sMessage)


def write_file(sFilename, oXml):
    oXmlTree = ET.ElementTree(oXml)
    with open(sFilename, 'wb') as oFile:
        oXmlTree.write(oFile, encoding="utf-8", xml_declaration=True)
