import time
import hashlib
import logging
from typing import List, Dict, Any

from backend.domain.interfaces.event_bus import IEventBus
from backend.domain.interfaces.alert_rule import IAlertRule
from backend.domain.events.base_events import AlertTriggeredEvent, BaseEvent
from backend.application.dtos.alert_dtos import Urgency, RuleResult

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus
        self.rules: List[IAlertRule] = []
        # Deduplication cache: {hash_key: timestamp}
        self._dedup_cache: Dict[str, float] = {}
        self.dedup_ttl_seconds = 300 # 5 minutes
        
    def add_rule(self, rule: IAlertRule):
        self.rules.append(rule)

    def _generate_hash(self, message: str, urgency: str) -> str:
        data = f"{message}|{urgency}".encode('utf-8')
        return hashlib.md5(data).hexdigest()

    def _is_duplicate(self, hash_key: str) -> bool:
        current_time = time.time()
        # Clean up old cache entries
        keys_to_delete = [k for k, v in self._dedup_cache.items() if current_time - v > self.dedup_ttl_seconds]
        for k in keys_to_delete:
            del self._dedup_cache[k]
            
        if hash_key in self._dedup_cache:
            return True
        
        self._dedup_cache[hash_key] = current_time
        return False

    async def process_event(self, event_data: BaseEvent):
        best_result: RuleResult = RuleResult(is_matched=False)
        
        for rule in self.rules:
            try:
                result = rule.evaluate(event_data)
                if result.is_matched:
                    # Lấy rule có weight cao nhất
                    if not best_result.is_matched or result.weight > best_result.weight:
                        best_result = result
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {e}")
                    
        if best_result.is_matched and best_result.urgency in (Urgency.CRITICAL, Urgency.HIGH):
            hash_key = self._generate_hash(best_result.message or "", best_result.urgency.value)
            
            if self._is_duplicate(hash_key):
                logger.info(f"Duplicate alert suppressed: {best_result.message}")
                return
                
            logger.info(f"[ALERT FIRED] {best_result.urgency}: {best_result.message}")
            event = AlertTriggeredEvent(
                source_origin="AlertEngine",
                correlation_id="system-alert",
                urgency_level=best_result.urgency.lower(),
                alert_message=best_result.message
            )
            await self.event_bus.publish(event)
