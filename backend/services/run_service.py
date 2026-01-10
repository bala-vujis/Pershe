import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RunService:
    def __init__(self, db, google_service, scraper_service, llm_service):
        self.db = db
        self.google_service = google_service
        self.scraper_service = scraper_service
        self.llm_service = llm_service
    
    async def create_run(self, user_id: str, project_id: str, mode: str = "preview", max_rows: Optional[int] = None):
        """Create a new run"""
        # Get project
        project = await self.db.projects.find_one({"id": project_id, "user_id": user_id})
        if not project:
            raise ValueError("Project not found")
        
        # Get field mapping
        field_mapping = await self.db.field_mappings.find_one({"project_id": project_id})
        if not field_mapping:
            raise ValueError("Field mapping not found")
        
        # Get prompt config
        prompt_config = await self.db.prompt_configs.find_one({"project_id": project_id})
        if not prompt_config:
            raise ValueError("Prompt config not found")
        
        # Fetch sheet data
        try:
            # Use row_range from project, or default to A1:Z1000
            row_range = project.get('row_range') or 'A1:Z1000'
            values = await self.google_service.get_sheet_values(
                user_id,
                project['spreadsheet_id'],
                project['sheet_name'],
                row_range
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch sheet data: {str(e)}")
        
        if not values or len(values) < 2:
            raise ValueError("Sheet has insufficient data")
        
        # Parse headers
        header_row_idx = project.get('header_row', 1) - 1
        headers = values[header_row_idx] if header_row_idx < len(values) else []
        data_rows = values[header_row_idx + 1:]
        
        # Limit rows for preview mode
        if mode == "preview":
            data_rows = data_rows[:3]
        elif max_rows:
            data_rows = data_rows[:max_rows]
        
        # Create run
        run_id = str(uuid.uuid4())
        run_doc = {
            "id": run_id,
            "user_id": user_id,
            "project_id": project_id,
            "status": "queued",
            "mode": mode,
            "total_rows": len(data_rows),
            "processed_rows": 0,
            "success_rows": 0,
            "failed_rows": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "finished_at": None
        }
        await self.db.runs.insert_one(run_doc)
        
        # Create run items
        for idx, row in enumerate(data_rows):
            # Parse row data
            row_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            
            item_doc = {
                "id": str(uuid.uuid4()),
                "run_id": run_id,
                "row_index": idx + header_row_idx + 2,  # +2 for header and 1-based indexing
                "input_data": row_dict,
                "status": "pending",
                "error_code": None,
                "error_message": None,
                "attempts": 0,
                "website_url": row_dict.get(field_mapping['website_col'], ""),
                "selected_pages": [],
                "summary": None,
                "output_icebreaker": None,
                "tokens_in": 0,
                "tokens_out": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.run_items.insert_one(item_doc)
        
        return run_id
    
    async def process_run(self, run_id: str):
        """Process all items in a run"""
        try:
            # Update run status
            await self.db.runs.update_one(
                {"id": run_id},
                {"$set": {"status": "running", "started_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Get run
            run = await self.db.runs.find_one({"id": run_id})
            if not run:
                return
            
            # Get project and configs
            project = await self.db.projects.find_one({"id": run['project_id']})
            field_mapping = await self.db.field_mappings.find_one({"project_id": run['project_id']})
            prompt_config = await self.db.prompt_configs.find_one({"project_id": run['project_id']})
            
            # Get user's OpenAI API key
            api_key_doc = await self.db.api_keys.find_one({"user_id": run['user_id'], "provider": "openai"})
            if not api_key_doc:
                await self.db.runs.update_one(
                    {"id": run_id},
                    {"$set": {"status": "failed", "finished_at": datetime.now(timezone.utc).isoformat()}}
                )
                return
            
            api_key = api_key_doc['key_encrypted']
            
            # Get pending items
            items = await self.db.run_items.find({"run_id": run_id, "status": "pending"}).to_list(1000)
            
            # Process items with concurrency limit
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent
            tasks = [self.process_item(item, field_mapping, prompt_config, api_key, semaphore) for item in items]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Write results back to sheet
            await self.write_results_to_sheet(run_id, run['user_id'], project, field_mapping)
            
            # Update run status
            success_count = await self.db.run_items.count_documents({"run_id": run_id, "status": "success"})
            failed_count = await self.db.run_items.count_documents({"run_id": run_id, "status": "failed"})
            
            await self.db.runs.update_one(
                {"id": run_id},
                {"$set": {
                    "status": "completed",
                    "processed_rows": success_count + failed_count,
                    "success_rows": success_count,
                    "failed_rows": failed_count,
                    "finished_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        except Exception as e:
            logger.error(f"Error processing run {run_id}: {str(e)}")
            await self.db.runs.update_one(
                {"id": run_id},
                {"$set": {"status": "failed", "finished_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    async def process_item(self, item: Dict, field_mapping: Dict, prompt_config: Dict, api_key: str, semaphore: asyncio.Semaphore):
        """Process a single run item"""
        async with semaphore:
            try:
                item_id = item['id']
                input_data = item['input_data']
                
                # Update status
                await self.db.run_items.update_one(
                    {"id": item_id},
                    {"$set": {"status": "processing", "attempts": item['attempts'] + 1}}
                )
                
                # Extract required fields
                website = input_data.get(field_mapping['website_col'], '').strip()
                company_name = input_data.get(field_mapping['company_col'], '').strip()
                first_name = input_data.get(field_mapping.get('first_name_col', ''), '').strip()
                description = input_data.get(field_mapping.get('description_col', ''), '').strip()
                title = input_data.get(field_mapping.get('title_col', ''), '').strip()
                
                # Validate required fields
                if not website or not company_name:
                    await self.db.run_items.update_one(
                        {"id": item_id},
                        {"$set": {
                            "status": "failed",
                            "error_code": "MISSING_DATA",
                            "error_message": "Missing website or company name",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    return
                
                # Scrape website
                scrape_result = await self.scraper_service.scrape_company(website, company_name)
                
                if not scrape_result['success']:
                    await self.db.run_items.update_one(
                        {"id": item_id},
                        {"$set": {
                            "status": "failed",
                            "error_code": scrape_result['error_code'],
                            "error_message": scrape_result['error_message'],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    return
                
                # Generate summary
                summary_result = await self.llm_service.generate_summary(
                    api_key,
                    prompt_config.get('model', 'gpt-4o'),
                    prompt_config.get('summary_preset', 'logistics'),
                    company_name,
                    scrape_result['combined_text'],
                    description,
                    prompt_config.get('summary_prompt')
                )
                
                if not summary_result['success']:
                    await self.db.run_items.update_one(
                        {"id": item_id},
                        {"$set": {
                            "status": "failed",
                            "error_code": summary_result['error_code'],
                            "error_message": summary_result['error_message'],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    return
                
                # Generate icebreaker
                icebreaker_result = await self.llm_service.generate_icebreaker(
                    api_key,
                    prompt_config.get('model', 'gpt-4o'),
                    first_name,
                    company_name,
                    summary_result['summary'],
                    title,
                    prompt_config.get('icebreaker_prompt')
                )
                
                if not icebreaker_result['success']:
                    await self.db.run_items.update_one(
                        {"id": item_id},
                        {"$set": {
                            "status": "failed",
                            "error_code": icebreaker_result['error_code'],
                            "error_message": icebreaker_result['error_message'],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    return
                
                # Success - update item
                await self.db.run_items.update_one(
                    {"id": item_id},
                    {"$set": {
                        "status": "success",
                        "selected_pages": scrape_result.get('selected_pages', []),
                        "summary": summary_result['summary'],
                        "output_icebreaker": icebreaker_result['icebreaker'],
                        "tokens_in": summary_result.get('tokens_used', 0) + icebreaker_result.get('tokens_used', 0),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Deduct credit (1 credit per successful processing)
                run = await self.db.runs.find_one({"id": item['run_id']})
                if run:
                    user_id = run['user_id']
                    # Get balance
                    balance_doc = await self.db.credit_balances.find_one({"user_id": user_id})
                    if balance_doc and balance_doc.get('balance', 0) >= 1:
                        # Deduct credit
                        await self.db.credit_balances.update_one(
                            {"user_id": user_id},
                            {"$inc": {"balance": -1}}
                        )
                        # Create ledger entry
                        await self.db.credit_ledger.insert_one({
                            "id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "delta": -1,
                            "reason": f"Run item {item_id}",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
            
            except Exception as e:
                logger.error(f"Error processing item {item.get('id')}: {str(e)}")
                await self.db.run_items.update_one(
                    {"id": item['id']},
                    {"$set": {
                        "status": "failed",
                        "error_code": "PROCESSING_ERROR",
                        "error_message": str(e),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
    
    async def write_results_to_sheet(self, run_id: str, user_id: str, project: Dict, field_mapping: Dict):
        """Write results back to Google Sheet"""
        try:
            # Get successful items
            items = await self.db.run_items.find(
                {"run_id": run_id, "status": {"$in": ["success", "failed"]}}
            ).sort("row_index", 1).to_list(1000)
            
            if not items:
                return
            
            # Prepare data to write
            output_mode = field_mapping.get('output_mode', 'same_sheet')
            
            if output_mode == "same_sheet":
                # Write to same sheet - append new columns
                # Get the last column
                sheet_values = await self.google_service.get_sheet_values(
                    user_id,
                    project['spreadsheet_id'],
                    project['sheet_name'],
                    'A1:Z1'
                )
                
                if sheet_values:
                    last_col_idx = len(sheet_values[0])
                    # Convert to A1 notation
                    col_letters = self._index_to_column(last_col_idx + 1)
                    
                    # Write headers
                    header_range = f"{col_letters}{project.get('header_row', 1)}"
                    await self.google_service.write_sheet_values(
                        user_id,
                        project['spreadsheet_id'],
                        project['sheet_name'],
                        header_range,
                        [["Icebreaker", "Status", "Error"]]
                    )
                    
                    # Write data
                    for item in items:
                        row_idx = item['row_index']
                        icebreaker = item.get('output_icebreaker', '')
                        status = "Success" if item['status'] == 'success' else "Failed"
                        error = item.get('error_message', '')
                        
                        data_range = f"{col_letters}{row_idx}"
                        await self.google_service.write_sheet_values(
                            user_id,
                            project['spreadsheet_id'],
                            project['sheet_name'],
                            data_range,
                            [[icebreaker, status, error]]
                        )
        
        except Exception as e:
            logger.error(f"Error writing results to sheet: {str(e)}")
    
    def _index_to_column(self, idx: int) -> str:
        """Convert column index to A1 notation (1=A, 2=B, 27=AA, etc.)"""
        result = ""
        while idx > 0:
            idx -= 1
            result = chr(idx % 26 + 65) + result
            idx //= 26
        return result
    
    async def retry_failed(self, run_id: str):
        """Reset failed items to pending for retry"""
        await self.db.run_items.update_many(
            {"run_id": run_id, "status": "failed"},
            {"$set": {"status": "pending", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
