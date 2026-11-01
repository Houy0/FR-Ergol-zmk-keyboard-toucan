#!/usr/bin/env python3
"""Build three Toucan targets once, from a clean pinned container workspace.

No packages are installed and no compiler/workspace cache is restored. Run this
script independently in two CI jobs; ci_compare.py checks their actual UF2 bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


def load_targets(project: Path) -> list[dict]:
    # Reuse the project's deliberately restricted YAML format reader. The source
    # audit validates this matrix before any network download/build is attempted.
    sys.path.insert(0, str(project / "scripts"))
    from verify_baseline import yaml_field, yaml_named_blocks, yaml_section
    matrix = (project / "build.yaml").read_text(encoding="utf-8")
    names = {"toucan_left": "left", "toucan_right": "right", "settings_reset": "settings_reset"}
    targets = []
    for board, block in yaml_named_blocks(yaml_section(matrix, "include", 0), "board", 2):
        shield = yaml_field(block, "shield", 4) or ""
        name = names[shield.split()[0]]
        targets.append({"target": name, "board": board, "shield": shield,
                        "filename": (yaml_field(block, "artifact-name", 4) or "") + ".uf2",
                        "cmake_args": shlex.split(yaml_field(block, "cmake-args", 4) or "")})
    if len(targets) != 3 or {entry["target"] for entry in targets} != {"left", "right", "settings_reset"}:
        raise ValueError("Build matrix must contain exactly the three Toucan targets")
    return targets


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(command: list[str], *, cwd: Path, env: dict, log: Path, echo: bool = True) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    print("Running:", " ".join(command), flush=True)
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        assert process.stdout is not None
        for line in process.stdout:
            output.write(line)
            output.flush()
            if echo:
                print(line, end="", flush=True)
        return process.wait()


def capture(command: list[str], cwd: Path, env: dict) -> str:
    return subprocess.check_output(command, cwd=cwd, env=env, text=True, encoding="utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass-index", type=int, choices=(1, 2), required=True)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    output = (args.output or project / "artifacts" / ("pass-" + str(args.pass_index))).resolve()
    provenance, diagnostics, firmware = (output / name for name in ("provenance", "diagnostics", "firmware"))
    for directory in (provenance, diagnostics, firmware):
        directory.mkdir(parents=True, exist_ok=True)
    workspace, build_root = Path("/tmp/toucan-west"), Path("/tmp/toucan-build")
    summary = {"schema_version": 1, "clean_pass": args.pass_index, "status": "fail",
               "compilation_performed": False, "physical_tests_performed": False, "targets": []}
    env = os.environ.copy()
    env.update({"TZ": "UTC", "LC_ALL": "C", "LANG": "C", "CCACHE_DISABLE": "1",
                "ZEPHYR_TOOLCHAIN_VARIANT": "zephyr", "ZEPHYR_SDK_INSTALL_DIR": "/opt/zephyr-sdk-0.16.3"})
    try:
        declaration = json.loads((project / "provenance/build-environment.json").read_text(encoding="utf-8"))
        summary["container_image"] = declaration["image"]
        summary["source_commit"] = capture(["git", "rev-parse", "HEAD"], project, env)
        epoch = capture(["git", "show", "-s", "--format=%ct", "HEAD"], project, env)
        if not epoch.isdecimal():
            raise RuntimeError("Git source timestamp is not a decimal SOURCE_DATE_EPOCH")
        env["SOURCE_DATE_EPOCH"] = epoch
        summary["source_date_epoch"] = int(epoch)
        sdk = Path(env["ZEPHYR_SDK_INSTALL_DIR"])
        sdk_version = (sdk / "sdk_version").read_text(encoding="utf-8").strip()
        if sdk_version != "0.16.3":
            raise RuntimeError("SDK version differs from pinned image declaration: " + sdk_version)
        tools = {"sdk_version": sdk_version, "zephyr_requirements_version": env.get("ZEPHYR_VERSION"),
                 "source_date_epoch": int(epoch), "container_image": declaration["image"]}
        commands = {"python": [sys.executable, "--version"], "west": ["west", "--version"],
                    "cmake": ["cmake", "--version"], "ninja": ["ninja", "--version"],
                    "git": ["git", "--version"], "protoc": ["protoc", "--version"],
                    "arm_gcc": [str(sdk / "arm-zephyr-eabi/bin/arm-zephyr-eabi-gcc"), "--version"]}
        for name, command in commands.items():
            tools[name] = capture(command, project, env)
        tools["python_packages"] = sorted(
            [{"name": d.metadata.get("Name", ""), "version": d.version} for d in importlib.metadata.distributions()],
            key=lambda d: (d["name"].lower(), d["version"]))
        tools["os_release"] = Path("/etc/os-release").read_text(encoding="utf-8")
        save_json(provenance / "tools.json", tools)
        shutil.copy2(project / "provenance/build-environment.json", provenance / "build-environment.json")
        shutil.copy2(project / "provenance/dependencies.json", provenance / "declared-dependencies.json")
        source_audit = run([sys.executable, str(project / "scripts/verify_port.py"), "--root", str(project),
                            "--report", str(provenance / "source-verification.json")], cwd=project, env=env,
                           log=provenance / "source-verification.log", echo=False)
        if source_audit:
            raise RuntimeError("Source verification failed; inspect source-verification.json/log")
        targets = load_targets(project)
        # These directories are private to a fresh CI job. Refuse reuse rather
        # than deleting anything or accidentally retaining a previous CMake cache.
        if workspace.exists() or build_root.exists():
            raise RuntimeError("Clean workspace/build directory already exists; use a fresh CI job")
        workspace.mkdir()
        build_root.mkdir()
        shutil.copytree(project / "config", workspace / "config")
        for name, command in (
            ("west-init", ["west", "init", "-l", str(workspace / "config")]),
            ("west-update", ["west", "update", "--fetch-opt=--filter=tree:0"]),
            ("west-export", ["west", "zephyr-export"]),
        ):
            if run(command, cwd=workspace, env=env, log=provenance / (name + ".log")):
                raise RuntimeError(name + " failed; build prerequisites were not established")
        with (provenance / "west-frozen.yml").open("w", encoding="utf-8") as stream:
            subprocess.run(["west", "manifest", "--freeze"], cwd=workspace, env=env, stdout=stream, check=True)
        (provenance / "west-projects.txt").write_text(
            capture(["west", "list", "--format", "{name}\t{revision}\t{path}"], workspace, env) + "\n", encoding="utf-8")
        revisions = []
        lock = json.loads((project / "provenance/dependencies.json").read_text(encoding="utf-8"))
        for entry in lock["projects"]:
            actual = capture(["git", "rev-parse", "HEAD"], workspace / entry["path"], env)
            revisions.append({"name": entry["name"], "expected": entry["revision"], "actual": actual,
                              "matches": actual == entry["revision"]})
        save_json(provenance / "direct-source-revisions.json", revisions)
        if not all(entry["matches"] for entry in revisions):
            raise RuntimeError("Downloaded direct source revision differs from the declared pin")
        for entry in targets:
            target, shield, filename = entry["target"], entry["shield"], entry["filename"]
            print("Building target:", target, flush=True)
            directory, diagnostic = build_root / target, diagnostics / target
            diagnostic.mkdir(parents=True, exist_ok=True)
            command = ["west", "build", "-s", str(workspace / "zmk/app"), "-d", str(directory),
                       "-b", entry["board"], "--", "-DSHIELD=" + shield,
                       "-DZMK_CONFIG=" + str(workspace / "config"), "-DZMK_EXTRA_MODULES=" + str(project)]
            command.extend(entry["cmake_args"])
            save_json(diagnostic / "build-command.json", command)
            build_code = run(command, cwd=workspace, env=env, log=diagnostic / "build.log")
            summary["compilation_performed"] = True
            for relative in ("zephyr/.config", "zephyr/zephyr.dts", "zephyr/zephyr.dts.pre", "zephyr/zmk.map", "zephyr/zmk.elf", "CMakeCache.txt"):
                source = directory / relative
                if source.is_file():
                    destination = diagnostic / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
            verify_code = run([sys.executable, str(project / "scripts/verify_firmware.py"), "--target", target,
                               "--build-dir", str(directory), "--project-root", str(project),
                               "--report", str(diagnostic / "firmware-verification.json")],
                              cwd=project, env=env, log=diagnostic / "firmware-verification.log", echo=False)
            result = {"target": target, "build_exit_code": build_code, "verification_exit_code": verify_code,
                      "status": "pass" if build_code == verify_code == 0 else "fail"}
            if result["status"] == "pass":
                payload = (directory / "zephyr/zmk.uf2").read_bytes()
                (firmware / filename).write_bytes(payload)
                result.update({"filename": filename, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)})
            summary["targets"].append(result)
            # A failed target never prevents the other halves/reset from yielding
            # useful diagnostics; final job status still fails if any target did.
        if len(summary["targets"]) == 3 and all(item["status"] == "pass" for item in summary["targets"]):
            summary["status"] = "pass"
    except Exception as error:
        summary["fatal_error"] = str(error)
        print("Build setup/error:", str(error), file=sys.stderr, flush=True)
    finally:
        save_json(provenance / "build-summary.json", summary)
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
