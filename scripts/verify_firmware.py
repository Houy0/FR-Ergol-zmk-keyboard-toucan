#!/usr/bin/env python3
"""Verify generated Toucan build inputs and UF2 structure, not runtime behavior.

Run once per target after west build; build-dir must contain zephyr/.config,
zephyr/zephyr.dts and normally zephyr/zmk.uf2. Uses Python 3.10+ stdlib only.
The caller must additionally require that the build process itself succeeded.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import struct
import sys


OUTER = (0, 11, 12, 23, 24, 35)
LAYER_NAMES = ("Base", "Symbols", "VimNav", "NumRow", "FnMedia")
NRF52840_FAMILY = 0xADA52840


@dataclass(eq=False)
class Node:
    name: str
    labels: tuple[str, ...]
    parent: Node | None
    props: dict[str, list[str]] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)

    def strings(self, key: str) -> list[str]:
        return [json.loads(value) for value in self.props.get(key, []) if value.startswith('"')]

    def integer(self, key: str) -> int | None:
        values = cells(self.props.get(key, []))
        if not values:
            return None
        if len(values) != 1 or not isinstance(values[0], int):
            raise ValueError("Expected one integer in " + self.name + "/" + key)
        return values[0]

    def enabled(self) -> bool:
        node = self
        while node:
            state = node.strings("status")
            if state and state[0] not in ("okay", "ok"):
                return False
            node = node.parent
        return True


def cells(tokens: list[str]) -> list[int | str]:
    result = []
    for token in tokens:
        if token in ("<", ">", ","):
            continue
        if token.startswith("&"):
            result.append(token[1:])
        elif re.fullmatch(r"-?(?:0[xX][0-9a-fA-F]+|[0-9]+)", token):
            result.append(int(token, 16) if "x" in token.lower() else int(token, 10))
        else:
            raise ValueError("Unresolved/non-cell DTS token: " + token)
    return result


class DeviceTree:
    """Small reader for generated DTS: nodes, properties, labels and phandles.

    This is not a replacement for dtc/edtlib validation. It accepts flattened
    generated DTS with numeric cells or &label references, and fails on unknown
    cell expressions instead of guessing where a binding ends.
    """
    def __init__(self, text: str):
        lexical = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|[^\s{};=<>\[\]:,"]+|[{};=<>\[\]:,]', re.S)
        tokens = [match.group(0) for match in lexical.finditer(text)
                  if not match.group(0).startswith(("/*", "//"))]
        self.nodes: list[Node] = []
        stack, head = [], []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token == "{":
                labels, cursor = [], 0
                while cursor + 1 < len(head) and head[cursor + 1] == ":":
                    labels.append(head[cursor])
                    cursor += 2
                name = "".join(head[cursor:])
                if not name:
                    raise ValueError("Unnamed DTS node")
                node = Node(name, tuple(labels), stack[-1] if stack else None)
                if node.parent:
                    node.parent.children.append(node)
                self.nodes.append(node)
                stack.append(node)
                head = []
            elif token == "}":
                if not stack or head:
                    raise ValueError("Unbalanced DTS node or unterminated property")
                stack.pop()
            elif token == "=":
                if not stack or not head:
                    raise ValueError("DTS property outside a node")
                name = "".join(head)
                values = []
                index += 1
                while index < len(tokens) and tokens[index] != ";":
                    values.append(tokens[index])
                    index += 1
                if index == len(tokens):
                    raise ValueError("Unterminated DTS property " + name)
                if name in stack[-1].props:
                    raise ValueError("Duplicate generated DTS property " + name)
                stack[-1].props[name] = values
                head = []
            elif token == ";":
                if head and stack:
                    stack[-1].props["".join(head)] = []
                head = []
            else:
                head.append(token)
            index += 1
        if stack:
            raise ValueError("Unclosed generated DTS node")
        self.labels = {}
        self.phandles = {}
        for node in self.nodes:
            for label in node.labels:
                if label in self.labels:
                    raise ValueError("Duplicate DTS label " + label)
                self.labels[label] = node
            for key in ("phandle", "linux,phandle"):
                if key in node.props:
                    number = node.integer(key)
                    if number in self.phandles and self.phandles[number] is not node:
                        raise ValueError("Duplicate DTS phandle")
                    self.phandles[number] = node

    def compatible(self, name: str) -> list[Node]:
        return [node for node in self.nodes if name in node.strings("compatible")]

    def resolve(self, value: int | str) -> Node:
        lookup = self.phandles if isinstance(value, int) else self.labels
        if value not in lookup:
            raise ValueError("Unknown DTS phandle/label: " + str(value))
        return lookup[value]

    def one_ref(self, node: Node, property_name: str) -> Node:
        values = cells(node.props.get(property_name, []))
        if len(values) != 1:
            raise ValueError("Expected one reference in " + node.name + "/" + property_name)
        return self.resolve(values[0])

    def named(self, label: str, node_name: str | None = None) -> Node:
        if label in self.labels:
            return self.labels[label]
        selected = [node for node in self.nodes if node.name.split("@")[0] == (node_name or label)]
        if len(selected) != 1:
            raise ValueError("Cannot identify generated DTS node " + label)
        return selected[0]

    def bindings(self, node: Node, key: str = "bindings", *,
                 cell_property: str = "#binding-cells") -> list[tuple[Node, list[int | str]]]:
        values = cells(node.props.get(key, []))
        result, index = [], 0
        while index < len(values):
            behavior = self.resolve(values[index])
            count = behavior.integer(cell_property)
            if count is None or count < 0 or index + count >= len(values):
                raise ValueError("Missing " + cell_property + " arity or incomplete reference array in " + node.name)
            result.append((behavior, values[index + 1:index + count + 1]))
            index += count + 1
        return result


def read_config(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        unset = re.fullmatch(r"# (CONFIG_[A-Z0-9_]+) is not set", line)
        setting = re.fullmatch(r"(CONFIG_[A-Z0-9_]+)=(.*)", line)
        if unset:
            values[unset[1]] = "n"
        elif setting:
            value = setting[2]
            values[setting[1]] = json.loads(value) if value.startswith('"') else value
    return values


class Verification:
    def __init__(self, args):
        self.args = args
        self.checks: list[dict] = []
        self.warnings: list[str] = []
        self.observed: dict = {}

    def check(self, name: str, passed: bool, detail: str) -> None:
        self.checks.append({"id": name, "passed": bool(passed), "detail": detail})

    def run(self, name: str, operation) -> None:
        try:
            operation()
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            # Keep reports portable; file-system errors can contain user paths.
            detail = error.strerror or type(error).__name__ if isinstance(error, OSError) else str(error)
            self.check(name, False, detail)

    def config(self) -> None:
        path = self.args.build_dir / "zephyr/.config"
        payload = path.read_bytes()
        config = read_config(payload.decode("utf-8-sig"))
        self.observed["config_sha256"] = hashlib.sha256(payload).hexdigest()
        self.check("board", config.get("CONFIG_BOARD") == "seeeduino_xiao_ble",
                   "Compiled board is seeeduino_xiao_ble")
        self.check("studio_disabled", config.get("CONFIG_ZMK_STUDIO") != "y", "Studio is not enabled")
        if self.args.target == "settings_reset":
            self.check("settings_reset_enabled", config.get("CONFIG_ZMK_SETTINGS_RESET_ON_START") == "y",
                       "Recovery firmware erases settings on startup")
            self.check("settings_reset_shield", config.get("CONFIG_SHIELD_SETTINGS_RESET") == "y",
                       "settings_reset shield was selected")
            self.check("reset_is_not_toucan", all(config.get("CONFIG_SHIELD_TOUCAN_" + side) != "y"
                                                 for side in ("LEFT", "RIGHT")),
                       "Recovery target has neither Toucan half shield")
            return
        side = self.args.target.upper()
        other = "RIGHT" if side == "LEFT" else "LEFT"
        expected = {"CONFIG_ZMK_SPLIT": "y", "CONFIG_BT": "y", "CONFIG_ZMK_POINTING": "y",
                    "CONFIG_ZMK_MOUSE": "y", "CONFIG_INPUT_THREAD_STACK_SIZE": "2048",
                    "CONFIG_ZMK_SLEEP": "y", "CONFIG_ZMK_IDLE_TIMEOUT": "30000",
                    "CONFIG_ZMK_IDLE_SLEEP_TIMEOUT": "3600000", "CONFIG_ZMK_PM_SOFT_OFF": "y",
                    "CONFIG_ZMK_BATTERY_REPORTING": "y", "CONFIG_SHIELD_TOUCAN_" + side: "y"}
        for key, value in expected.items():
            self.check(key, config.get(key) == value, "Expected " + value + "; observed " + str(config.get(key)))
        self.check("other_shield_absent", config.get("CONFIG_SHIELD_TOUCAN_" + other) != "y",
                   "Opposite half shield is not selected")
        is_left = self.args.target == "left"
        self.check("central_role", (config.get("CONFIG_ZMK_SPLIT_ROLE_CENTRAL") == "y") == is_left,
                   "Left is central, right is peripheral")
        self.check("display_role", (config.get("CONFIG_ZMK_DISPLAY") == "y") == is_left,
                   "Display enabled only on left")
        if is_left:
            for key in ("CONFIG_ZMK_BLE", "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING",
                        "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY"):
                self.check(key, config.get(key) == "y", "Expected y; observed " + str(config.get(key)))
        self.observed["central"] = is_left

    def devicetree(self) -> None:
        path = self.args.build_dir / "zephyr/zephyr.dts"
        payload = path.read_bytes()
        tree = DeviceTree(payload.decode("utf-8-sig"))
        self.observed["devicetree_sha256"] = hashlib.sha256(payload).hexdigest()
        self.check("generated_dts_readable", bool(tree.nodes), "Generated DTS parsed without unresolved expressions")
        if self.args.target == "settings_reset":
            self.observed["keymap_checks"] = "not-applicable-to-recovery-firmware"
            return
        keymaps = tree.compatible("zmk,keymap")
        self.check("one_keymap", len(keymaps) == 1, "Exactly one compiled keymap")
        if len(keymaps) != 1:
            return
        layers = [node for node in keymaps[0].children if node.enabled() and "bindings" in node.props]
        names = [node.strings("display-name") for node in layers]
        self.check("five_layers", names == [[name] for name in LAYER_NAMES],
                   "Five populated layers in Base/Symbols/VimNav/NumRow/FnMedia priority order")
        for layer in layers:
            bindings = tree.bindings(layer)
            self.check("42_bindings:" + layer.name, len(bindings) == 42,
                       "Decoded " + str(len(bindings)) + " bindings using actual #binding-cells")
            self.check("outer_none:" + layer.name, len(bindings) == 42 and all(
                "zmk,behavior-none" in bindings[index][0].strings("compatible") for index in OUTER),
                "Six outer positions resolve to the None behavior, not Transparent")
        chosen = tree.named("chosen")
        layout = tree.one_ref(chosen, "zmk,physical-layout")
        self.check("physical_layout_selected", "zmk,physical-layout" in layout.strings("compatible"),
                   "Chosen physical layout resolves")
        # Physical attributes use #key-cells; behavior bindings use
        # #binding-cells. They are distinct DTS specifier spaces in ZMK.
        physical = tree.bindings(layout, "keys", cell_property="#key-cells")
        self.check("42_physical_positions", len(physical) == 42 and all(
            "zmk,key-physical-attrs" in node.strings("compatible") and len(arguments) == 7
            for node, arguments in physical), "42 physical attributes, each with seven coordinate/geometry arguments")
        transform = tree.one_ref(layout, "transform")
        mapping = cells(transform.props.get("map", []))
        expected_map = [(row << 8) | column for row in range(3) for column in range(12)]
        expected_map += [(3 << 8) | column for column in range(3, 9)]
        self.check("matrix_map_42", mapping == expected_map and len(set(mapping)) == 42,
                   "42 unique matrix positions; thumbs 36..41 retain row 3 columns 3..8")
        self.check("matrix_offset", (transform.integer("col-offset") or 0) == (0 if self.args.target == "left" else 6),
                   "Compiled column offset matches half")
        timing_text = (self.args.project_root / "config/timing.h").read_text(encoding="utf-8-sig")
        timing = {name: int(value) for name, value in re.findall(
            r"(?m)^#define\s+(TAP_PREFERRED_MS|HOLD_PREFERRED_MS|QUICK_TAP_MS|STICKY_TIMEOUT_MS)\s+(\d+)\s*$", timing_text)}
        if len(timing) != 4:
            raise ValueError("Cannot read the four controlled timing constants from config/timing.h")
        for label, node_name, threshold, flavor in (
            ("hrm", "toucan_homerow_mods", "TAP_PREFERRED_MS", "tap-preferred"),
            ("sc", "toucan_hold_preferred_layer_tap", "HOLD_PREFERRED_MS", "hold-preferred"),
            ("ltp", "toucan_tap_preferred_layer_tap", "TAP_PREFERRED_MS", "tap-preferred"),
            ("bsl", "toucan_sticky_layer", "TAP_PREFERRED_MS", "tap-preferred"),
            ("bsk", "toucan_sticky_modifier", "TAP_PREFERRED_MS", "tap-preferred"),
            ("lbsk", "toucan_sticky_modifier_on_base", "TAP_PREFERRED_MS", "tap-preferred")):
            node = tree.named(label, node_name)
            self.check("timing:" + label, node.integer("tapping-term-ms") == timing[threshold]
                       and node.strings("flavor") == [flavor], "Compiled threshold and flavor match config/timing.h")
            if label in ("hrm", "sc", "ltp"):
                self.check("quick_tap:" + label, node.integer("quick-tap-ms") == timing["QUICK_TAP_MS"],
                           "Compiled quick-tap interval matches source")
        self.check("shift_immediate", "hold-while-undecided" in tree.named("bsk", "toucan_sticky_modifier").props,
                   "Sticky Shift's hold remains active while undecided")
        for label, name, flag in (("sk", "sticky_key", "quick-release"), ("sl", "sticky_layer", "ignore-modifiers")):
            node = tree.named(label, name)
            self.check("sticky:" + label, flag in node.props
                       and node.integer("release-after-ms") == timing["STICKY_TIMEOUT_MS"],
                       "Compiled sticky flag and expiration match source")
        listeners = tree.compatible("zmk,input-listener")
        listener = next((node for node in listeners if "glidepoint_listener" in node.labels
                         or node.name == "glidepoint_listener"), None)
        self.check("pointing_listener_role", listener is not None and listener.enabled() == (self.args.target == "left"),
                   "Toucan input listener enabled on central left only")
        if listener is not None:
            scrollers = [node for node in listener.children if node.name == "scroller"]
            self.check("scroll_vim_only", len(scrollers) == 1 and cells(scrollers[0].props.get("layers", [])) == [2],
                       "Only VimNav (index 2) activates touchpad scrolling")
        if self.args.target == "right":
            devices = tree.compatible("cirque,pinnacle")
            self.check("right_cirque", len(devices) == 1 and devices[0].enabled(), "Right Cirque SPI device is enabled")
        else:
            display = tree.one_ref(chosen, "zephyr,display")
            self.check("left_sharp_display", "sharp,ls0xx" in display.strings("compatible") and display.enabled(),
                       "Left chosen display resolves to enabled Sharp device")
        self.observed["keymap_layer_count"] = len(layers)
        self.observed["physical_position_count"] = len(physical)
        self.observed["compiled_timing_ms"] = timing

    def uf2(self) -> None:
        path = self.args.uf2 or self.args.build_dir / "zephyr/zmk.uf2"
        data = path.read_bytes()
        self.observed["uf2"] = {"filename": path.name, "bytes": len(data),
                                "sha256": hashlib.sha256(data).hexdigest()}
        self.check("uf2_block_size", len(data) > 0 and len(data) % 512 == 0,
                   "Nonempty UF2 consists of complete 512-byte blocks")
        if not data or len(data) % 512:
            return
        expected_count = len(data) // 512
        numbers, families, family_blocks = [], set(), 0
        valid_headers = True
        for offset in range(0, len(data), 512):
            first, second, flags, address, size, number, total, family = struct.unpack_from("<8I", data, offset)
            end = struct.unpack_from("<I", data, offset + 508)[0]
            valid_headers &= (first, second, end) == (0x0A324655, 0x9E5D5157, 0x0AB16F30)
            valid_headers &= 0 < size <= 476 and total == expected_count and number < total
            numbers.append(number)
            if flags & 0x2000:
                families.add(family)
                family_blocks += 1
        self.check("uf2_headers", valid_headers, "Magic values, payload lengths and declared block counts are valid")
        self.check("uf2_complete", set(numbers) == set(range(expected_count)) and len(set(numbers)) == expected_count,
                   "All block numbers occur exactly once")
        if families:
            self.check("uf2_family", families == {NRF52840_FAMILY} and family_blocks == expected_count,
                       "All UF2 blocks identify the nRF52840 family")
        else:
            self.warnings.append("UF2 has no family-ID flag; nRF52840 family cannot be confirmed from UF2 headers.")
        self.observed["uf2"]["blocks"] = expected_count
        self.observed["uf2"]["family_ids"] = [hex(value) for value in sorted(families)]

    def report(self) -> dict:
        failures = sum(not item["passed"] for item in self.checks)
        return {"schema_version": 1, "scope": "generated-build-artifacts", "target": self.args.target,
                "project": self.args.project_root.name, "status": "fail" if failures else "pass",
                "compilation_executed_by_this_script": False, "physical_tests_performed": False,
                "limits": ["Caller must require the build command to succeed; stale files alone are insufficient.",
                           "This inspects .config, generated DTS and UF2 structure, not firmware execution.",
                           "UF2 SHA-256 records bytes; build origin and reproducibility need separate evidence."],
                "summary": {"checks": len(self.checks), "failed": failures,
                            "passed": len(self.checks) - failures, "warnings": len(self.warnings)},
                "checks": self.checks, "warnings": self.warnings, "observed": self.observed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=("left", "right", "settings_reset"))
    parser.add_argument("--build-dir", required=True, type=Path)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--uf2", type=Path, help="UF2 path if not build-dir/zephyr/zmk.uf2")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    verification = Verification(args)
    for name in ("config", "devicetree", "uf2"):
        verification.run(name, getattr(verification, name))
    report = verification.report()
    text = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    if args.report:
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(text, encoding="utf-8")
        except OSError:
            print("Cannot write firmware verification report", file=sys.stderr)
            return 1
    print(text, end="")
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
