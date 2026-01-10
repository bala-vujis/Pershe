import httpx
import asyncio
from bs4 import BeautifulSoup
from readability import Document
import html2text
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0
    
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
            if parsed.hostname in ['localhost', '127.0.0.1'] or parsed.hostname.startswith('192.168.') or parsed.hostname.startswith('10.') or parsed.hostname.startswith('169.254.'):
                return False
            return True
        except:
            return False
    
    async def fetch_page(self, url: str, timeout: int = 15) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_text(self, html: str) -> str:
        """Extract readable text from HTML"""
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
            soup = BeautifulSoup(html, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator=' ', strip=True)
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract internal links from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Skip anchors, mailto, tel, etc.
                if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                    continue
                
                # Convert to absolute URL
                absolute_url = urljoin(base_url, href)
                
                # Only keep same-domain links
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                    # Remove query params and fragments for deduplication
                    clean_url = absolute_url.split('?')[0].split('#')[0]
                    if clean_url not in links:
                        links.append(clean_url)
            
            return links
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []
    
    def score_page_link(self, url: str) -> int:
        """Score a page URL based on keywords"""
        url_lower = url.lower()
        score = 0
        
        # High value keywords
        if any(kw in url_lower for kw in ['about', 'services', 'solutions', 'products', 'capabilities']):
            score += 10
        
        # Medium value keywords
        if any(kw in url_lower for kw in ['industries', 'sectors', 'expertise']):
            score += 8
        
        # Good value keywords
        if any(kw in url_lower for kw in ['quality', 'certifications', 'locations', 'network', 'team']):
            score += 6
        
        # Negative keywords
        if any(kw in url_lower for kw in ['blog', 'news', 'careers', 'privacy', 'terms', 'cookie', 'contact', 'login']):
            score -= 10
        
        return score
    
    def select_best_pages(self, links: List[str], max_pages: int = 3) -> List[str]:
        """Select best pages to scrape based on scoring"""
        scored_links = [(link, self.score_page_link(link)) for link in links]
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N with positive scores
        selected = [link for link, score in scored_links[:max_pages] if score > 0]
        return selected
    
    async def scrape_company(self, website_url: str, company_name: str, max_pages: int = 3, max_chars_per_page: int = 6000) -> Dict:
        """Scrape company website and return structured data"""
        try:
            # Normalize URL
            url = self.normalize_url(website_url)
            
            # Validate URL
            if not self.is_valid_url(url):
                return {
                    "success": False,
                    "error_code": "INVALID_URL",
                    "error_message": "Invalid or blocked URL"
                }
            
            # Fetch homepage
            homepage_html = await self.fetch_page(url)
            if not homepage_html:
                return {
                    "success": False,
                    "error_code": "FETCH_FAILED",
                    "error_message": "Failed to fetch website"
                }
            
            # Extract homepage text
            homepage_text = self.extract_text(homepage_html)
            if not homepage_text or len(homepage_text) < 100:
                return {
                    "success": False,
                    "error_code": "EMPTY_CONTENT",
                    "error_message": "Website has no readable content"
                }
            
            # Extract and score internal links
            links = self.extract_links(homepage_html, url)
            selected_links = self.select_best_pages(links, max_pages)
            
            # Fetch selected pages
            pages_data = [{
                "url": url,
                "text": homepage_text[:max_chars_per_page]
            }]
            
            # Fetch additional pages concurrently
            if selected_links:
                tasks = [self.fetch_page(link) for link in selected_links[:max_pages]]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for link, html in zip(selected_links, results):
                    if html and not isinstance(html, Exception):
                        text = self.extract_text(html)
                        if text and len(text) > 100:
                            pages_data.append({
                                "url": link,
                                "text": text[:max_chars_per_page]
                            })
            
            # Combine all text
            combined_text = "\n\n---\n\n".join([f"Page: {p['url']}\n\n{p['text']}" for p in pages_data])
            
            return {
                "success": True,
                "website_url": url,
                "company_name": company_name,
                "pages_scraped": len(pages_data),
                "selected_pages": [p['url'] for p in pages_data],
                "combined_text": combined_text[:12000],  # Max chars to LLM
                "total_chars": len(combined_text)
            }
        
        except Exception as e:
            logger.error(f"Error scraping {website_url}: {str(e)}")
            return {
                "success": False,
                "error_code": "SCRAPE_ERROR",
                "error_message": str(e)
            }
