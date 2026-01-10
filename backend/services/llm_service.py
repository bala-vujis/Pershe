from openai import AsyncOpenAI
import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        pass
    
    def get_client(self, api_key: str):
        """Get OpenAI client with provided API key"""
        return AsyncOpenAI(api_key=api_key)
    
    def get_summary_prompt(self, preset: str, custom_prompt: Optional[str] = None) -> str:
        """Get summary prompt based on preset"""
        if preset == "custom" and custom_prompt:
            return custom_prompt
        
        if preset == "industrial":
            return """You are extracting ICP-relevant facts from an industrial supplier/manufacturer website. Be concrete and avoid generic marketing language.
Return ONLY valid JSON with the schema below. If unknown, use null/empty. Do not guess.

Schema:
{
  "company_one_liner": string|null,
  "product_families": string[],
  "capabilities_processes": string[],
  "materials": string[],
  "certifications": string[],
  "industries_served": string[],
  "quality_notes": string[],
  "differentiators": string[],
  "ideal_customer_fit": string|null,
  "personalization_hooks": string[]
}

Input:
- Company name: {company_name}
- Website text: {website_text}
- Optional description: {company_description}"""
        
        # Default: logistics
        return """You are extracting ICP-relevant facts from a logistics company website. Be precise and avoid generic marketing language.
Return ONLY valid JSON with the schema below. If a field is unknown, use null or an empty array. Do not guess.

Schema:
{
  "company_one_liner": string|null,
  "services": string[],
  "modes": string[],
  "geographies": string[],
  "industries_served": string[],
  "proof_points": string[],
  "differentiators": string[],
  "ideal_customer_fit": string|null,
  "personalization_hooks": string[]
}

Input:
- Company name: {company_name}
- Website text: {website_text}
- Optional description: {company_description}"""
    
    def get_icebreaker_prompt(self) -> str:
        """Get icebreaker generation prompt"""
        return """You write short, believable first lines for B2B cold emails. The user will send emails manually; you only generate the text.

RULES:
- Output ONLY valid JSON: {"icebreaker":"..."}
- Keep it under 55 words.
- Must be specific to the company based on the provided summary. No generic compliments.
- If data is weak, ask a smart, relevant question instead of inventing details.
- No emojis. No buzzwords.
- Use exactly one blank line after "Hey {FirstName}," (insert \n\n).
- Do not mention "I used AI" or "I scraped your website".

Inputs:
- FirstName: {first_name}
- Company: {company_name}
- Summary JSON: {summary_json}
- Optional Title: {title}

Return JSON only."""
    
    async def generate_summary(self, api_key: str, model: str, preset: str, company_name: str, website_text: str, company_description: str = "", custom_prompt: Optional[str] = None) -> Dict:
        """Generate company summary using OpenAI"""
        try:
            client = self.get_client(api_key)
            
            prompt_template = self.get_summary_prompt(preset, custom_prompt)
            prompt = prompt_template.format(
                company_name=company_name,
                website_text=website_text[:10000],  # Limit tokens
                company_description=company_description or "Not provided"
            )
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction assistant. You MUST return ONLY valid JSON with no additional text before or after. Do not include markdown code blocks or any other formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            summary_json = json.loads(content)
            
            return {
                "success": True,
                "summary": summary_json,
                "tokens_used": response.usage.total_tokens
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Content: {content if 'content' in locals() else 'No content'}")
            return {
                "success": False,
                "error_code": "INVALID_JSON",
                "error_message": f"LLM returned invalid JSON: {str(e)}"
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating summary: {error_msg}")
            
            # Check for authentication errors
            if "401" in error_msg or "Incorrect API key" in error_msg or "invalid_api_key" in error_msg:
                return {
                    "success": False,
                    "error_code": "INVALID_API_KEY",
                    "error_message": "Invalid OpenAI API key. Please update your API key in Settings."
                }
            
            return {
                "success": False,
                "error_code": "LLM_ERROR",
                "error_message": error_msg
            }
    
    async def generate_icebreaker(self, api_key: str, model: str, first_name: str, company_name: str, summary_json: Dict, title: str = "", custom_prompt: Optional[str] = None) -> Dict:
        """Generate personalized icebreaker using OpenAI"""
        try:
            client = self.get_client(api_key)
            
            prompt_template = custom_prompt if custom_prompt else self.get_icebreaker_prompt()
            prompt = prompt_template.format(
                first_name=first_name or "there",
                company_name=company_name,
                summary_json=json.dumps(summary_json, indent=2),
                title=title or "Not provided"
            )
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a B2B cold email writing assistant. You MUST return ONLY valid JSON with no additional text before or after. Do not include markdown code blocks or any other formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result_json = json.loads(content)
            
            icebreaker = result_json.get('icebreaker', '')
            
            return {
                "success": True,
                "icebreaker": icebreaker,
                "tokens_used": response.usage.total_tokens
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Content: {content}")
            return {
                "success": False,
                "error_code": "INVALID_JSON",
                "error_message": f"LLM returned invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error generating icebreaker: {str(e)}")
            return {
                "success": False,
                "error_code": "LLM_ERROR",
                "error_message": str(e)
            }
