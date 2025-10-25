"""Test HTML parsing and link extraction."""
import pytest
from app.parser import parse_and_extract_links


def test_extract_links():
    html = """
    <html>
        <body>
            <a href="http://example.com/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="javascript:void(0)">Skip</a>
            <a href="mailto:user@example.com">Skip</a>
            <a href="tel:123456">Skip</a>
        </body>
    </html>
    """
    base_url = "http://example.com"
    links = parse_and_extract_links(html, base_url)
    
    assert len(links) == 2
    assert "http://example.com/page1" in links
    assert "http://example.com/page2" in links


def test_extract_links_invalid_html():
    html = "<html><not-closed>"
    base_url = "http://example.com"
    links = parse_and_extract_links(html, base_url)
    
    assert len(links) == 0