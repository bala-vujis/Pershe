import httpx
import asyncio
from bs4 import BeautifulSoup
from readability import Document
import html2text
from urllib.parse import urljoin, urlparse, urlunparse
import logging
from typing import List, Dict, Optional, Set
import re
import time

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0
        
        # Spec: Blacklist patterns
        self.blacklist_patterns = [
            r'^/#', r'^#',  # Anchors
            r'/privacy', r'/terms', r'/cookie', r'/login', r'/signup', 
            r'/careers', r'/jobs', r'/contact', 
            r'/wp-content', r'/cdn-cgi', r'/assets', r'/static',
            r'\.pdf$', r'\.jpg$', r'\.png$', r'\.css$', r'\.js$'
        ]
        
        # Spec: Preference patterns
        self.preference_patterns = [
            'product', 'products', 'solutions', 'industries', 
            'manufactur', 'export', 'about', 'services', 'capabilit'
        ]

    def get_base_origin(self, url: str) -> str:
        """
        Parse website_url and compute:
        base_origin = protocol + "://" + host (example: https://novagard.com)
        """
        parsed = urlparse(url)
        # Ensure scheme exists
        scheme = parsed.scheme if parsed.scheme else 'https'
        return f"{scheme}://{parsed.netloc}"

    def normalize_url(self, url: str) -> str:
        """Normalize URL - add https if missing, remove trailing slash"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not internal/private"""
        try:
            parsed = urlparse(url)
            # Prevent SSRF
            if parsed.hostname in ['localhost', '127.0.0.1'] or \
               str(parsed.hostname).startswith(('192.168.', '10.', '169.254.')):
                return False
            return True
        except:
            return False
    
    async def fetch_page(self, url: str, timeout: int = 20, retries: int = 2) -> Optional[str]:
        """Fetch HTML content from URL with retry logic"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < retries:
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    logger.error(f"All retries failed for {url}")
                    return None
        return None
    
    def extract_text(self, html: str) -> str:
        """Extract readable text from HTML"""
        if not html:
            return ""
        try:
            # Use readability to extract main content
            doc = Document(html)
            clean_html = doc.summary()
            
            # Convert to plain text
            text = self.h2t.handle(clean_html)
            
            # Clean up
            text = re.sub(r'\n{3,}', '\n\n', text)
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            # Fallback to basic extraction
            try:
                soup = BeautifulSoup(html, 'html.parser')
                for script in soup(["script", "style", "nav", "footer"]):
                    script.decompose()
                return soup.get_text(separator=' ', strip=True)
            except:
                return ""
    
    def score_link(self, href: str) -> int:
        """
        Score a link based on spec:
        Prefer URLs that match: /product|/products|/solutions|/industries|...
        """
        score = 0
        href_lower = href.lower()
        
        # Check blacklist first
        for pattern in self.blacklist_patterns:
            if re.search(pattern, href_lower):
                return -100  # Heavily penalize
        
        # Check preference list
        for term in self.preference_patterns:
            if term in href_lower:
                score += 10
                
        return score

    def extract_links(self, html: str, base_origin: str) -> List[str]:
        """
        Extract and filter links based on spec:
        1. From extracted hrefs, keep only those that start with / or are absolute same-domain
        2. Clean + score links
        3. Pick top 3 by score
        """
        if not html:
            return []
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            candidates = set()
            
            base_domain = urlparse(base_origin).netloc
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                
                # Skip empty
                if not href:
                    continue
                
                # Build full URL safe
                # Spec: "Ensure exactly one slash between host and path"
                # If href starts with /, base_origin should not have trailing slash (handled by get_base_origin)
                
                full_url = ""
                if href.startswith('http'):
                    # Absolute URL
                    if urlparse(href).netloc != base_domain:
                        continue
                    full_url = href
                elif href.startswith('/'):
                    # Relative path starting with /
                    full_url = base_origin + href
                else:
                    # Relative path not starting with / (e.g. "products.html")
                    # We treat it as relative to base_origin for simplicity, or just append /
                    full_url = f"{base_origin}/{href}"
                
                # Remove anchors and query params for deduping
                clean_url = full_url.split('#')[0].split('?')[0]
                
                # Ensure it's not the homepage itself
                if clean_url.rstrip('/') == base_origin.rstrip('/'):
                    continue
                    
                candidates.add(clean_url)
            
            # Score candidates
            scored_links = []
            for url in candidates:
                path = urlparse(url).path
                score = self.score_link(path)
                if score > -50:  # specific cutoff to exclude blacklisted
                    scored_links.append((url, score))
            
            # Sort by score desc
            scored_links.sort(key=lambda x: x[1], reverse=True)
            
            # Return top links
            return [link for link, score in scored_links]
            
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []

    async def scrape_company(self, website_url: str, company_name: str, max_pages: int = 3, max_chars_per_page: int = 6000) -> Dict:
        """Scrape company website and return structured data"""
        try:
            # 1. Normalize base domain
            # Spec: base_origin = protocol + "://" + host
            # First ensure it has protocol
            normalized_input_url = self.normalize_url(website_url)
            if not self.is_valid_url(normalized_input_url):
                 return {
                    "success": False,
                    "error_code": "INVALID_URL",
                    "error_message": "Invalid or blocked URL"
                }
            
            base_origin = self.get_base_origin(normalized_input_url)
            
            # 2. Fetch homepage
            # Spec: Fetch pages -> Add timeout + retry
            homepage_html = await self.fetch_page(base_origin)
            
            # If homepage fails, try the original full URL provided (in case it was a specific landing page)
            if not homepage_html and normalized_input_url != base_origin:
                homepage_html = await self.fetch_page(normalized_input_url)
                # If that worked, update base_origin to be safe? No, keep base_origin strict for link building.
            
            if not homepage_html:
                 return {
                    "success": False,
                    "error_code": "FETCH_FAILED",
                    "error_message": "Failed to fetch website"
                }

            homepage_text = self.extract_text(homepage_html)
            
            # 3. Clean + score links before limiting to 3
            links = self.extract_links(homepage_html, base_origin)
            selected_links = links[:max_pages]
            
            # 4. Fetch pages
            pages_data = [{
                "url": base_origin,
                "text": homepage_text[:max_chars_per_page]
            }]
            
            if selected_links:
                tasks = [self.fetch_page(link) for link in selected_links]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for link, html in zip(selected_links, results):
                    if html and not isinstance(html, Exception):
                        text = self.extract_text(html)
                        if text and len(text) > 100:
                            pages_data.append({
                                "url": link,
                                "text": text[:max_chars_per_page]
                            })
            
            # Combine text for the LLM
            # We preserve page boundaries to help the LLM understand structure
            combined_text = "\n\n".join([f"### SOURCE PAGE: {p['url']} ###\n{p['text']}" for p in pages_data])
            
            return {
                "success": True,
                "website_url": base_origin,
                "company_name": company_name,
                "pages_scraped": len(pages_data),
                "selected_pages": [p['url'] for p in pages_data],
                "combined_text": combined_text[:15000],  # Increased limit slightly as we have multiple pages
                "total_chars": len(combined_text)
            }
            
        except Exception as e:
            logger.error(f"Error scraping {website_url}: {str(e)}")
            return {
                "success": False,
                "error_code": "SCRAPE_ERROR",
                "error_message": str(e)
            }
