from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional


@dataclass
class Habit(ABC):
    habit_id: int
    name: str
    periodicity: str
    created_at: datetime = field(default_factory=datetime.now)
    completion_dates: list[date] = field(default_factory=list)
    
    def mark_completed(self, when: Optional[date] = None) -> None:
        if when is None:
            when = date.today()
            
        if when not in self.completion_dates:
            self.completion_dates.append(when)
        
    
    def current_streak(self) -> int:
        if not self.completion_dates:
            return 0
        dates_set = set(self.completion_dates)
        streak = 0
        check_date = date.today()
        while check_date in dates_set:
            streak = streak + 1 
            check_date = check_date - timedelta(days=1)
            
        return streak
    
    @abstractmethod
    def is_due(self, today: Optional[date] = None) -> bool:
        pass
    
