from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TasteDNA:
    """
    User's current preference representation.

    Values represent preference strength for each attribute.
    """

    user_id: str

    cuisine: Dict[str, float] = field(default_factory=dict)
    protein: Dict[str, float] = field(default_factory=dict)
    flavor: Dict[str, float] = field(default_factory=dict)
    spice_level: Dict[str, float] = field(default_factory=dict)
    base: Dict[str, float] = field(default_factory=dict)
    meal_type: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "cuisine": self.cuisine,
            "protein": self.protein,
            "flavor": self.flavor,
            "spice_level": self.spice_level,
            "base": self.base,
            "meal_type": self.meal_type,
        }