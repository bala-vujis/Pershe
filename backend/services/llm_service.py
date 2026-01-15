from openai import AsyncOpenAI
import os
import json
import logging
from typing import Dict, Optional, List, Any
import re

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        pass
    
    def get_client(self, api_key: str):
        """Get OpenAI client with provided API key"""
        return AsyncOpenAI(api_key=api_key)
    
    def get_summary_prompt(self, preset: str, custom_prompt: Optional[str] = None) -> str:
        """Get summary prompt based on spec"""
        
        # Spec D & E: Page summarization and Aggregation
        # We perform this in one shot to save credits/tokens as requested
        
        return """You are an expert B2B analyst. Your goal is to create a 'Company Research Brief' by extracting and aggregating data from the provided website content (which may contain multiple pages).

Input:
- Company: {company_name}
- Content: {website_text}
- Optional Description: {company_description}

Instructions:
1. Analyze ALL provided text from all pages.
2. Aggregate findings (merge arrays, dedupe).
3. Prefer specific, non-generic details.
4. If the page is empty or content is missing, return empty arrays.
5. "one_sentence_company" should be a concise description of what they do.

Return ONLY valid JSON with this exact schema:
{{
  "products": ["specific product names or categories"],
  "industries": ["specific industries served"],
  "geo_markets": ["locations or regions served"],
  "manufacturing_capabilities": ["specific processes or capabilities"],
  "trade_signals": ["awards, certifications, partnerships, recent news"],
  "one_sentence_company": "A concise description of the company"
}}"""

    def get_icebreaker_prompt(self) -> str:
        """Get icebreaker generation prompt based on spec"""
        return """You write short, believable first lines for B2B cold emails. The user will send emails manually; you only generate the text.

CONTEXT:
Lead Context: {lead_context}
Company Research Brief: {company_research_brief}

RULES:
- Output ONLY valid JSON: {{"icebreaker":"..."}}
- Keep it under 55 words.
- Must be specific to the company based on the research brief.
- If data is weak, ask a smart, relevant question.
- No emojis. No buzzwords.
- Do not mention "I used AI" or "I scraped your website".
- Do not use hyphens (-) in the icebreaker. Use commas or other punctuation if needed.

Return JSON only."""
    
    async def generate_summary(self, api_key: str, model: str, preset: str, company_name: str, website_text: str, company_description: str = "", custom_prompt: Optional[str] = None) -> Dict:
        """Generate company summary using OpenAI"""
        content = None
        try:
            client = self.get_client(api_key)
            
            prompt_template = self.get_summary_prompt(preset, custom_prompt)
            prompt = prompt_template.format(
                company_name=company_name,
                website_text=website_text[:12000],  # Limit tokens
                company_description=company_description or "Not provided"
            )
            
            logger.info(f"Calling OpenAI for summary - Company: {company_name}")
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction assistant. You MUST return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            summary_json = self._clean_and_parse_json(content)
            
            # Spec: If empty page, return all fields as empty arrays + one_sentence_company="no content"
            # We check if the result is effectively empty
            if not any(summary_json.values()):
                summary_json["one_sentence_company"] = "no content"
            
            return {
                "success": True,
                "summary": summary_json,
                "tokens_used": response.usage.total_tokens
            }
        
        except Exception as e:
            return self._handle_llm_error(e, content)

    async def generate_icebreaker(self, api_key: str, model: str, first_name: str, company_name: str, summary_json: Dict, title: str = "", custom_prompt: Optional[str] = None) -> Dict:
        """Generate personalized icebreaker using OpenAI"""
        content = None
        try:
            client = self.get_client(api_key)
            
            # Prepare Lead Context as per Spec
            # First name, role/headline (cleaned), company short name, location
            lead_context_parts = []
            if first_name: lead_context_parts.append(f"Name: {first_name}")
            if title: lead_context_parts.append(f"Role: {title}")
            lead_context_parts.append(f"Company: {company_name}")
            lead_context_str = ", ".join(lead_context_parts)
            
            # Prepare Company Research Brief
            # If research is empty, fallback_description (not handled here, logic in run_service or just passed as empty)
            # We assume summary_json is the brief
            
            prompt_template = custom_prompt if custom_prompt else self.get_icebreaker_prompt()
            
            # Format inputs
            # Handle both standard and custom prompt variables
            format_vars = {
                'lead_context': lead_context_str,
                'company_research_brief': json.dumps(summary_json, indent=2),
                # Legacy support for custom prompts
                'first_name': first_name or "there",
                'company_name': company_name,
                'summary_json': json.dumps(summary_json, indent=2),
                'title': title or ""
            }
            
            # Safe formatting
            from string import Template
            try:
                # Try standard format first
                if not custom_prompt:
                     prompt = prompt_template.format(**format_vars)
                else:
                    # For custom prompts, use safe substitution
                     prompt = Template(prompt_template).safe_substitute(**format_vars)
            except Exception:
                # Fallback
                 prompt = Template(prompt_template).safe_substitute(**format_vars)

            logger.info(f"Calling OpenAI for icebreaker - Company: {company_name}")
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a B2B cold email writing assistant. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            result_json = self._clean_and_parse_json(content)
            
            icebreaker = result_json.get('icebreaker', '')
            
            # Spec validation: "If icebreaker contains - hyphen, run a post-process replace"
            if '-' in icebreaker:
                # Replace hyphen with space only if it does not break meaning (simple heuristic: replace ' - ' with ', ' or just ' ')
                # Spec says "Replace hyphen with space only if it does not break meaning". 
                # Simplest safe approach: replace " - " with ", " and "-" inside words we leave? 
                # "Otherwise regenerate with 'No hyphen characters allowed.'"
                
                # Let's try simple replacement first
                modified_icebreaker = icebreaker.replace(' - ', ', ').replace('-', ' ')
                
                # If it still looks weird or we want to be strict as per spec "Otherwise regenerate"
                # Let's regenerate to be safe if it was a major hyphen usage
                if '-' in icebreaker: # strict
                     logger.info("Regenerating icebreaker due to hyphens")
                     response = await client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a B2B cold email writing assistant. Return ONLY valid JSON."},
                            {"role": "user", "content": prompt + "\n\nIMPORTANT: No hyphen characters allowed."}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    )
                     content = response.choices[0].message.content.strip()
                     result_json = self._clean_and_parse_json(content)
                     icebreaker = result_json.get('icebreaker', '')

            return {
                "success": True,
                "icebreaker": icebreaker,
                "tokens_used": response.usage.total_tokens
            }
        
        except Exception as e:
            return self._handle_llm_error(e, content)

    def _clean_and_parse_json(self, content: str) -> Dict:
        """Helper to clean markdown and parse JSON"""
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())

    def _handle_llm_error(self, e: Exception, content: Optional[str]) -> Dict:
        """Standard error handling"""
        error_msg = str(e)
        logger.error(f"LLM Error: {error_msg}")
        
        if isinstance(e, json.JSONDecodeError):
             return {
                "success": False,
                "error_code": "INVALID_JSON",
                "error_message": f"LLM returned invalid JSON. Content: {content[:100]}..."
            }
            
        if "401" in error_msg or "Incorrect API key" in error_msg:
            return {
                "success": False,
                "error_code": "INVALID_API_KEY",
                "error_message": "Invalid OpenAI API key."
            }
            
        return {
            "success": False,
            "error_code": "LLM_ERROR",
            "error_message": error_msg
        }
