from dataclasses import dataclass, field


@dataclass
class Config:
    force: bool = False
    verbose: bool = False
    metadata: dict = field(default_factory=dict)
