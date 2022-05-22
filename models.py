from dataclasses import dataclass
from typing import Tuple


@dataclass
class matching:
    keywords: Tuple[str, ...]
    match_keywords : str
