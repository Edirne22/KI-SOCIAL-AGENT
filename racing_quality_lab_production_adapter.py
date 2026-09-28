"""Adapter that evaluates Quality-Lab cases through real production Racing truth gates."""
from racing_event_contract import session_errors
from racing_source_claim_guard import claim_strength_errors
from racing_source_entity_guard import errors as entity_errors
from chief_quality_manager import human_text_review

def production_truth_errors(item, caption):
    errors=[]
    errors.extend(session_errors(item,caption))
    errors.extend(claim_strength_errors(item,caption))
    errors.extend(entity_errors(item,caption))
    human_ok,human_errors=human_text_review("Motorcycle Racing",item,caption)
    if not human_ok:
        errors.extend(human_errors)
    return errors
