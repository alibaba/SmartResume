"""
Address normalizer module.
Normalizes Chinese address strings to standard name_path/code_path using a city code CSV.
"""
import csv
import os
from typing import Optional


class AddressNormalizer:
    """Normalize address strings using a city code tree (CSV)."""

    class Node:
        def __init__(
            self,
            code: Optional[str],
            name: Optional[str],
            parent: Optional["AddressNormalizer.Node"] = None,
            weight: int = 3,
            code_path: Optional[str] = None,
            name_path: Optional[str] = None,
        ):
            self.code = code
            self.name = name
            self.parent = parent
            self.code_path = code_path
            self.name_path = name_path
            self.children: list = []
            self.aliases: set = set()
            self.weight = weight

        def add_child(self, child: "AddressNormalizer.Node") -> None:
            self.children.append(child)
            child.parent = self

    def __init__(self, csv_file: str) -> None:
        """
        Initialize normalizer with a city code CSV.

        Args:
            csv_file: Path to CSV with columns: code, parent_code, name, code_path, name_path
        """
        self.tree = self.build_tree(csv_file)
        self.all_nodes = list(self.tree.values())

    def create_aliases(self, name: str) -> set:
        """Create aliases by stripping common suffixes (市, 县, 省, etc.)."""
        aliases = set()
        suffixes = ["市", "县", "省", "自治区", "区", "自治州"]
        for suffix in suffixes:
            if name.endswith(suffix):
                alias = name[: -len(suffix)]
                if alias != name and len(alias) > 1:
                    aliases.add(alias)
        return aliases

    def build_tree(self, csv_file: str) -> dict:
        """Build tree from CSV. CSV must have: code, parent_code, name, code_path, name_path."""
        tree: dict = {}
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("code", "").strip()
                name = row.get("name", "").strip()
                parent_code = row.get("parent_code", "").strip()
                code_path = row.get("code_path", "").strip()
                name_path = row.get("name_path", "").strip()
                if not code or not name:
                    continue

                weight = (
                    5
                    if name
                    in [
                        "北京",
                        "上海",
                        "深圳",
                        "广州",
                        "珠海",
                        "香港",
                        "杭州",
                        "重庆",
                        "南京",
                    ]
                    else 3
                )
                node = self.Node(
                    code=code,
                    name=name,
                    weight=weight,
                    code_path=code_path or None,
                    name_path=name_path or None,
                )
                node.aliases = self.create_aliases(name)
                node.aliases.add(name)
                tree[code] = node

                if parent_code in tree:
                    parent = tree[parent_code]
                    parent.add_child(node)
                    node.weight = parent.weight + 1

        return tree

    def get_leaf_nodes(self) -> list:
        """Return nodes that have no children."""
        return [node for node in self.tree.values() if not node.children]

    def norm_address(self, address: Optional[str]) -> Optional["AddressNormalizer.Node"]:
        """
        Normalize an address string to the best matching node.

        Args:
            address: Raw address string (e.g. "海淀", "南山区", "河南信阳")

        Returns:
            Node with name_path/code_path, or None if no match. Node.name may be None for no match.
        """
        if not address or not str(address).strip():
            return None

        address = str(address).strip()
        matches = []
        for node in self.all_nodes:
            for alias in node.aliases:
                if alias in address:
                    matches.append(node)
                    break

        matches.sort(key=lambda x: (x.weight, len(x.name or "")), reverse=True)
        if len(matches) > 1:
            both_have_paths = matches[0].code_path and matches[1].code_path
            is_child = both_have_paths and matches[0].code_path in matches[1].code_path
            depth_0 = len(matches[0].code_path.split("/"))
            depth_1 = len(matches[1].code_path.split("/"))
            child_deeper = depth_1 > depth_0
            is_deeper = is_child and child_deeper
            if is_deeper:
                matches[0] = matches[1]
        match_res = matches[0] if matches else self.Node(None, None)

        if match_res.code_path:
            codes = match_res.code_path.split("/")
            if len(codes) == 5 and match_res.parent:
                return match_res.parent
            return match_res

        return match_res if match_res.code_path else None

    def print_tree(self) -> None:
        """Print tree structure (for debugging)."""
        roots = [node for node in self.tree.values() if node.parent is None]
        for root in roots:
            self._print_node(root, level=0)

    def _print_node(self, node: "AddressNormalizer.Node", level: int) -> None:
        indent = " " * (level * 4)
        aliases = ", ".join(a for a in (node.aliases or set()) if a != node.name)
        if aliases:
            print(f"{indent}{node.name} (别名: {aliases}) {node.weight}")
        else:
            print(f"{indent}{node.name} {node.weight}")
        for child in node.children:
            self._print_node(child, level + 1)


def get_default_csv_path() -> str:
    """Return default path to city_code.csv under this package."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "norm_table", "city_code.csv")


def create_normalizer(csv_file: Optional[str] = None) -> Optional[AddressNormalizer]:
    """
    Create an AddressNormalizer instance.

    Args:
        csv_file: Path to city code CSV. If None, uses package default norm_table/city_code.csv.

    Returns:
        AddressNormalizer if CSV exists, else None.
    """
    path = csv_file or get_default_csv_path()
    if not os.path.exists(path):
        return None
    try:
        return AddressNormalizer(path)
    except Exception:
        return None


# Default instance (lazy, uses package norm_table if present)
_default_normalizer: Optional[AddressNormalizer] = None


def get_default_normalizer() -> Optional[AddressNormalizer]:
    """Return or create the default AddressNormalizer (lazy, once)."""
    global _default_normalizer
    if _default_normalizer is None:
        _default_normalizer = create_normalizer()
    return _default_normalizer


# Module-level instance for compatibility (e.g. formatter). None if CSV not found.
normalizer = get_default_normalizer()
