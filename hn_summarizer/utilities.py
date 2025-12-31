"""Utility functions for file operations and HN thread downloading."""

import os
import sys
import re
import html
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib.parse import urlparse

import requests


class Utilities:
    """Utility class for file operations and HN API interactions."""

    @staticmethod
    def create_subdirectories():
        """Create required subdirectories for the application."""
        subdirectories = ['./data', './final_output', './input', './output', './script_attic']
        for directory in subdirectories:
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.access(directory, os.W_OK):
                print(f"Warning: {directory} is not writable.", file=sys.stderr)

    @staticmethod
    def check_hnitem(hnitem, hnitem_id=None):
        """
        Check and normalize a Hacker News item identifier.
        
        Args:
            hnitem: Either a full HN URL or just the item ID
            hnitem_id: Optional pre-parsed item ID
            
        Returns:
            dict with 'hnitem' (full URL) and 'hnitem_id' keys
        """
        if hnitem.isdigit() and len(hnitem) > 5:
            hnitem = f"https://news.ycombinator.com/item?id={hnitem}"
            hnitem_id = Utilities.get_item_id(hnitem)
        hnitem_dict = {'hnitem': hnitem, 'hnitem_id': hnitem_id}
        return hnitem_dict

    @staticmethod
    def get_item_id(hnitem):
        """Extract the item ID from a Hacker News URL."""
        parsed_url = urlparse(hnitem)
        query_params = dict(q.split('=') for q in parsed_url.query.split('&'))
        return query_params['id']

    @staticmethod
    def sanitize_for_xml(text):
        """
        Sanitize text content for XML.
        
        Removes invalid XML characters and normalizes whitespace.
        
        Args:
            text: The text to sanitize
            
        Returns:
            Sanitized text safe for XML inclusion
        """
        if text is None:
            return ""
        # Remove XML-invalid control characters (keep tab, newline, carriage return)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # Normalize multiple whitespace/newlines to single space for cleaner output
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def download_hn_thread(hn_item_id, intermediate_file):
        """
        Download a Hacker News thread and save it as XML.
        
        Args:
            hn_item_id: The HN item ID to download
            intermediate_file: Path to save the XML output
        """
        url = f"https://hn.algolia.com/api/v1/items/{hn_item_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Create proper XML structure
        root = ET.Element("thread")
        root.set("hn_item_id", str(hn_item_id))
        
        # Add tableheader element
        ET.SubElement(root, "tableheader")
        
        def extract_comments(comment, parent_element):
            if comment.get('text') and comment.get('author'):
                entry = ET.SubElement(parent_element, "entry")
                author_elem = ET.SubElement(entry, "author")
                author_elem.text = Utilities.sanitize_for_xml(comment['author'])
                comment_elem = ET.SubElement(entry, "comment")
                # Decode HTML entities in comment text, then sanitize for XML
                comment_text = html.unescape(comment.get('text', ''))
                # Strip HTML tags but keep text content
                comment_text = re.sub(r'<[^>]+>', ' ', comment_text)
                comment_elem.text = Utilities.sanitize_for_xml(comment_text)
            for child in comment.get('children', []):
                extract_comments(child, parent_element)
        
        extract_comments(data, root)
        
        # Create XML tree and write with proper formatting
        tree = ET.ElementTree(root)
        
        # Use minidom for pretty printing
        xml_str = ET.tostring(root, encoding='unicode', method='xml')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
        
        # Remove extra blank lines that minidom adds
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines)
        
        with open(intermediate_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
