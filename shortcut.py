from typing import Dict, TypedDict


class Shortcut(TypedDict):
    AppName: str
    Exe: str

class ShortcutsVDF(TypedDict):
    shortcuts: Dict[str, Shortcut]
