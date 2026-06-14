from datetime import datetime
from typing import List, Dict, Any

class ReconciliationEngine:
    """Động cơ xử lý giải quyết xung đột (Conflict Resolution) trong Auto Sync."""
    
    def __init__(self):
        pass
        
    def detect_time_overlap(self, new_event: dict, existing_events: List[dict]) -> bool:
        """Kiểm tra có bị trùng lịch với bất kỳ sự kiện nào đang tồn tại không (Rule 1)."""
        try:
            new_start = datetime.fromisoformat(new_event['start_time'].replace("Z", "+00:00"))
            new_end = datetime.fromisoformat(new_event['end_time'].replace("Z", "+00:00"))
            
            for existing in existing_events:
                ex_start = datetime.fromisoformat(existing['start_time'].replace("Z", "+00:00"))
                ex_end = datetime.fromisoformat(existing['end_time'].replace("Z", "+00:00"))
                
                # Check overlap: Max(start1, start2) < Min(end1, end2)
                overlap_start = max(new_start, ex_start)
                overlap_end = min(new_end, ex_end)
                if overlap_start < overlap_end:
                    return True
        except Exception:
            return False
        return False

    def resolve_concurrent_update(self, local_event: dict, remote_event: dict) -> str:
        """
        Rule 2: Last-Write-Wins.
        Trả về 'LOCAL_WINS' hoặc 'REMOTE_WINS' dựa vào updated_at.
        """
        try:
            local_updated = datetime.fromisoformat(local_event['updated_at'].replace("Z", "+00:00"))
            remote_updated = datetime.fromisoformat(remote_event['updated_at'].replace("Z", "+00:00"))
            
            if remote_updated > local_updated:
                return 'REMOTE_WINS'
            else:
                return 'LOCAL_WINS'
        except Exception:
            return 'REMOTE_WINS' # Default to remote truth if parsing fails

    def process_sync_batch(self, remote_events: List[dict], local_events: List[dict]) -> Dict[str, List[Any]]:
        """So khớp ID và trả về các Batch Insert, Update, Soft-Delete."""
        local_dict = {ev['source_id']: ev for ev in local_events}
        remote_dict = {ev['source_id']: ev for ev in remote_events}
        
        to_insert = []
        to_update = []
        to_soft_delete = []
        
        # 1. Check Insert & Update
        for rid, remote_ev in remote_dict.items():
            if rid not in local_dict:
                to_insert.append(remote_ev)
            else:
                local_ev = local_dict[rid]
                winner = self.resolve_concurrent_update(local_ev, remote_ev)
                if winner == 'REMOTE_WINS':
                    to_update.append(remote_ev)
                    
        # 2. Check Soft Delete (Local có mà Remote ko có)
        for lid, local_ev in local_dict.items():
            if lid not in remote_dict:
                # Mark soft delete
                to_soft_delete.append(local_ev)
                
        return {
            "insert": to_insert,
            "update": to_update,
            "soft_delete": to_soft_delete
        }
