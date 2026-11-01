#!/usr/bin/env python3
"""Check the controlled Toucan Selenium source format with Python's stdlib.

This is a deliberately small source linter, not a C preprocessor, devicetree
compiler, west resolver or behavior simulator. It understands this project's
object-like aliases, decimal defaults, guarded headers and DTS node/property
format, and rejects unsupported syntax. ZMK keycodes remain symbolic; only
the audited subset used here is accepted. Command-line C defines are not read.

Run: python scripts/verify_port.py --report provenance/port-verification.json
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys

from verify_baseline import (
    Audit, HEX40, HEX64, UPSTREAM_COMMIT, active_config, property_body,
    yaml_field, yaml_named_blocks, yaml_section,
)


ARCHIVES = {
    "config/toucan.keymap": "reference/baseline/config-toucan.keymap",
    "boards/shields/toucan/toucan.keymap": "reference/baseline/shield-toucan.keymap",
    "boards/shields/toucan/toucan.dtsi": "reference/baseline/toucan.dtsi",
}
LAYER_ORDER = ["base", "symbols", "vim_nav", "num_row", "fn_media"]
LAYER_NAMES = {"BASE": "0", "SYMBOLS": "1", "VIM_NAV": "2", "NUM_ROW": "3", "FN_MEDIA": "4"}
OUTER = (0, 11, 12, 23, 24, 35)
TIMINGS = {"TAP_PREFERRED_MS", "HOLD_PREFERRED_MS", "QUICK_TAP_MS", "STICKY_TIMEOUT_MS"}
GUARDS = {
    "TOUCAN_V1_LAYERS_H", "TOUCAN_SELENIUM_TIMING_H",
    "TOUCAN_SELENIUM_ERGOL_H", "TOUCAN_SELENIUM_BEHAVIORS_DTSI",
}
# This is the audited v0.3 subset, not a replacement for keys.h. Unknown symbols
# fail closed and must be reviewed against the pinned upstream header.
KEYS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") | {"N" + str(n) for n in range(10)}
KEYS |= {"F" + str(n) for n in range(1, 13)} | {
    "LSHIFT", "RSHIFT", "LALT", "RALT", "LCTRL", "RCTRL", "LGUI", "RGUI",
    "SPACE", "TAB", "ENTER", "BACKSPACE", "ESCAPE", "DEL", "HOME", "END",
    "LEFT", "RIGHT", "UP", "DOWN", "PG_UP", "PG_DN", "SEMI", "COMMA", "DOT",
    "FSLH", "GRAVE", "CARET", "NUBS", "PIPE2", "DLLR", "PRCNT", "RPAR",
    "AMPS", "STAR", "SQT", "LBRC", "RBRC", "EQUAL", "BSLH", "PLUS", "MINUS",
    "DQT", "TILDE", "LBKT", "RBKT", "UNDER", "LPAR", "PIPE", "SLCK", "PSCRN",
    "INS", "C_NEXT", "C_PREV", "C_VOL_UP", "C_VOL_DN", "C_BRI_UP", "C_BRI_DN",
    "C_PP", "C_MUTE", "C_AL_LOCK",
}
MODIFIERS = {"LSHIFT", "RSHIFT", "LALT", "RALT", "LCTRL", "RCTRL", "LGUI", "RGUI"}
WRAPPERS = {"LS", "RS", "LA", "RA", "LC", "RC", "LG", "RG"}
MASKS = {"MOD_LCTL", "MOD_RCTL", "MOD_LGUI", "MOD_RGUI", "MOD_LALT", "MOD_RALT", "MOD_LSFT", "MOD_RSFT"}
BUILTIN_CELLS = {
    "none": 0, "trans": 0, "kp": 1, "mo": 1, "to": 1, "sk": 1, "sl": 1,
    "bt": 2, "out": 1, "msc": 1, "bootloader": 0, "sys_reset": 0,
    "macro_tap": 0, "macro_press": 0, "macro_release": 0,
    "macro_pause_for_release": 0, "macro_param_1to1": 0,
}
BUILTIN_DEFS = {
    "MACRO_PLACEHOLDER": "0", "BT_CLR": "0 0", "BT_SEL": "3", "OUT_TOG": "0",
}
CUSTOM_CELLS = {
    "hrm": 2, "sc": 2, "ltp": 2, "osl": 1, "bsl": 2, "osm": 1, "bsk": 2,
    "sym": 0, "sym_shift": 0, "lkp": 1, "losm": 1, "lbsk": 2,
    "vim_prev": 0, "vim_next": 0, "bt_sel1_clr": 0,
}


def uncomment(text: str) -> str:
    """Strip C comments while retaining quoted strings, including URL text."""
    pattern = r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*'
    return re.sub(pattern, lambda m: m[0] if m[0].startswith('"') else " ", text, flags=re.S)


TOKEN = re.compile(r'\s+|"(?:\\.|[^"\\])*"|&[A-Za-z_]\w*|#[A-Za-z_][\w-]*|[A-Za-z_][\w,@-]*|\d+|[/{};:=<>,()|]')


def tokens(text: str) -> list[str]:
    result, pos = [], 0
    while pos < len(text):
        match = TOKEN.match(text, pos)
        if not match:
            raise ValueError("Unsupported source syntax near " + repr(text[pos:pos + 45]))
        value = match[0]
        if not value.isspace():
            result.append(value)
        pos = match.end()
    return result


def source_parts(text: str) -> tuple[str, dict[str, str], list[str]]:
    """Read only object defines, includes and conventional include guards."""
    body, defines, includes, guards = [], {}, [], []
    for line in uncomment(text).splitlines():
        if not line.lstrip().startswith("#") or re.match(r'\s*#binding-cells\s*=', line):
            body.append(line)
            continue
        match = re.fullmatch(r'\s*#\s*(\w+)\s*(.*?)\s*', line)
        if not match:
            raise ValueError("Unsupported preprocessor directive: " + line)
        directive, rest = match.groups()
        if directive == "include":
            if not re.fullmatch(r'<[^<>]+>|"[^"\n]+"', rest):
                raise ValueError("Only literal includes are supported")
            includes.append(rest)
        elif directive == "define":
            definition = re.fullmatch(r'([A-Za-z_]\w*)(?:\s+(.*))?', rest)
            if not definition:
                raise ValueError("Function-like or malformed #define is unsupported: " + rest)
            name, value = definition.groups()
            if name in defines:
                raise ValueError("Duplicate object define: " + name)
            defines[name] = value or ""
        elif directive == "ifndef":
            if rest not in GUARDS | TIMINGS:
                raise ValueError("Unsupported conditional guard: " + rest)
            guards.append(rest)
        elif directive == "endif" and not rest:
            if not guards:
                raise ValueError("Unmatched #endif")
            guards.pop()
        else:
            raise ValueError("Unsupported conditional/directive: #" + directive + " " + rest)
    if guards:
        raise ValueError("Unclosed header guard")
    return "\n".join(body), defines, includes


def expand(values: list[str], definitions: dict[str, str], trail: tuple[str, ...] = ()) -> list[str]:
    result = []
    for value in values:
        if value in definitions:
            if value in trail:
                raise ValueError("Cyclic object alias: " + " -> ".join(trail + (value,)))
            result.extend(expand(tokens(definitions[value]), definitions, trail + (value,)))
        else:
            result.append(value)
    return result


@dataclass
class Node:
    name: str
    label: str | None = None
    props: dict[str, list[str]] = field(default_factory=dict)
    children: list["Node"] = field(default_factory=list)


class DTSSubset:
    def __init__(self, values: list[str]):
        self.values, self.pos = values, 0

    def take(self, expected: str | None = None) -> str:
        if self.pos >= len(self.values):
            raise ValueError("Unexpected end of controlled DTS source")
        value = self.values[self.pos]
        self.pos += 1
        if expected is not None and value != expected:
            raise ValueError("Expected " + expected + ", got " + value)
        return value

    def scope(self, nested: bool = False) -> tuple[dict[str, list[str]], list[Node]]:
        properties, children = {}, []
        while self.pos < len(self.values):
            if self.values[self.pos] == "}":
                if not nested:
                    raise ValueError("Unexpected closing brace")
                self.take("}")
                self.take(";")
                return properties, children
            name, label = self.take(), None
            if not re.fullmatch(r'/|&[A-Za-z_]\w*|#?[A-Za-z_][\w,@-]*', name):
                raise ValueError("Invalid node/property token: " + name)
            if self.pos < len(self.values) and self.values[self.pos] == ":":
                self.take(":")
                label, name = name, self.take()
            following = self.take()
            if following == "{":
                props, nodes = self.scope(True)
                children.append(Node(name, label, props, nodes))
                continue
            if label is not None or name in properties:
                raise ValueError("Label on property or duplicate property: " + name)
            if following == ";":
                properties[name] = []
            elif following == "=":
                value = []
                while self.pos < len(self.values) and self.values[self.pos] != ";":
                    value.append(self.take())
                self.take(";")
                if not value:
                    raise ValueError("Empty property value: " + name)
                properties[name] = value
            else:
                raise ValueError("Expected node, assignment or boolean property at " + name)
        if nested:
            raise ValueError("Missing closing brace")
        return properties, children

    def parse(self) -> list[Node]:
        props, nodes = self.scope()
        if props:
            raise ValueError("Properties outside a root node")
        return nodes


def groups(values: list[str]) -> list[list[str]]:
    result, current, depth, separator = [], None, 0, False
    for value in values:
        if value == "<":
            if current is not None or separator:
                raise ValueError("Nested angle group or missing group comma")
            current = []
        elif value == ">":
            if current is None or depth:
                raise ValueError("Unbalanced angle group or expression")
            result.append(current)
            current = None
            separator = True
        elif current is None:
            if value != "," or not separator:
                raise ValueError("Unexpected token outside angle group: " + value)
            separator = False
        else:
            depth += (value == "(") - (value == ")")
            if depth < 0:
                raise ValueError("Unbalanced parentheses")
            current.append(value)
    if current is not None or not result or not separator:
        raise ValueError("Missing or unclosed angle group")
    return result


def atom(values: list[str], pos: int) -> tuple[str, int]:
    if pos >= len(values) or values[pos].startswith("&"):
        raise ValueError("Missing binding parameter")
    name = values[pos]
    if not re.fullmatch(r'[A-Za-z_]\w*|\d+', name):
        raise ValueError("Unsupported binding expression: " + name)
    pos += 1
    if pos < len(values) and values[pos] == "(":
        if name not in WRAPPERS:
            raise ValueError("Unsupported keycode wrapper: " + name)
        child, pos = atom(values, pos + 1)
        if pos >= len(values) or values[pos] != ")":
            raise ValueError("Expected closing keycode wrapper parenthesis")
        return name + "(" + child + ")", pos + 1
    return name, pos


def is_key(value: str) -> bool:
    if value in KEYS:
        return True
    match = re.fullmatch(r'([A-Z]{2})\((.*)\)', value)
    return bool(match and match[1] in WRAPPERS and is_key(match[2]))


def is_modifier(value: str) -> bool:
    if value in MODIFIERS:
        return True
    match = re.fullmatch(r'([A-Z]{2})\((.*)\)', value)
    return bool(match and match[1] in WRAPPERS and is_modifier(match[2]))


@dataclass(frozen=True)
class Binding:
    ref: str
    args: tuple[str, ...] = ()

    def show(self) -> str:
        return "&" + self.ref + (" " + " ".join(self.args) if self.args else "")


def bindings(values: list[str], definitions: dict[str, str], cells: dict[str, int], *, placeholders: bool = False) -> list[Binding]:
    result = []
    for group in groups(expand(values, definitions)):
        pos = 0
        while pos < len(group):
            ref = group[pos]
            pos += 1
            if not ref.startswith("&") or ref[1:] not in cells:
                raise ValueError("Unknown behavior reference or unresolved alias: " + ref)
            name, arguments = ref[1:], []
            for _ in range(cells[name]):
                value, pos = atom(group, pos)
                arguments.append(value)
            item = Binding(name, tuple(arguments))
            validate_binding(item, placeholders)
            result.append(item)
    return result


def validate_binding(item: Binding, placeholders: bool) -> None:
    name, args = item.ref, item.args
    layer = lambda value: value.isdecimal() and 0 <= int(value) < 5
    key = lambda value: is_key(value) or placeholders and value == "0"
    mod = lambda value: is_modifier(value) or placeholders and value == "0"
    valid = True
    if name == "kp":
        valid = key(args[0])
    elif name in {"mo", "to", "sl", "osl"}:
        valid = layer(args[0])
    elif name in {"sk", "osm", "lkp", "losm"}:
        valid = mod(args[0])
    elif name == "hrm":
        valid = args[0] in MODIFIERS and key(args[1])
    elif name in {"sc", "ltp"}:
        valid = layer(args[0]) and key(args[1])
    elif name == "bsl":
        valid = layer(args[0]) and args[0] == args[1]
    elif name in {"bsk", "lbsk"}:
        valid = mod(args[0]) and args[0] == args[1]
    elif name == "bt":
        valid = args[0] == "0" and args[1] == "0" or args[0] == "3" and args[1] in {str(i) for i in range(5)}
    elif name == "out":
        valid = args[0] in {"0", "1", "2"}
    elif name == "msc":
        valid = args[0] in {"SCRL_LEFT", "SCRL_RIGHT", "SCRL_UP", "SCRL_DOWN"}
    if not valid:
        raise ValueError("Invalid parameter domain for " + item.show())


class PortAudit(Audit):
    def prepare(self) -> None:
        self.parts = {}
        self.definitions = dict(BUILTIN_DEFS)
        for path in ("config/layers.h", "config/timing.h", "config/ergol.h", "config/selenium-behaviors.dtsi", "config/toucan.keymap"):
            body, definitions, includes = source_parts(self.read(path))
            if path.endswith(".h") and body.strip():
                raise ValueError("Header contains unsupported non-directive source: " + path)
            meaningful = {k: v for k, v in definitions.items() if k not in GUARDS}
            if path.endswith("selenium-behaviors.dtsi") and meaningful:
                raise ValueError("Unexpected helper-local object defines")
            if path.endswith("toucan.keymap") and meaningful != {"ZMK_POINTING_DEFAULT_SCRL_VAL": "25"}:
                raise ValueError("Unexpected keymap object defines or wheel default")
            self.parts[path] = (body, definitions, includes)
            for name, value in definitions.items():
                if name in GUARDS:
                    if value:
                        raise ValueError("Nonempty include-guard define: " + name)
                    continue
                if name in self.definitions:
                    raise ValueError("Repeated local define: " + name)
                self.definitions[name] = value
        self.cells = {**BUILTIN_CELLS, **CUSTOM_CELLS}
        self.check("controlled_source_subset", True, "Literal includes, object aliases and guarded headers parsed; no external preprocessing")

    def provenance_archives(self) -> None:
        record = json.loads(self.read("provenance/upstream.json"))
        self.check("upstream_identity", record.get("schema_version") == 1 and record.get("stage") == "official-baseline"
                   and record.get("upstream", {}).get("commit") == UPSTREAM_COMMIT, "Historical baseline record remains unchanged in scope")
        entries = record["upstream_files"]
        self.check("upstream_file_count", len(entries) == 47, "44 live source records and three archived originals")
        seen_local, seen_upstream = set(), set()
        for entry in entries:
            relative = entry["local_path"]
            duplicate = relative in seen_local or entry["upstream_path"] in seen_upstream
            seen_local.add(relative)
            seen_upstream.add(entry["upstream_path"])
            self.check("provenance_unique:" + relative, not duplicate, "Unique historical source and destination")
            inspected = ARCHIVES.get(relative, relative)
            payload = self.path(inspected).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
            self.check("upstream_bytes:" + relative, entry.get("mode") == "100644"
                       and bool(HEX64.fullmatch(entry["sha256"])) and hashlib.sha256(payload).hexdigest() == entry["sha256"].lower()
                       and bool(HEX40.fullmatch(entry["git_blob"])) and blob == entry["git_blob"].lower(), "Recorded SHA-256 and Git blob ID checked at " + inspected)
        self.check("three_archived_originals", set(ARCHIVES).issubset(seen_local), "All three intentionally edited source files have baseline records")
        normalised = record["normalised_files"]
        expected = {"config/toucan_left.conf", "config/toucan_right.conf"}
        self.check("normalised_config_entries", len(normalised) == 2 and {item["local_path"] for item in normalised} == expected, "Exactly two normalized per-half files")
        for entry in normalised:
            payload = self.path(entry["local_path"]).read_bytes()
            self.check("normalised_bytes:" + entry["local_path"], payload == self.path(entry["source_path"]).read_bytes()
                       and hashlib.sha256(payload).hexdigest() == entry["sha256"].lower(), "Per-half normalization remains byte-identical to source")
        self.observed["historical_upstream_records"] = len(entries)
        self.observed["archived_originals"] = ARCHIVES

    def includes_and_aliases(self) -> None:
        expected = {
            "config/toucan.keymap": ['<behaviors.dtsi>', '<dt-bindings/zmk/keys.h>', '<dt-bindings/zmk/bt.h>', '<dt-bindings/zmk/outputs.h>', '<dt-bindings/zmk/pointing.h>', '"layers.h"', '"ergol.h"', '"selenium-behaviors.dtsi"'],
            "config/selenium-behaviors.dtsi": ['<dt-bindings/zmk/keys.h>', '<dt-bindings/zmk/bt.h>', '"layers.h"', '"timing.h"'],
            "config/ergol.h": ['<dt-bindings/zmk/keys.h>'], "config/layers.h": [], "config/timing.h": [],
        }
        for path, includes in expected.items():
            self.check("includes:" + path, self.parts[path][2] == includes, "Controlled include order and set")
        self.check("no_builtin_include_shadow", not self.path("config/behaviors.dtsi").exists(), "Custom helper does not shadow ZMK behaviors.dtsi")
        fallback_body, fallback_defs, fallback_includes = source_parts(self.read("boards/shields/toucan/toucan.keymap"))
        self.check("single_active_keymap", not fallback_body.strip() and not fallback_defs
                   and fallback_includes == ['"../../../config/toucan.keymap"'], "Shield fallback includes exactly the one active user keymap")
        layer_defs = {k: v for k, v in self.parts["config/layers.h"][1].items() if k not in GUARDS}
        self.check("layer_constants", layer_defs == LAYER_NAMES, "Five explicit layer indices, 0 through 4 in priority order")
        alias_defs = {k: v for k, v in self.parts["config/ergol.h"][1].items() if k not in GUARDS}
        if not alias_defs:
            raise ValueError("No Ergo-L aliases")
        for name, value in alias_defs.items():
            if not re.fullmatch(r'[SX]_[A-Z0-9_]+', name):
                raise ValueError("Unsupported alias name: " + name)
            resolved = bindings(["<"] + tokens(value) + [">"], self.definitions, self.cells)
            self.check("alias:" + name, len(resolved) == 1 and resolved[0].ref == "kp", "One validated keypress: " + " ".join(item.show() for item in resolved))
        self.observed["object_aliases"] = len(alias_defs)

    def keymap(self) -> None:
        body = self.parts["config/toucan.keymap"][0]
        roots = DTSSubset(tokens(body)).parse()
        if len(roots) != 1 or roots[0].name != "/" or roots[0].props or len(roots[0].children) != 1:
            raise ValueError("Expected one root containing only keymap")
        keymap = roots[0].children[0]
        if keymap.name != "keymap" or keymap.props != {"compatible": ['"zmk,keymap"']}:
            raise ValueError("Unexpected keymap node or properties")
        self.check("five_layers_in_order", [node.name for node in keymap.children] == LAYER_ORDER, "Base, Symbols, VimNav, NumRow, FnMedia")
        self.layers = {}
        for node in keymap.children:
            if node.name in self.layers or node.children or set(node.props) != {"display-name", "bindings"}:
                raise ValueError("Duplicate layer or unsupported layer syntax: " + node.name)
            row = bindings(node.props["bindings"], self.definitions, self.cells)
            self.layers[node.name] = row
            self.check("positions_42:" + node.name, len(row) == 42, "Parsed " + str(len(row)) + " behavior invocations with checked arity/domains")
            self.check("outer_columns_none:" + node.name, len(row) == 42 and all(row[i] == Binding("none") for i in OUTER), "Indices 0,11,12,23,24,35 are explicitly none")
            self.check("no_shift_hrm:" + node.name, all(item.args[0] not in {"LSHIFT", "RSHIFT"} for item in row if item.ref == "hrm"), "Shift remains on the thumb; no home-row Shift")
        base = self.layers["base"]
        thumbs = [Binding("bsk", ("LSHIFT", "LSHIFT")), Binding("sc", ("2", "BACKSPACE")), Binding("sc", ("4", "ESCAPE")), Binding("sc", ("3", "ENTER")), Binding("ltp", ("2", "SPACE")), Binding("sym")]
        self.check("base_thumbs", base[36:42] == thumbs, "Shift, Backspace/VimNav, Escape/FnMedia, Enter/NumRow, Space/VimNav, Symbols")
        other_thumbs = {
            "symbols": "<&bsl NUM_ROW NUM_ROW &kp SPACE &kp ENTER &trans &trans &trans>",
            "vim_nav": "<&bsk LSHIFT LSHIFT &sc FN_MEDIA DEL &trans &trans &mo FN_MEDIA &lbsk RALT RALT>",
            "num_row": "<&trans &kp RS(SPACE) &trans &trans &kp LS(SPACE) &kp RALT>",
            "fn_media": "<&trans &bootloader &trans &trans &sys_reset &out OUT_TOG>",
        }
        for name, expected in other_thumbs.items():
            self.check("layer_thumbs:" + name, self.layers[name][36:42] == bindings(tokens(expected), self.definitions, self.cells), "Reference thumb transitions, sticky modifiers and service controls")
        self.check("base_hid_letter_rows", base[1:11] == [Binding("kp", (letter,)) for letter in "QWERTYUIOP"]
                   and base[25:35] == [Binding("kp", (letter,)) for letter in ("Z", "X", "C", "V", "B", "N", "M", "COMMA", "DOT", "FSLH")], "Native Ergo-L receives the agreed HID letter positions")
        for index, expected in {14: ("LGUI", "S"), 15: ("LCTRL", "D"), 16: ("LALT", "F"), 19: ("LALT", "J"), 20: ("LCTRL", "K"), 21: ("LGUI", "L")}.items():
            self.check("base_hrm:" + str(index), base[index] == Binding("hrm", expected), "Expected native Ergo-L HID home-row modifier mapping")
        expected_nav = {27: Binding("kp", ("LC(W)",)), 29: Binding("kp", ("LC(P)",)), 41: Binding("lbsk", ("RALT", "RALT"))}
        for index, item in expected_nav.items():
            self.check("vim_key:" + str(index), self.layers["vim_nav"][index] == item, "Native Ergo-L shortcut or base-return AltGr: " + item.show())
        self.check("num_punctuation", self.layers["num_row"][30:35] == [Binding("kp", (v,)) for v in ("C", "DOT", "N", "LS(N)", "MINUS")], "Number-row punctuation uses native Ergo-L HID aliases")
        for index, item in {5: Binding("bt", ("3", "3")), 6: Binding("bt", ("3", "2")), 17: Binding("bt", ("3", "4")), 18: Binding("bt_sel1_clr"), 30: Binding("bt", ("3", "0"))}.items():
            self.check("bluetooth_service:" + str(index), self.layers["fn_media"][index] == item, "Profiles 0..4 and Shift-selective clear remain accessible")
        self.observed["layer_binding_counts"] = {name: len(row) for name, row in self.layers.items()}

    def behaviors_and_timing(self) -> None:
        roots = DTSSubset(tokens(self.parts["config/selenium-behaviors.dtsi"][0])).parse()
        if [node.name for node in roots] != ["&sk", "&sl", "/"] or roots[2].props or len(roots[2].children) != 1 or roots[2].children[0].name != "behaviors":
            raise ValueError("Unexpected helper root/override structure")
        nodes = roots[2].children[0].children
        self.check("custom_behavior_set", len(nodes) == len(CUSTOM_CELLS) and {n.label for n in nodes} == set(CUSTOM_CELLS), "Exactly the supported Toucan behavior labels")
        self.behaviors = {}
        hold_children = {"hrm": ("kp", "kp"), "sc": ("mo", "kp"), "ltp": ("mo", "kp"), "bsl": ("mo", "osl"), "bsk": ("kp", "osm"), "lbsk": ("lkp", "losm")}
        for node in nodes:
            if not node.label or node.label in self.behaviors or node.children:
                raise ValueError("Duplicate/unlabelled behavior or nested behavior node")
            self.behaviors[node.label] = node
            label, props = node.label, node.props
            compatible = props.get("compatible", [])
            expected_compat = '"zmk,behavior-hold-tap"' if label in hold_children else '"zmk,behavior-macro-one-param"' if label in {"osl", "osm", "lkp", "losm"} else '"zmk,behavior-mod-morph"'
            self.check("behavior_schema:" + label, compatible == [expected_compat]
                       and props.get("#binding-cells") == ["<", str(CUSTOM_CELLS.get(label, -1)), ">"], "Audited compatible and number of binding cells")
            allowed = {"compatible", "#binding-cells", "bindings"}
            allowed |= {"tapping-term-ms", "quick-tap-ms", "flavor", "hold-while-undecided"} if label in hold_children else {"tap-ms", "wait-ms"} if label in {"osl", "osm", "lkp", "losm"} else {"mods", "keep-mods"}
            if set(props) - allowed:
                raise ValueError("Unsupported behavior properties at " + label + ": " + str(set(props) - allowed))
            if label in hold_children:
                child_groups = groups(props["bindings"])
                children = tuple(g[0][1:] for g in child_groups if len(g) == 1 and g[0].startswith("&"))
                self.check("hold_children:" + label, len(child_groups) == 2 and children == hold_children[label], "Two child phandles, with parameters supplied by the hold-tap")
                timing = "HOLD_PREFERRED_MS" if label == "sc" else "TAP_PREFERRED_MS"
                self.check("timing_source:" + label, props.get("tapping-term-ms") == ["<", timing, ">"], "Decision threshold comes directly from " + timing)
                self.check("flavor:" + label, props.get("flavor") == ['"hold-preferred"' if label == "sc" else '"tap-preferred"'], "Explicit reference flavor")
                self.check("quick_tap_source:" + label, props.get("quick-tap-ms") == ["<", "QUICK_TAP_MS", ">"] if label in {"hrm", "sc", "ltp"} else "quick-tap-ms" not in props, "Quick-tap only on the three reference typing/layer-tap behaviors")
                self.check("undecided_hold:" + label, ("hold-while-undecided" in props and props["hold-while-undecided"] == []) == (label == "bsk"), "Immediate undecided hold only on sticky modifier")
            else:
                parsed = bindings(props["bindings"], self.definitions, self.cells, placeholders=True)
                self.check("behavior_bindings:" + label, bool(parsed), "All internal behavior references, arities and parameter domains checked")
                if label in {"osl", "osm", "lkp", "losm"}:
                    self.check("zero_macro_delays:" + label, props.get("tap-ms") == ["<", "0", ">"] and props.get("wait-ms") == ["<", "0", ">"], "Explicit zero macro tap/wait delay")
                else:
                    self.check("morph_branches:" + label, len(parsed) == 2, "Exactly two mod-morph branches")
                    for name in ("mods", "keep-mods"):
                        if name in props:
                            value = groups(props[name])
                            if len(value) != 1 or not value[0] or any(t not in MASKS | {"(", ")", "|"} for t in value[0]):
                                raise ValueError("Unsupported modifier mask at " + label)
        macro_expected = {
            "osl": "<&macro_param_1to1>, <&macro_tap &sl MACRO_PLACEHOLDER>",
            "osm": "<&macro_param_1to1>, <&macro_tap &sk MACRO_PLACEHOLDER>",
            "lkp": "<&macro_tap &to BASE>, <&macro_param_1to1>, <&macro_press &kp MACRO_PLACEHOLDER>, <&macro_pause_for_release>, <&macro_param_1to1>, <&macro_release &kp MACRO_PLACEHOLDER>",
            "losm": "<&macro_tap &to BASE>, <&macro_param_1to1>, <&macro_tap &sk MACRO_PLACEHOLDER>",
        }
        for label, expected in macro_expected.items():
            self.check("macro_protocol:" + label, self.behaviors[label].props["bindings"] == tokens(expected), "Forward macro parameter, preserve press/pause/release protocol and return to Base where required")
        morph_expected = {
            "sym": ("<&sym_shift>, <&bsl SYMBOLS SYMBOLS>", "<(MOD_LCTL | MOD_RCTL | MOD_LGUI | MOD_RGUI | MOD_LALT)>", "<(MOD_LCTL | MOD_RCTL | MOD_LGUI | MOD_RGUI | MOD_LALT)>"),
            "sym_shift": ("<&bsl SYMBOLS SYMBOLS>, <&bsk LS(RALT) LS(RALT)>", "<(MOD_LSFT | MOD_RSFT)>", "<(MOD_LSFT | MOD_RSFT)>"),
            "vim_prev": ("<&kp LA(LEFT)>, <&kp LS(GRAVE)>", "<(MOD_LALT | MOD_LGUI)>", "<(MOD_LALT | MOD_LGUI)>"),
            "vim_next": ("<&kp LA(RIGHT)>, <&kp GRAVE>", "<(MOD_LALT | MOD_LGUI)>", "<(MOD_LALT | MOD_LGUI)>"),
            "bt_sel1_clr": ("<&bt BT_SEL 1>, <&bt BT_CLR>", "<MOD_LSFT>", None),
        }
        for label, (branches, mask, keep) in morph_expected.items():
            props = self.behaviors[label].props
            self.check("morph_protocol:" + label, props["bindings"] == tokens(branches) and props.get("mods") == tokens(mask)
                       and props.get("keep-mods") == (tokens(keep) if keep else None), "Reference branches and modifier masking, including Shift-only AltGr and guarded Bluetooth clear")
        for label, flag in (("&sk", "quick-release"), ("&sl", "ignore-modifiers")):
            node = next(node for node in roots if node.name == label)
            self.check("sticky_override:" + label, node.props == {"release-after-ms": ["<", "STICKY_TIMEOUT_MS", ">"], flag: []}, "Minimal reference override plus independent one-shot timeout; other defaults come from pinned ZMK")
        timing_defs = {k: v for k, v in self.parts["config/timing.h"][1].items() if k not in GUARDS}
        self.check("independent_timing_defaults", set(timing_defs) == TIMINGS and all(re.fullmatch(r'\d+', v) for v in timing_defs.values()), "Four independent decimal object defines; no coupling aliases")
        if set(timing_defs) != TIMINGS or not all(re.fullmatch(r'\d+', v) for v in timing_defs.values()):
            raise ValueError("Malformed timing defaults")
        timings = {name: int(value) for name, value in timing_defs.items()}
        self.check("timing_ranges", all(timings[n] > 0 for n in TIMINGS - {"QUICK_TAP_MS"}) and timings["QUICK_TAP_MS"] >= 0, "Decision/sticky defaults positive; quick-tap non-negative")
        self.observed["timing_defaults_ms"] = timings

    def hardware_and_scroll(self) -> None:
        current = uncomment(self.read("boards/shields/toucan/toucan.dtsi"))
        original = uncomment(self.read("reference/baseline/toucan.dtsi"))
        include = '#include "../../../config/layers.h"'
        self.check("scroll_layer_header_once", current.count(include) == 1, "Hardware source includes the shared layer indices once")
        self.check("scroll_vimnav_only", re.findall(r'\blayers\s*=\s*<(.*?)>\s*;', current, re.S) == ["VIM_NAV"], "Touchpad scroll override is restricted to VimNav")
        reverted = current.replace(include, "")
        reverted = re.sub(r'\blayers\s*=\s*<VIM_NAV>\s*;', 'layers = <1 2>;', reverted)
        self.check("hardware_only_scroll_change", re.sub(r'\s+', '', reverted) == re.sub(r'\s+', '', original), "Apart from comments/whitespace, only layer-header include and scroll-layer property differ from official DTSI")
        physical = len(re.findall(r'&key_physical_attrs\b', property_body(current, "keys")))
        mapping = [(int(a), int(b)) for a, b in re.findall(r'RC\(\s*(\d+)\s*,\s*(\d+)\s*\)', property_body(current, "map"))]
        expected = [(r, c) for r in range(3) for c in range(12)] + [(3, c) for c in range(3, 9)]
        self.check("physical_and_matrix_42", physical == 42 and mapping == expected, "Official physical order and six thumb indices retained")
        self.observed["trackpad_scroll_layer"] = "VIM_NAV (2)"

    def build_matrix_port(self) -> None:
        rows = yaml_named_blocks(yaml_section(self.read("build.yaml"), "include", 0), "board", 2)
        expected = {
            "toucan_left rgbled_adapter nice_view_gem": "toucan-v1-selenium-left",
            "toucan_right rgbled_adapter": "toucan-v1-selenium-right",
            "settings_reset": "toucan-v1-settings-reset",
        }
        seen = {}
        for board, block in rows:
            shield = yaml_field(block, "shield", 4)
            if shield in seen:
                raise ValueError("Duplicate build target")
            seen[shield] = block
            self.check("build_board:" + str(shield), board == "seeeduino_xiao_ble", "Official XIAO BLE controller")
            self.check("build_name:" + str(shield), yaml_field(block, "artifact-name", 4) == expected.get(shield), "Distinct firmware artifact name")
            self.check("no_studio_snippet:" + str(shield), yaml_field(block, "snippet", 4) is None, "No Studio USB snippet")
        self.check("build_three_official_targets", len(rows) == 3 and set(seen) == set(expected), "Left, right and separately named reset only")
        for side, shield in (("left", "toucan_left rgbled_adapter nice_view_gem"), ("right", "toucan_right rgbled_adapter")):
            self.check("studio_disabled:" + side, yaml_field(seen[shield], "cmake-args", 4) == "-DCONFIG_ZMK_STUDIO=n", "Studio explicitly disabled at build selection")
            config = active_config(self.read("config/toucan_" + side + ".conf"))
            self.check("no_studio_config_override:" + side, config.get("CONFIG_ZMK_STUDIO") != "y", "No contradictory per-half Studio setting")
        self.check("reset_no_extra_args", yaml_field(seen["settings_reset"], "cmake-args", 4) is None, "Reset remains a dedicated plain settings-reset build")
        self.observed["build_target_count"] = len(rows)

    def report(self) -> dict:
        report = super().report()
        report["scope"] = "toucan-selenium-stage-3-controlled-static-source-checks"
        report["limits"] += [
            "The DTS linter only accepts the controlled local syntax and object aliases; it is not a C preprocessor or devicetree compiler.",
            "Keycodes are symbolic names from an audited v0.3 subset; HID values, modifiers and generated overlays are not compiled/evaluated.",
            "Checked timings are source defaults; external C defines and runtime/sticky/hold-tap event scheduling were not simulated.",
            "No physical keypress, host character, Bluetooth, display or touchpad test was performed.",
        ]
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    audit = PortAudit(args.root)
    audit.check("project_directory", audit.root.is_dir(), "Project root exists")
    for name, operation in (
        ("provenance_archives", audit.provenance_archives), ("symlinks", audit.no_symlinks),
        ("side_configs", audit.side_configs), ("hardware_roles", audit.hardware_roles),
        ("dependency_lock", audit.dependency_lock), ("prepare", audit.prepare),
        ("includes_aliases", audit.includes_and_aliases), ("keymap", audit.keymap),
        ("behaviors_timing", audit.behaviors_and_timing),
        ("hardware_scroll", audit.hardware_and_scroll), ("build_matrix", audit.build_matrix_port),
    ):
        audit.run(name, operation)
    report = audit.report()
    encoded = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 1 if report["summary"]["failed"] else 2 if report["pending"] else 0


if __name__ == "__main__":
    sys.exit(main())
