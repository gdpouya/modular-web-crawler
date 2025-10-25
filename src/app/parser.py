"""HTML parser and link extractor."""
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
from typing import List, Set
import structlog

logger = structlog.get_logger()


def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent storage and comparison.
    
    - Lowercase scheme and host
    - Remove default ports (80/443)
    - Remove fragments
    - Sort query parameters
    - Remove trailing slash for non-root paths
    """
    parsed = urlparse(url)
    
    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    
    # Sort query parameters
    if parsed.query:
        params = parse_qs(parsed.query)
        query = urlencode(sorted(params.items()), doseq=True)
    else:
        query = ""
    
    # Remove trailing slash for non-root paths
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    
    return urlunparse((scheme, netloc, path, "", query, ""))


def parse_and_extract_links(html: str, base_url: str) -> Set[str]:
    """
    Parse HTML and extract normalized links.
    
    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative links

    Returns:
        Set of normalized absolute URLs
    """
    urls = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            
            # Skip javascript: and mailto: links
            if href.startswith(("javascript:", "mailto:", "tel:")):
                continue
                
            # Resolve relative URLs
            abs_url = urljoin(base_url, href)
            
            # Only keep http(s) URLs
            parsed = urlparse(abs_url)
            if parsed.scheme not in ("http", "https"):
                continue
                
            # Normalize and add
            norm_url = normalize_url(abs_url)
            urls.add(norm_url)
            
    except Exception as e:
        logger.error("parse_failed", url=base_url, error=str(e))
        
    return urls