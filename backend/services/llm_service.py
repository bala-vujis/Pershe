from openai import AsyncOpenAI
import os
import json
import logging
from typing import Dict, Optional, List, Any
import re
from string import Template

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        pass
    
    def get_client(self, api_key: str):
        """Get OpenAI client with provided API key"""
        return AsyncOpenAI(api_key=api_key)
    
    def get_summary_prompt(self, preset: str, custom_prompt: Optional[str] = None) -> str:
        """Get summary prompt based on spec"""
        
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
        """Get icebreaker generation prompt based on Vujis spec"""
        return """You're a helpful, intelligent Cold outbound assistant for vujis.

Your task is to take these summaries and turn them into catchy, personalized openers for a cold outbound email campaign. The idea is we have done good research on the person and what they do at the company — and use it to lead into a pitch for Vujis.

CONTEXT:
Lead Context: {lead_context}
Company Research Brief: {company_research_brief}

STYLE/TEMPLATE TO FOLLOW (if provided):
{icebreaker_template}

RULES:
**You'll return your icebreakers in the following strict JSON format:
{"icebreaker": "Hey {FirstName},\n\nIf you reply with the HS code or product name of what {Shortened_Company_Name} offers, I can share 3 importers currently importing {their_product_base_category} from your competitors.\n\nIf it helps, I can also show you exactly how our platform pulled it."}

The Icebreaker should be of between 50 to 70 at max
Do NOT write generic compliments (e.g., "Nice website!").
Always Give 1 line gap (\n\n) after "Hey {name},
Shorten long company names where appropriate (e.g. "Love GenX" instead of "GenX International Logistics Solutions").
Do the same with locations (e.g. "SoCal" instead of "Southern California").
Focus on niche-specific indicators: obscure industries, supply chain specifics, target regions, strategic moves, etc.
Only mention 2 industry in {"thier industry"}
Use Vujis as the solution being pitched — focus on its strength to help exporters find new customers, understand what their competition are up to and researching new trends as well as getting the contact info of purchasing managers or other decision makers in overseas companies they want to sell to.
never use hiphen in personalised email as it reduces the chances of sounding human
remove hyphens (-)'-'"-" no hyphers or dash should be used in the entire message.
always Shorted the length of their role into the main keywords that are related to Export, international sales, etc..
Keep the company name as short as possible
don't try to change any wording from the given script
Avoid saying "solution" because we are approaching companies that sells "physical products".
sometimes there maybe irrelavant service companies will come, manage those somehow please :)

**Your job is to make it sound like we’ve done a ton of research, even though this is scalable automation.

**if website data is not available use company short description"""

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
            logger.info(f"Summary Content: {content[:100]}...")
            summary_json = self._clean_and_parse_json(content)
            
            # Spec: If empty page, return all fields as empty arrays + one_sentence_company="no content"
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
            
            # Prepare Lead Context
            lead_context_parts = []
            if first_name: lead_context_parts.append(f"Name: {first_name}")
            if title: lead_context_parts.append(f"Role: {title}")
            lead_context_parts.append(f"Company: {company_name}")
            lead_context_str = ", ".join(lead_context_parts)
            
            prompt_template = self.get_icebreaker_prompt()
            
            # Format input using fixed internal variables, injecting custom_prompt as a template string
            prompt = prompt_template.format(
                lead_context=lead_context_str,
                company_research_brief=json.dumps(summary_json, indent=2),
                icebreaker_template=(custom_prompt or "No specific template provided. Use standard professional tone.").strip()
            )

            logger.info(f"Calling OpenAI for icebreaker - Company: {company_name}")
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a B2B cold email writing assistant. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, 
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Icebreaker Response Content: {content}") 
            
            result_json = self._clean_and_parse_json(content)
            
            # Restore fallback logic for legacy prompts/formats
            icebreaker = (result_json.get('icebreaker') or result_json.get('email') or result_json.get('message') or result_json.get('intro') or "").strip()
            
            # Hard validation: fail if empty
            if not icebreaker:
                return {
                    "success": False,
                    "error_code": "EMPTY_ICEBREAKER",
                    "error_message": "Model returned empty icebreaker JSON.",
                }
            
            # Spec validation: "If icebreaker contains - hyphen, run a post-process replace"
            if '-' in icebreaker:
                modified_icebreaker = icebreaker.replace(' - ', ', ').replace('-', ' ')
                
                # Strict check
                if '-' in modified_icebreaker: 
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
                     icebreaker = (result_json.get('icebreaker') or "").strip()
                     
                     if not icebreaker:
                        return {
                            "success": False,
                            "error_code": "EMPTY_ICEBREAKER_RETRY",
                            "error_message": "Model returned empty icebreaker on retry.",
                        }
                else:
                    icebreaker = modified_icebreaker

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
