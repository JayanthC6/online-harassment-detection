from abc import ABC, abstractmethod
from typing import Dict, Any

class ModelAdapter(ABC):
    @abstractmethod
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Returns a dictionary representing the prediction.
        Expected schema:
        {
            "primary_label": "Hate Speech",
            "confidence": 0.95,
            "secondary_labels": {
                "Threat": 0.82,
                "Cyberbullying": 0.45
            },
            "model": "heuristic-distilbert",
            "label": "harassing", # Derived (legacy compatibility)
            "category": "hate_speech", # Derived (legacy compatibility)
            "explanation": [...] # Optional explanation
        }
        """
        pass
