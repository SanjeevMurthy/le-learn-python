"""
xml_parser.py

XML data parsing utilities.

Prerequisites:
- xml.etree.ElementTree (stdlib)
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_xml_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Parse an XML file into a nested dictionary.

    Interview Question:
        Q: Why is XML still relevant in DevOps?
        A: Legacy systems, SOAP APIs, Maven/pom.xml, JUnit test reports,
           Jenkins config.xml, .NET configs, SVG files.
           Parsing: ElementTree (stdlib, safe), lxml (fast, XPath).
           Security: use defusedxml to prevent XXE attacks
           (XML External Entity — reads files, SSRF).
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        return _element_to_dict(root)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return None


def _element_to_dict(element: ET.Element) -> Dict[str, Any]:
    """Convert an XML element to a dictionary."""
    result: Dict[str, Any] = {}

    if element.attrib:
        result['@attributes'] = dict(element.attrib)

    children = list(element)
    if not children:
        result['text'] = element.text or ''
        return result

    for child in children:
        tag = child.tag
        child_dict = _element_to_dict(child)
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(child_dict)
        else:
            result[tag] = child_dict

    return result


def parse_junit_xml(filepath: str) -> Dict[str, Any]:
    """Parse a JUnit XML test report."""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        suites = root.findall('.//testsuite') if root.tag != 'testsuite' else [root]

        results = {
            'total_tests': 0, 'failures': 0, 'errors': 0,
            'skipped': 0, 'time': 0.0, 'suites': [],
        }

        for suite in suites:
            suite_info = {
                'name': suite.get('name', ''),
                'tests': int(suite.get('tests', 0)),
                'failures': int(suite.get('failures', 0)),
                'errors': int(suite.get('errors', 0)),
                'time': float(suite.get('time', 0)),
            }
            results['total_tests'] += suite_info['tests']
            results['failures'] += suite_info['failures']
            results['errors'] += suite_info['errors']
            results['time'] += suite_info['time']
            results['suites'].append(suite_info)

        return results
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    # Demo with inline XML
    xml_str = '<config><server host="localhost" port="8080"/><database><name>mydb</name></database></config>'
    root = ET.fromstring(xml_str)
    result = _element_to_dict(root)
    print(f"  Parsed: {result}")
