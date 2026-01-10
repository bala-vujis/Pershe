from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class CreditService:
    def __init__(self, db):
        self.db = db
    
    async def get_balance(self, user_id: str) -> int:
        """Get user's credit balance"""
        balance_doc = await self.db.credit_balances.find_one({"user_id": user_id})
        if not balance_doc:
            # Create initial balance
            await self.db.credit_balances.insert_one({
                "user_id": user_id,
                "balance": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return 0
        return balance_doc.get('balance', 0)
    
    async def add_credits(self, user_id: str, amount: int, reason: str):
        """Add credits to user's balance"""
        # Update balance
        await self.db.credit_balances.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}},
            upsert=True
        )
        
        # Create ledger entry
        await self.db.credit_ledger.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "delta": amount,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    async def deduct_credits(self, user_id: str, amount: int, reason: str) -> bool:
        """Deduct credits from user's balance. Returns False if insufficient balance."""
        balance = await self.get_balance(user_id)
        
        if balance < amount:
            logger.warning(f"Insufficient credits for user {user_id}. Balance: {balance}, Required: {amount}")
            return False
        
        # Update balance
        await self.db.credit_balances.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": -amount}}
        )
        
        # Create ledger entry
        await self.db.credit_ledger.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "delta": -amount,
            "reason": reason,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return True
