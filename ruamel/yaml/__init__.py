from __future__ import annotations

from typing import List, Any

import re
import json


def _parse_scalar(value: str):
    if value is None:
        return None
    v = value.strip()
    if v.lower() in ("null", "none", "~"):
        return None
    if v == "":
        return ""
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    # try int
    try:
        if "." not in v:
            return int(v)
        return float(v)
    except Exception:
        pass
    # strip quotes
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


class YAML:
    def __init__(self, typ: str = "safe"):
        self.typ = typ

    def load(self, stream) -> Any:
        text = stream.read()
        docs = self._split_docs(text)
        if not docs:
            return {}
        # only return first document
        return self._parse_document(docs[0])

    def load_all(self, stream) -> List[Any]:
        text = stream.read()
        docs = self._split_docs(text)
        return [self._parse_document(d) for d in docs if d.strip()]

    def dump(self, data: Any, stream) -> None:
        """
        Very small YAML emitter for mappings, lists and scalars.
        Not a full implementation — suitable for tests which write simple dicts.
        """
        def _emit_scalar(val):
            if val is None:
                return "null"
            if isinstance(val, bool):
                return "true" if val else "false"
            if isinstance(val, (int, float)):
                return str(val)
            # for strings, use JSON to produce a quoted-safe representation
            return json.dumps(str(val))

        def _emit(obj, indent=0):
            pad = " " * indent
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        stream.write(f"{pad}{k}:\n")
                        _emit(v, indent=indent + 2)
                    else:
                        stream.write(f"{pad}{k}: {_emit_scalar(v)}\n")
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        stream.write(f"{pad}-\n")
                        _emit(item, indent=indent + 2)
                    else:
                        stream.write(f"{pad}- {_emit_scalar(item)}\n")
            else:
                stream.write(f"{pad}{_emit_scalar(obj)}\n")

        _emit(data, indent=0)

    def _split_docs(self, text: str) -> List[str]:
        # split on YAML document marker --- at line start
        parts = re.split(r"^---\s*$", text, flags=re.MULTILINE)
        parts = [p for p in parts if p.strip()]
        return parts

    def _parse_document(self, text: str) -> Any:
        # Very small YAML subset parser: mappings, nested mappings, and simple lists prefixed with '- '
        lines = [ln.rstrip("\n") for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if not lines:
            return {}
        root = {}
        stack = [( -1, root )]

        for ln in lines:
            indent = len(ln) - len(ln.lstrip(" "))
            cur = ln.lstrip()
            # list item
            if cur.startswith("- "):
                val = cur[2:]
                # ensure current container is list
                while stack and indent <= stack[-1][0]:
                    stack.pop()
                parent = stack[-1][1]
                if not isinstance(parent, list):
                    # create a new list under the most recently added key in the mapping
                    if isinstance(parent, dict):
                        if parent:
                            last_key = next(reversed(parent))
                            # if the last value is an empty mapping, replace it with a list
                            if isinstance(parent[last_key], dict) and not parent[last_key]:
                                lst = []
                                parent[last_key] = lst
                                parent = lst
                            else:
                                # fallback: attach a new list under the last key
                                lst = []
                                parent[last_key] = lst
                                parent = lst
                        else:
                            # parent is an empty mapping that was created for a nested key
                            # find the mapping that contains this empty mapping and replace
                            if len(stack) >= 2 and isinstance(stack[-2][1], dict):
                                container_map = stack[-2][1]
                                last_key = next(reversed(container_map))
                                lst = []
                                container_map[last_key] = lst
                                parent = lst
                            else:
                                lst = []
                                parent = lst
                    else:
                        lst = []
                        parent = lst
                # append scalar or create nested dict
                if ": " in val or val.endswith(":"):
                    # nested mapping starts here
                    item = {}
                    parent.append(item)
                    stack.append((indent, item))
                else:
                    parent.append(_parse_scalar(val))
                continue

            # mapping key
            if ":" in cur:
                k, sep, rest = cur.partition(":")
                key = k.strip()
                value = rest.strip()
                # find container at correct indent
                while stack and indent <= stack[-1][0]:
                    stack.pop()
                container = stack[-1][1]
                if value == "":
                    # nested mapping
                    new = {}
                    container[key] = new
                    stack.append((indent, new))
                else:
                    container[key] = _parse_scalar(value)
                continue

            # fallback: ignore
        return root
