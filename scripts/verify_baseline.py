#!/usr/bin/env python3
"""Check this project's official Toucan baseline, using Python's stdlib only.

After copying to scripts/verify_baseline.py, run from any directory:
    python scripts/verify_baseline.py --report reports/baseline-check.json

During preparation:
    python work/check_baseline.py --root outputs/toucan-v1-selenium-hrm

This checks source files and the controlled project manifest format. It does
not compile firmware, resolve west imports or certify physical operation.
The small YAML readers below intentionally accept only the block-list format
written by this project; they are not general-purpose YAML parsers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys


UPSTREAM_COMMIT = "7154e0187128e493cd15785a18af1546419d5bb1"
PROJECT_NAMES = {
    "zmk", "zephyr", "cirque-input-module", "zmk-rgbled-widget",
    "nanopb", "zmk-studio-messages",
}
ZEPHYR_BLOCKLIST = [
    "ci-tools", "hal_altera", "hal_cypress", "hal_infineon", "hal_microchip",
    "hal_nxp", "hal_openisa", "hal_silabs", "hal_xtensa", "hal_st", "hal_ti",
    "loramac-node", "mcuboot", "mcumgr", "net-tools", "openthread", "edtt",
    "trusted-firmware-m",
]
HEX40 = re.compile(r"[0-9a-fA-F]{40}\Z")
HEX64 = re.compile(r"[0-9a-fA-F]{64}\Z")


def strip_c_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)


def yaml_scalar(value: str) -> str:
    """Read the project's unescaped scalar values, never arbitrary YAML."""
    value = re.sub(r"\s+#.*$", "", value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def yaml_section(text: str, name: str, indent: int = 2) -> str:
    lines = text.splitlines()
    marker = " " * indent + name + ":"
    for index, line in enumerate(lines):
        if line.strip() and line.split("#", 1)[0].rstrip() == marker:
            selected = []
            for following in lines[index + 1:]:
                if following.strip() and not following.lstrip().startswith("#"):
                    spaces = len(following) - len(following.lstrip(" "))
                    if spaces <= indent:
                        break
                selected.append(following)
            return "\n".join(selected)
    raise ValueError("Missing controlled YAML section: " + name)


def yaml_named_blocks(section: str, field: str, indent: int) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?m)^" + " " * indent + r"- " + field + r":[ \t]*(.*?)[ \t]*$")
    matches = list(pattern.finditer(section))
    if not matches:
        raise ValueError("Expected block list entries '- " + field + ":'")
    return [
        (yaml_scalar(match.group(1)), section[match.end():matches[i + 1].start()
                                             if i + 1 < len(matches) else len(section)])
        for i, match in enumerate(matches)
    ]


def yaml_field(block: str, name: str, indent: int = 6) -> str | None:
    matches = re.findall(r"(?m)^" + " " * indent + re.escape(name) + r":[ \t]*(.*?)[ \t]*$", block)
    if len(matches) > 1:
        raise ValueError("Duplicate controlled YAML field: " + name)
    return yaml_scalar(matches[0]) if matches else None


def parse_west(text: str) -> tuple[dict[str, dict[str, str | None]], dict[str, str]]:
    remotes = {}
    if re.search(r"(?m)^  remotes:[ \t]*$", text):
        for name, block in yaml_named_blocks(yaml_section(text, "remotes"), "name", 4):
            if name in remotes:
                raise ValueError("Duplicate west remote: " + name)
            remotes[name] = yaml_field(block, "url-base") or ""
    projects = {}
    for name, block in yaml_named_blocks(yaml_section(text, "projects"), "name", 4):
        if name in projects:
            raise ValueError("Duplicate west project: " + name)
        projects[name] = {field: yaml_field(block, field) for field in
                          ("revision", "remote", "url", "path", "repo-path", "import", "clone-depth")}
        projects[name]["block"] = block
    return projects, remotes


def property_body(text: str, name: str) -> str:
    match = re.search(r"\b" + re.escape(name) + r"\s*=\s*<(?P<body>.*?)>;", text, re.S)
    if not match:
        raise ValueError("Missing devicetree property: " + name)
    return match.group("body")


def node_body(text: str, label: str) -> str:
    label_pattern = re.escape(label)
    match = re.search(r"(?:&" + label_pattern + r"\b|\b" + label_pattern
                      + r":\s*[\w,@-]+)\s*\{(.*?)\};", text, re.S)
    if not match:
        raise ValueError("Missing devicetree reference node: " + label)
    return match.group(1)


def active_config(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        match = re.fullmatch(r"\s*(CONFIG_[A-Z0-9_]+)=(.*?)\s*", line)
        if match:
            name, value = match.groups()
            if name in values and values[name] != value:
                raise ValueError("Conflicting Kconfig values for " + name)
            values[name] = value
    return values


class Audit:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.checks: list[dict] = []
        self.warnings: list[str] = []
        self.pending: list[str] = []
        self.observed: dict = {}

    def check(self, name: str, passed: bool, detail: str) -> None:
        self.checks.append({"id": name, "passed": bool(passed), "detail": detail})

    def path(self, relative: str) -> Path:
        posix = PurePosixPath(relative)
        if posix.is_absolute() or ".." in posix.parts or "\\" in relative or ":" in relative:
            raise ValueError("Unsafe project-relative path: " + relative)
        candidate = self.root.joinpath(*posix.parts)
        candidate.resolve().relative_to(self.root)
        return candidate

    def read(self, relative: str) -> str:
        return self.path(relative).read_text(encoding="utf-8-sig")

    def run(self, name: str, operation) -> None:
        try:
            operation()
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self.check(name, False, str(exc))

    def provenance(self) -> None:
        record = json.loads(self.read("provenance/upstream.json"))
        self.check("upstream_identity", record.get("schema_version") == 1
                   and record.get("stage") == "official-baseline"
                   and record.get("upstream", {}).get("commit") == UPSTREAM_COMMIT,
                   "Expected audited Beekeeb commit " + UPSTREAM_COMMIT)
        files = record["upstream_files"]
        self.check("upstream_file_count", len(files) == 47,
                   "Expected 47 unchanged upstream regular files; found " + str(len(files)))
        seen_local, seen_upstream = set(), set()
        for entry in files:
            relative = entry["local_path"]
            duplicate = relative in seen_local or entry["upstream_path"] in seen_upstream
            seen_local.add(relative)
            seen_upstream.add(entry["upstream_path"])
            self.check("provenance_unique:" + relative, not duplicate, "Unique source and destination")
            payload = self.path(relative).read_bytes()
            sha = hashlib.sha256(payload).hexdigest()
            blob = hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
            self.check("upstream_bytes:" + relative,
                       entry.get("mode") == "100644"
                       and bool(HEX64.fullmatch(entry["sha256"]))
                       and sha == entry["sha256"].lower()
                       and bool(HEX40.fullmatch(entry["git_blob"]))
                       and blob == entry["git_blob"].lower(),
                       "Compare SHA-256 and Git blob ID to local provenance")
        normalised = record["normalised_files"]
        expected = {"config/toucan_left.conf", "config/toucan_right.conf"}
        self.check("normalised_config_entries", len(normalised) == 2
                   and {item["local_path"] for item in normalised} == expected,
                   "Exactly the two per-half user configurations")
        for entry in normalised:
            payload = self.path(entry["local_path"]).read_bytes()
            source = self.path(entry["source_path"]).read_bytes()
            self.check("normalised_bytes:" + entry["local_path"], payload == source
                       and hashlib.sha256(payload).hexdigest() == entry["sha256"].lower(),
                       "Real file equals the corresponding upstream shield configuration")
        self.observed["upstream_commit"] = UPSTREAM_COMMIT
        self.observed["upstream_regular_files"] = len(files)

    def no_symlinks(self) -> None:
        links = []
        for directory, folders, files in os.walk(self.root, followlinks=False):
            folders[:] = [folder for folder in folders if folder != ".git"]
            for name in folders + files:
                path = Path(directory) / name
                info = path.lstat()
                reparse = bool(getattr(info, "st_file_attributes", 0)
                               & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
                if path.is_symlink() or reparse:
                    links.append(path.relative_to(self.root).as_posix())
            folders[:] = [folder for folder in folders
                          if not (Path(directory) / folder).is_symlink()
                          and not getattr((Path(directory) / folder), "is_junction", lambda: False)()]
        self.check("no_source_symlinks", not links,
                   "No symlinks/junctions outside .git" if not links else ", ".join(links))
        self.check("no_root_config_aliases",
                   not self.path("toucan_left.conf").exists() and not self.path("toucan_right.conf").exists(),
                   "Redundant root-level upstream config aliases are absent")

    def matrix_and_keymap(self) -> None:
        dtsi = strip_c_comments(self.read("boards/shields/toucan/toucan.dtsi"))
        attributes = property_body(dtsi, "keys")
        mapping = [(int(row), int(column)) for row, column in re.findall(
            r"RC\(\s*(\d+)\s*,\s*(\d+)\s*\)", property_body(dtsi, "map"))]
        count = len(re.findall(r"&key_physical_attrs\b", attributes))
        expected = [(row, column) for row in range(3) for column in range(12)]
        expected += [(3, column) for column in range(3, 9)]
        self.check("physical_positions_42", count == 42, "Found " + str(count) + " physical attributes")
        self.check("matrix_42_unique", len(mapping) == 42 and len(set(mapping)) == 42,
                   "Found " + str(len(mapping)) + " RC entries / " + str(len(set(mapping))) + " unique")
        self.check("matrix_order_and_thumb_indices", mapping == expected,
                   "Three 12-key rows; indices 36..41 map to RC(3,3)..RC(3,8)")
        self.check("matrix_dimensions", re.search(r"\bcolumns\s*=\s*<12>", dtsi) is not None
                   and re.search(r"\brows\s*=\s*<4>", dtsi) is not None,
                   "Electrical matrix is 4 by 12")
        keymap = self.read("config/toucan.keymap")
        self.check("keymap_duplicate_matches", keymap == self.read("boards/shields/toucan/toucan.keymap"),
                   "User and upstream shield keymaps remain identical for this baseline")
        plain = strip_c_comments(keymap)
        layers = re.findall(r"\bbindings\s*=\s*<(.*?)>;", plain, re.S)
        sizes = [len(re.findall(r"&[A-Za-z_]\w*", layer)) for layer in layers]
        self.check("official_layer_sizes", sizes == [42, 42, 42, 42],
                   "Four official populated layers, each with 42 binding references: " + str(sizes))
        base = re.search(r"\bbase\s*\{.*?\bbindings\s*=\s*<(.*?)>;", plain, re.S)
        bindings = [" ".join(value.split()) for value in re.findall(r"&\w+[^&]*", base.group(1))] if base else []
        letters = ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"]
        self.check("baseline_qwerty_42_active", len(bindings) == 42
                   and bindings[1:11] == ["&kp " + letter for letter in letters]
                   and not re.search(r"&(?:none|trans)\b", base.group(1) if base else "&none"),
                   "Official 42-key QWERTY base; no Selenium or six reserved keys yet")
        for pattern, explanation in ((r"&mo\s+TAB\b", "Official ADJ contains &mo TAB (keycode used as layer index)."),
                                     (r"&bt\s+LSHFT\b", "Official ADJ contains &bt LSHFT (keycode used as Bluetooth command).")):
            if re.search(pattern, plain):
                self.warnings.append(explanation + " Preserved in this reference; not a build-failure claim.")
        self.observed["matrix_positions"] = len(mapping)
        self.observed["physical_positions"] = count
        self.observed["populated_keymap_layers"] = len(layers)

    def side_configs(self) -> None:
        expected = {"CONFIG_ZMK_POINTING": "y", "CONFIG_ZMK_MOUSE": "y",
                    "CONFIG_ZMK_BATTERY_REPORTING": "y", "CONFIG_ZMK_SLEEP": "y",
                    "CONFIG_ZMK_IDLE_SLEEP_TIMEOUT": "3600000", "CONFIG_ZMK_IDLE_TIMEOUT": "30000",
                    "CONFIG_ZMK_PM_SOFT_OFF": "y", "CONFIG_INPUT_THREAD_STACK_SIZE": "2048"}
        for side in ("left", "right"):
            user_file = "config/toucan_" + side + ".conf"
            shield_file = "boards/shields/toucan/toucan_" + side + ".conf"
            self.check("side_config_matches:" + side,
                       self.path(user_file).read_bytes() == self.path(shield_file).read_bytes(),
                       "User per-half config is a real copy of the correct shield config")
            values = active_config(self.read(user_file))
            for name, value in expected.items():
                self.check("side_config:" + side + ":" + name, values.get(name) == value,
                           name + "=" + value + " in source (generated .config not checked)")
            if side == "left":
                for name in ("CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING",
                             "CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY"):
                    self.check("side_config:left:" + name, values.get(name) == "y", name + "=y")

    def hardware_roles(self) -> None:
        left = strip_c_comments(self.read("boards/shields/toucan/toucan_left.overlay"))
        right = strip_c_comments(self.read("boards/shields/toucan/toucan_right.overlay"))
        common = strip_c_comments(self.read("boards/shields/toucan/toucan.dtsi"))
        kconfig = self.read("boards/shields/toucan/Kconfig.defconfig")
        central = re.search(r"(?ms)^if SHIELD_TOUCAN_LEFT\s+(.*?)^endif", kconfig)
        self.check("left_is_central_source", central is not None and re.search(
            r"config ZMK_SPLIT_ROLE_CENTRAL\s+default y\b", central.group(1)) is not None,
                   "Central role defaults to y inside the left-only shield condition")
        self.check("right_offset_6", re.search(r"\bcol-offset\s*=\s*<6>", node_body(right, "default_transform")) is not None,
                   "Right half retains column offset 6")
        self.check("pointing_split_route", 'compatible = "zmk,input-split"' in common
                   and re.search(r"device\s*=\s*<&glidepoint_split>", node_body(common, "glidepoint_listener")) is not None
                   and re.search(r'device\s*=\s*<&glidepoint>', node_body(right, "glidepoint_split")) is not None
                   and re.search(r'status\s*=\s*"okay"', node_body(left, "glidepoint_listener")) is not None,
                   "Cirque input originates on right and is consumed by central left listener")
        self.check("right_cirque_source", 'compatible = "cirque,pinnacle"' in right
                   and 'sensitivity = "2x"' in right and "x-invert;" in right
                   and re.search(r"dr-gpios\s*=\s*<&gpio0\s+2\b", right) is not None,
                   "Right source retains Cirque identity, DR pin, sensitivity and inversion")
        self.check("display_on_left_source", "nice_view_spi: &spi0" in left
                   and "nice_view_spi" not in right
                   and 'compatible = "sharp,ls0xx"' in self.read("boards/shields/nice_view_gem/nice_view_gem.overlay")
                   and active_config(self.read("boards/shields/nice_view_gem/nice_view_gem.conf")).get("CONFIG_ZMK_DISPLAY") == "y",
                   "Left provides display SPI and nice_view_gem enables the Sharp display")

    def build_matrix(self) -> None:
        matrix = self.read("build.yaml")
        rows = yaml_named_blocks(yaml_section(matrix, "include", 0), "board", 2)
        self.check("build_matrix_three_targets", len(rows) == 3, "Left, right and separate settings_reset")
        seen = {}
        for board, block in rows:
            shield = yaml_field(block, "shield", 4)
            if shield in seen:
                raise ValueError("Duplicate build shield target: " + str(shield))
            seen[shield] = block
            self.check("build_board:" + str(shield), board == "seeeduino_xiao_ble", "Official XIAO BLE board")
        expected = {"toucan_left rgbled_adapter nice_view_gem", "toucan_right rgbled_adapter", "settings_reset"}
        self.check("build_matrix_shields", set(seen) == expected, "Official shield combinations only")
        expected_artifacts = {
            "toucan_left rgbled_adapter nice_view_gem": "toucan-v1-reference-left",
            "toucan_right rgbled_adapter": "toucan-v1-reference-right",
            "settings_reset": "toucan-v1-settings-reset",
        }
        artifacts = {shield: yaml_field(block, "artifact-name", 4) for shield, block in seen.items()}
        self.check("build_artifacts_distinct_and_labelled", artifacts == expected_artifacts,
                   "Three distinct reference-left, reference-right and settings-reset artifact names")
        left = seen.get("toucan_left rgbled_adapter nice_view_gem", "")
        self.check("baseline_studio_left", yaml_field(left, "snippet", 4) == "studio-rpc-usb-uart"
                   and "-DCONFIG_ZMK_STUDIO=y" in (yaml_field(left, "cmake-args", 4) or ""),
                   "Official left baseline keeps Studio and its USB snippet")
        for shield in ("toucan_right rgbled_adapter", "settings_reset"):
            self.check("no_studio:" + shield, "studio" not in seen.get(shield, "").lower(),
                       "No Studio snippet/options on this target")
        self.observed["build_target_count"] = len(rows)

    def dependency_lock(self) -> None:
        filenames = ("config/west.yml", "provenance/dependencies.json")
        absent = [name for name in filenames if not self.path(name).is_file()]
        if absent:
            self.pending.append("Dependency lock not assessed; missing " + ", ".join(absent))
            self.observed["dependency_lock"] = "pending"
            return
        manifest = self.read(filenames[0])
        projects, remotes = parse_west(manifest)
        self.check("manifest_self_path", yaml_field(yaml_section(manifest, "self"), "path", 4) == "config",
                   "West self checkout remains config")
        lock = json.loads(self.read(filenames[1]))
        self.check("dependency_schema", lock.get("schema_version") == 1, "Dependency provenance schema 1")
        records = lock["projects"]
        locked = {entry["name"]: entry for entry in records}
        self.check("dependency_project_set", len(records) == 6 and len(locked) == 6
                   and set(locked) == PROJECT_NAMES and set(projects) == PROJECT_NAMES,
                   "Exactly zmk, zephyr, Cirque, rgbled, nanopb and Studio messages; no implicit direct revisions")
        for name in sorted(PROJECT_NAMES):
            source, record = projects.get(name, {}), locked.get(name, {})
            revision = source.get("revision") or ""
            recorded = record.get("revision") or ""
            self.check("dependency_pin:" + name, bool(HEX40.fullmatch(revision))
                       and bool(HEX40.fullmatch(recorded)) and revision.lower() == recorded.lower(),
                       "Manifest and provenance agree on a complete 40-digit Git revision")
            self.check("no_clone_depth:" + name, source.get("clone-depth") is None,
                       "No clone-depth on exact SHA revisions")
            path = source.get("path") or name
            self.check("dependency_path:" + name, path == record.get("path"), "Manifest checkout path agrees with provenance")
            url = source.get("url")
            if not url and source.get("remote") in remotes:
                url = remotes[source["remote"]].rstrip("/") + "/" + (source.get("repo-path") or name)
            def canonical(value):
                return (value or "").rstrip("/").removesuffix(".git")
            self.check("dependency_url:" + name, bool(url) and canonical(url) == canonical(record.get("url")),
                       "Manifest remote/repository agrees with provenance URL")
        self.check("zmk_import_retained", projects.get("zmk", {}).get("import") == "app/west.yml",
                   "Retain the pinned ZMK upstream manifest import")
        block = projects.get("zephyr", {}).get("block") or ""
        match = re.search(r"(?m)^        name-blocklist:\s*$", block)
        blocklist = []
        if match:
            for line in block[match.end():].splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                item = re.fullmatch(r"          -\s+(.+?)\s*", line)
                if not item:
                    break
                blocklist.append(yaml_scalar(item.group(1)))
        expected_blocklist = lock.get("west_policy", {}).get("zephyr_name_blocklist")
        self.check("zephyr_import_blocklist", projects.get("zephyr", {}).get("import") == ""
                   and blocklist == expected_blocklist == ZEPHYR_BLOCKLIST,
                   "Zephyr explicit import blocklist equals all 18 recorded upstream exclusions")
        environment = lock.get("build_environment", {})
        if environment.get("status") == "deferred-to-step-5":
            self.warnings.append("Build environment is explicitly deferred to step 5; source pins do not freeze image, SDK or Actions.")
        self.observed["dependency_lock"] = "six-direct-pins-checked-locally"
        self.observed["build_environment_status"] = environment.get("status", "not-recorded")

    def report(self) -> dict:
        failures = sum(not check["passed"] for check in self.checks)
        return {"schema_version": 1, "scope": "official-baseline-static-source-checks",
                "project_root": self.root.name,
                "status": "fail" if failures else "incomplete" if self.pending else "pass",
                "compilation_checked": False, "physical_tests_performed": False,
                "limits": ["No compiler, generated .config or generated devicetree was checked.",
                           "Hashes and pins are compared with local provenance; no remote repository was fetched.",
                           "The six direct pins and Zephyr policy are not a resolved transitive workspace or a pinned build environment."],
                "summary": {"checks": len(self.checks), "passed": len(self.checks) - failures,
                            "failed": failures, "warnings": len(self.warnings), "pending": len(self.pending)},
                "observed": self.observed, "checks": self.checks,
                "warnings": self.warnings, "pending": self.pending}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="project directory (default: parent of scripts/)")
    parser.add_argument("--report", type=Path, help="also write the JSON report to this path")
    args = parser.parse_args()
    audit = Audit(args.root)
    audit.check("project_directory", audit.root.is_dir(), "Project root exists")
    for name, operation in (("provenance", audit.provenance), ("symlinks", audit.no_symlinks),
                            ("matrix_and_keymap", audit.matrix_and_keymap), ("side_configs", audit.side_configs),
                            ("hardware_roles", audit.hardware_roles), ("build_matrix", audit.build_matrix),
                            ("dependency_lock", audit.dependency_lock)):
        audit.run(name, operation)
    report = audit.report()
    encoded = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    if args.report:
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(encoded, encoding="utf-8", newline="\n")
        except OSError as exc:
            print("Cannot write report: " + str(exc), file=sys.stderr)
            return 1
    print(encoded, end="")
    return 1 if report["summary"]["failed"] else 2 if report["pending"] else 0


if __name__ == "__main__":
    sys.exit(main())
