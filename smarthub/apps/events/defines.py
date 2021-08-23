"""App specific constants"""
from .models import EventTriggerType

NUMERIC_TRIGGER_TYPES = [
    EventTriggerType.LESS_THAN,
    EventTriggerType.LESS_THAN_OR_EQUAL,
    EventTriggerType.GREATER_THAN_OR_EQUAL,
    EventTriggerType.GREATER_THAN,
]

NON_NUMERIC_TRIGGER_TYPES = [EventTriggerType.EQUAL, EventTriggerType.NOT_EQUAL]
