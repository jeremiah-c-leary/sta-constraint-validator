'''
JUnit XML output so interface validation can run in a CI/CD pipeline.

One <testsuite> per interface pin and one <testcase> per check, named by
the check's permanent ID (for example EDG-001).  Checks
blocked by an earlier failure are reported as skipped, so the pipeline
shows the first thing that is wrong rather than every consequence of it.
'''

import xml.etree.ElementTree as ET

from stacv.analysis import checks


def build(validations, name='stacv'):
    root = ET.Element('testsuites', name=name)
    totals = {'tests': 0, 'failures': 0, 'skipped': 0}
    for validation in validations:
        suite = ET.SubElement(root, 'testsuite', name=validation.name)
        counts = {'tests': len(validation.results),
                  'failures': validation.count(checks.FAIL),
                  'skipped': validation.count(checks.SKIP)}
        for key, value in counts.items():
            suite.set(key, str(value))
            totals[key] += value
        suite.set('errors', '0')
        for result in validation.results:
            add_testcase(suite, validation, result)
    for key, value in totals.items():
        root.set(key, str(value))
    root.set('errors', '0')
    return root


def add_testcase(suite, validation, result):
    # The name is the permanent check ID so CI history survives title changes.
    case = ET.SubElement(suite, 'testcase', classname=validation.name, name=result.check_id, time='0')
    body = '\n'.join([f'{result.check_id}: {result.title}', result.message] + result.details)
    if result.status == checks.FAIL:
        failure = ET.SubElement(case, 'failure', message=f'{result.title}: {result.message}',
                                type=result.check_id)
        failure.text = body
    elif result.status == checks.SKIP:
        ET.SubElement(case, 'skipped', message=f'{result.title}: {result.message}')
    else:
        out = ET.SubElement(case, 'system-out')
        out.text = body


def write(validations, file_name):
    root = build(validations)
    # Indenting is cosmetic and ET.indent needs Python 3.9 or later.
    if hasattr(ET, 'indent'):
        ET.indent(root)
    ET.ElementTree(root).write(file_name, encoding='utf-8', xml_declaration=True)
