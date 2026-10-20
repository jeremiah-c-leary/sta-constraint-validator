'''
Generates a JUnit file from the rule results.
'''

import xml.etree.ElementTree as ET


def generate_junit_file(sFilename, oPortResults):
    print(f'Creating JUnit file {sFilename}')

    oXmlFile = build_testsuites(oPortResults)
    write_file(sFilename, oXmlFile)


def build_testsuites(oPortResults):
    oTestsuites = build_testsuites_element(oPortResults)
    for oPortResult in oPortResults.results:
        build_testsuite(oTestsuites, oPortResult)
    return oTestsuites


def build_testsuites_element(oPortResults):
    sTests = str(oPortResults.get_number_of_rules())
    sFailures = str(oPortResults.get_number_of_failures())
    sSkipped = str(oPortResults.get_number_of_skips())
    return ET.Element('testsuites', name='stacv', tests=sTests, failures=sFailures, skipped=sSkipped)


def build_testsuite(oTestsuites, oPortResult):
    oTestsuite = build_testsuite_element(oTestsuites, oPortResult)
    add_testcases_to_testsuite(oTestsuite, oPortResult)


def build_testsuite_element(oTestsuites, oPortResult):
    sTests = str(oPortResult.get_number_of_rules())
    sFailures = str(oPortResult.get_number_of_failures())
    sSkipped = str(oPortResult.get_number_of_skips())
    sName = oPortResult.get_identifier()
    return ET.SubElement(oTestsuites, 'testsuite', name=sName, tests=sTests, failures=sFailures, skipped=sSkipped)


def add_testcases_to_testsuite(oTestsuite, oPortResult):
    sClassName = oPortResult.get_identifier()
    for oResult in oPortResult.get_results().results:
        build_testcase(oTestsuite, sClassName, oResult)


def build_testcase(oTestsuite, sClassName, oResult):
    oTestcase = build_testcase_element(oTestsuite, sClassName, oResult)
    if oResult.is_failed():
        add_failure_to_testcase(oTestcase, oResult)
    elif oResult.is_skipped():
        add_skipped_to_testcase(oTestcase, oResult)


def build_testcase_element(oTestsuite, sClassName, oResult):
    return ET.SubElement(oTestsuite, 'testcase', name=oResult.rule_id, classname=sClassName)


def add_failure_to_testcase(oTestcase, oResult):
    oFailure = ET.SubElement(oTestcase, 'failure', message=oResult.failure_message)
    oFailure.text = '\n'.join(oResult.details)


def add_skipped_to_testcase(oTestcase, oResult):
    sMessage = '\n'.join(oResult.details)
    ET.SubElement(oTestcase, 'skipped', message=sMessage)


def write_file(sFilename, oXml):
    oXmlTree = ET.ElementTree(oXml)
    ET.indent(oXmlTree, space='  ', level=0)
    with open(sFilename, 'wb') as oFile:
        oXmlTree.write(oFile, encoding="utf-8", xml_declaration=True)
