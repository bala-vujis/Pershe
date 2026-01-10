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
{{
  "company_one_liner": "string or null",
  "product_families": ["array of strings"],
  "capabilities_processes": ["array of strings"],
  "materials": ["array of strings"],
  "certifications": ["array of strings"],
  "industries_served": ["array of strings"],
  "quality_notes": ["array of strings"],
  "differentiators": ["array of strings"],
  "ideal_customer_fit": "string or null",
  "personalization_hooks": ["array of strings"]
}}

Input:
- Company name: {company_name}
- Website text: {website_text}
- Optional description: {company_description}"""
        
        # Default: logistics
        return """You are extracting ICP-relevant facts from a logistics company website. Be precise and avoid generic marketing language.
Return ONLY valid JSON with the schema below. If a field is unknown, use null or an empty array. Do not guess.

Schema:
{{
  "company_one_liner": "string or null",
  "services": ["array of strings"],
  "modes": ["array of strings"],
  "geographies": ["array of strings"],
  "industries_served": ["array of strings"],
  "proof_points": ["array of strings"],
  "differentiators": ["array of strings"],
  "ideal_customer_fit": "string or null",
  "personalization_hooks": ["array of strings"]
}}

Input:
- Company name: {company_name}
- Website text: {website_text}
- Optional description: {company_description}"""
    
    def get_icebreaker_prompt(self) -> str:
        """Get icebreaker generation prompt"""
        return """You write short, believable first lines for B2B cold emails. The user will send emails manually; you only generate the text.

RULES:
- Output ONLY valid JSON: {{"icebreaker":"..."}}
- Keep it under 55 words.
- Must be specific to the company based on the provided summary. No generic compliments.
- If data is weak, ask a smart, relevant question instead of inventing details.
- No emojis. No buzzwords.
- Do not mention "I used AI" or "I scraped your website".

Inputs:
- FirstName: {first_name}
- Company: {company_name}
- Summary JSON: {summary_json}
- Optional Title: {title}

Return JSON only."""
    
    async def generate_summary(self, api_key: str, model: str, preset: str, company_name: str, website_text: str, company_description: str = "", custom_prompt: Optional[str] = None) -> Dict:
        """Generate company summary using OpenAI"""
        content = None
        try:
            client = self.get_client(api_key)
            
            prompt_template = self.get_summary_prompt(preset, custom_prompt)
            prompt = prompt_template.format(
                company_name=company_name,
                website_text=website_text[:10000],  # Limit tokens
                company_description=company_description or "Not provided"
            )
            
            logger.info(f"Calling OpenAI for summary - Company: {company_name}, Model: {model}")
            
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
            logger.info(f"OpenAI response received - Length: {len(content)}, First 100 chars: {content[:100]}")
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
                logger.info("Removed ```json prefix")
            if content.startswith("```"):
                content = content[3:]
                logger.info("Removed ``` prefix")
            if content.endswith("```"):
                content = content[:-3]
                logger.info("Removed ``` suffix")
            content = content.strip()
            
            logger.info(f"After cleanup - Length: {len(content)}, First 100 chars: {content[:100]}")
            
            summary_json = json.loads(content)
            logger.info(f"✓ JSON parsed successfully for {company_name}")
            
            return {
                "success": True,
                "summary": summary_json,
                "tokens_used": response.usage.total_tokens
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Content: {content if content else 'No content'}")
            logger.error(f"Content repr: {repr(content)}")
            return {
                "success": False,
                "error_code": "INVALID_JSON",
                "error_message": f"LLM returned invalid JSON: {str(e)}"
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating summary: {error_msg}")
            logger.error(f"Exception type: {type(e).__name__}")
            
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
        content = None
        try:
            client = self.get_client(api_key)
            
            prompt_template = custom_prompt if custom_prompt else self.get_icebreaker_prompt()
            
            # Prepare format variables supporting both naming conventions
            format_vars = {
                'first_name': first_name or "there",
                'FirstName': first_name or "there",
                'company_name': company_name,
                'Company_Name': company_name,
                'Shortened_Company_Name': company_name.split()[0] if company_name else "",
                'summary_json': json.dumps(summary_json, indent=2),
                'title': title or "Not provided",
                'Title': title or "Not provided"
            }
            
            # Use safe_substitute to avoid KeyError if variables don't match
            from string import Template
            
            # First try regular format for our standard prompts
            try:
                prompt = prompt_template.format(**format_vars)
            except KeyError as e:
                # If format fails, try Template.safe_substitute which ignores missing keys
                logger.warning(f"Format failed, trying safe substitute: {e}")
                template = Template(prompt_template)
                prompt = template.safe_substitute(**format_vars)
            
            # If this is a custom prompt (user-provided template), wrap it with clear instructions
            if custom_prompt:
                prompt = f"""Based on the company summary below, generate a personalized cold email icebreaker following this template:

Template:
{prompt}

Company Summary:
{json.dumps(summary_json, indent=2)}

Instructions:
- Replace placeholders like [specific detail] with actual information from the summary
- Keep it under 55 words
- Be specific and relevant
- No emojis or buzzwords
- Output ONLY this JSON format: {{"icebreaker": "your generated text here"}}
- The icebreaker should be the complete email opener text, not a template"""
            
            logger.info(f"Calling OpenAI for icebreaker - Company: {company_name}, Model: {model}")
            
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
            logger.info(f"OpenAI response received - Length: {len(content)}, First 100 chars: {content[:100]}")
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
                logger.info("Removed ```json prefix")
            if content.startswith("```"):
                content = content[3:]
                logger.info("Removed ``` prefix")
            if content.endswith("```"):
                content = content[:-3]
                logger.info("Removed ``` suffix")
            content = content.strip()
            
            logger.info(f"After cleanup - Length: {len(content)}, First 100 chars: {content[:100]}")
            
            result_json = json.loads(content)
            
            # Try to extract icebreaker from various possible keys
            icebreaker = result_json.get('icebreaker', '')
            if not icebreaker:
                # Try other possible keys
                icebreaker = result_json.get('email', '')
            if not icebreaker:
                icebreaker = result_json.get('message', '')
            if not icebreaker:
                # If response has nested structure, try to extract
                if 'email_template' in result_json:
                    greeting = result_json['email_template'].get('greeting', '')
                    body = result_json['email_template'].get('body', '')
                    if isinstance(body, list):
                        body = ' '.join([str(item) for item in body])
                    icebreaker = f"{greeting}\n\n{body}"
            
            logger.info(f"✓ Icebreaker generated successfully for {company_name}: {icebreaker[:50]}...")
            
            return {
                "success": True,
                "icebreaker": icebreaker,
                "tokens_used": response.usage.total_tokens
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Content: {content if content else 'No content'}")
            logger.error(f"Content repr: {repr(content)}")
            return {
                "success": False,
                "error_code": "INVALID_JSON",
                "error_message": f"LLM returned invalid JSON: {str(e)}"
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating icebreaker: {error_msg}")
            logger.error(f"Exception type: {type(e).__name__}")
            
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
