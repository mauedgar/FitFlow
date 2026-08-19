#!/usr/bin/env python3
"""
repo-packager — empaqueta contexto de repositorio via PageRank + Repomix.
Modos: reducido | ampliado | drill-down
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import Optional

try:
    import networkx as nx
except ImportError:
    print("ERROR: networkx no instalado. Ejecuta: pip install networkx", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

CACHE_DIR_NAME = ".repo-packager-cache"
MAX_AMPLIADO_PATHS = 10
CHARS_PER_TOKEN = 4  # rough estimate

IMPORT_PATTERNS = [
    # Python
    re.compile(r"^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))", re.MULTILINE),
    # JS/TS ESM + CJS
    re.compile(
        r"""(?:import\s+(?:[\w*{}\s,]+from\s+)?|require\s*\(\s*)['"]([^'"]+)['"]""",
        re.MULTILINE,
    ),
    # Go
    re.compile(r'^\s*import\s+(?:\(|")([\w./-]+)', re.MULTILINE),
    # Java / Kotlin-ish
    re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE),
    # Rust
    re.compile(r"^\s*(?:use|mod)\s+([\w:]+)", re.MULTILINE),
]


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def extract_imports(content: str) -> set[str]:
    imports: set[str] = set()
    for pat in IMPORT_PATTERNS:
        for m in pat.finditer(content):
            for g in m.groups():
                if g:
                    imports.add(g.strip())
                    break
    return imports


def resolve_to_file(imp: str, all_files: dict[str, str], current_file: str) -> Optional[str]:
    imp = imp.replace("\\", "/").lstrip("./")
    candidates = []
    for fpath in all_files:
        stem = Path(fpath).stem
        name = Path(fpath).name
        if (
            fpath == imp
            or fpath.startswith(imp + ".")
            or fpath.endswith("/" + imp)
            or fpath.endswith("/" + imp + ".py")
            or fpath.endswith("/" + imp + ".ts")
            or fpath.endswith("/" + imp + ".tsx")
            or fpath.endswith("/" + imp + ".js")
            or fpath.endswith("/" + imp + ".jsx")
            or fpath.endswith("/" + imp + ".go")
            or fpath.endswith("/" + imp + ".rs")
            or stem == Path(imp).stem
            or name == imp
        ):
            candidates.append(fpath)
    if not candidates:
        return None
    current_dir = str(Path(current_file).parent)
    candidates.sort(key=lambda c: (0 if c.startswith(current_dir) else 1, len(c)))
    return candidates[0]


def build_graph(files: dict[str, str]) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(files.keys())
    for src, content in files.items():
        for imp in extract_imports(content):
            dst = resolve_to_file(imp, files, src)
            if dst and dst != src:
                if G.has_edge(src, dst):
                    G[src][dst]["weight"] += 1
                else:
                    G.add_edge(src, dst, weight=1)
    return G


def compute_pagerank(
    G: nx.DiGraph,
    personalize: Optional[list[str]] = None,
    focus: Optional[str] = None,
) -> dict[str, float]:
    personalization = None
    if personalize or focus:
        personalization = {}
        boost_nodes = set(personalize or [])
        if focus:
            # boost everything under the focus path
            for n in G.nodes:
                if n.startswith(focus.rstrip("/") + "/") or n == focus:
                    boost_nodes.add(n)
        if boost_nodes:
            for n in boost_nodes:
                if n in G:
                    personalization[n] = 100.0
            residual = 1.0 / max(len(G) - len(personalization), 1)
            for n in G:
                if n not in personalization:
                    personalization[n] = residual
    return nx.pagerank(G, alpha=0.85, personalization=personalization, weight="weight")


def get_cache_paths(json_path: Path) -> tuple[Path, Path]:
    cache_dir = json_path.parent / CACHE_DIR_NAME
    cache_dir.mkdir(exist_ok=True)
    stem = json_path.stem
    return cache_dir / f"{stem}.graph.pkl", cache_dir / f"{stem}.rank.json"


def load_or_build_graph(json_path: Path, files: dict[str, str]) -> nx.DiGraph:
    import pickle

    graph_cache, _ = get_cache_paths(json_path)
    json_mtime = json_path.stat().st_mtime

    if graph_cache.exists():
        try:
            with open(graph_cache, "rb") as f:
                cached = pickle.load(f)
            if cached.get("mtime") == json_mtime and "graph" in cached:
                return cached["graph"]
        except Exception:
            pass

    G = build_graph(files)
    with open(graph_cache, "wb") as f:
        pickle.dump({"mtime": json_mtime, "graph": G}, f)
    return G


def reason_for_candidate(fpath: str, score: float, G: nx.DiGraph, selected: set[str]) -> str:
    in_degree = G.in_degree(fpath, weight="weight") if fpath in G else 0
    is_neighbor = any(G.has_edge(s, fpath) or G.has_edge(fpath, s) for s in selected)
    if in_degree >= 3:
        return "alto indegree (muy importado)"
    if is_neighbor:
        return "vecino directo de seleccionados"
    if score > 0.01:
        return "score medio-alto"
    return "candidato residual"


def extract_signatures_only(content: str) -> str:
    """Keep imports + function/class/type signatures, drop bodies."""
    lines = content.splitlines()
    kept = []
    skip_until_dedent = None
    for line in lines:
        stripped = line.lstrip()
        # always keep imports / requires / use / package
        if re.match(
            r"^(import |from |require\(|use |package |mod |export )", stripped
        ) or stripped.startswith("//") or stripped.startswith("#"):
            kept.append(line)
            continue
        # keep signatures (heuristic)
        if re.match(
            r"^(export )?(async )?(function |class |interface |type |const |let |var |def |fn |pub |struct |enum )",
            stripped,
        ) or re.match(r"^\s*(public |private |protected |static )", stripped):
            kept.append(line)
            # crude body skip for languages with braces
            if "{" in line and not line.rstrip().endswith("}"):
                skip_until_dedent = len(line) - len(stripped)
            continue
        if skip_until_dedent is not None:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 999
            if current_indent <= skip_until_dedent and line.strip():
                skip_until_dedent = None
                if not line.strip().startswith("}"):
                    kept.append(line)
            continue
        # keep top-level declarations without body
        if stripped and not stripped.startswith((" ", "\t", "}", ")")):
            if any(k in stripped for k in ("=", ":", "->", "=>")) and len(stripped) < 120:
                kept.append(line)
    return "\n".join(kept) if kept else content[:500] + "\n// ... (signatures-only truncated)"


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def mode_reducido(args: argparse.Namespace) -> None:
    json_path = Path(args.json)
    if not json_path.exists():
        print(f"ERROR: no existe {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    files: dict[str, str] = data.get("files", {})
    if not files:
        print("ERROR: JSON sin clave 'files'", file=sys.stderr)
        sys.exit(1)

    G = load_or_build_graph(json_path, files)
    ranked = compute_pagerank(G, personalize=args.personalize or None)
    sorted_files = sorted(ranked.items(), key=lambda x: x[1], reverse=True)

    selected = []
    total_tokens = 0
    selected_set = set()
    for fpath, score in sorted_files:
        content = files[fpath]
        if args.signatures_only:
            content = extract_signatures_only(content)
        toks = estimate_tokens(content)
        if total_tokens + toks > args.budget:
            break
        selected.append((fpath, content, score))
        selected_set.add(fpath)
        total_tokens += toks

    # candidates = next ones that did not fit + high-score neighbors
    candidates = []
    for fpath, score in sorted_files:
        if fpath in selected_set:
            continue
        if len(candidates) >= 25:
            break
        reason = reason_for_candidate(fpath, score, G, selected_set)
        candidates.append((fpath, score, reason, estimate_tokens(files[fpath])))

    # output
    print("=" * 60)
    print("MODO: reducido")
    print(f"Archivos incluidos: {len(selected)}  |  Tokens estimados: ~{total_tokens}")
    print(f"Budget: {args.budget}  |  Signatures-only: {args.signatures_only}")
    if args.personalize:
        print(f"Personalize: {', '.join(args.personalize)}")
    print("=" * 60)

    print("\n--- PATHS SELECCIONADOS (score) ---")
    for fpath, _, score in selected:
        print(f"  {score:.5f}  {fpath}")

    print("\n--- CANDIDATOS A EXPANSIÓN (score | razón | ~tokens) ---")
    for fpath, score, reason, toks in candidates:
        print(f"  {score:.5f}  {fpath}  |  {reason}  |  ~{toks} tok")

    print("\n--- CONTENIDO DEL PACK ---\n")
    for fpath, content, score in selected:
        print(f"// ===== {fpath}  (PageRank {score:.5f}) =====")
        print(content)
        print()


def mode_drill_down(args: argparse.Namespace) -> None:
    # same as reducido but with strong focus personalization
    args.personalize = (args.personalize or []) + [args.focus]
    # force focus into the personalization heavily via the focus param
    json_path = Path(args.json)
    if not json_path.exists():
        print(f"ERROR: no existe {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    files: dict[str, str] = data.get("files", {})
    if not files:
        print("ERROR: JSON sin clave 'files'", file=sys.stderr)
        sys.exit(1)

    G = load_or_build_graph(json_path, files)
    ranked = compute_pagerank(G, personalize=args.personalize, focus=args.focus)
    sorted_files = sorted(ranked.items(), key=lambda x: x[1], reverse=True)

    selected = []
    total_tokens = 0
    selected_set = set()
    for fpath, score in sorted_files:
        # prefer files under focus
        content = files[fpath]
        if args.signatures_only:
            content = extract_signatures_only(content)
        toks = estimate_tokens(content)
        if total_tokens + toks > args.budget:
            break
        selected.append((fpath, content, score))
        selected_set.add(fpath)
        total_tokens += toks

    candidates = []
    for fpath, score in sorted_files:
        if fpath in selected_set:
            continue
        if len(candidates) >= 20:
            break
        reason = reason_for_candidate(fpath, score, G, selected_set)
        if fpath.startswith(args.focus.rstrip("/") + "/") or fpath == args.focus:
            reason = "dentro del focus + " + reason
        candidates.append((fpath, score, reason, estimate_tokens(files[fpath])))

    print("=" * 60)
    print("MODO: drill-down")
    print(f"Focus: {args.focus}")
    print(f"Archivos incluidos: {len(selected)}  |  Tokens estimados: ~{total_tokens}")
    print(f"Budget: {args.budget}  |  Signatures-only: {args.signatures_only}")
    print("=" * 60)

    print("\n--- PATHS SELECCIONADOS (score) ---")
    for fpath, _, score in selected:
        print(f"  {score:.5f}  {fpath}")

    print("\n--- CANDIDATOS A EXPANSIÓN (score | razón | ~tokens) ---")
    for fpath, score, reason, toks in candidates:
        print(f"  {score:.5f}  {fpath}  |  {reason}  |  ~{toks} tok")

    print("\n--- CONTENIDO DEL PACK ---\n")
    for fpath, content, score in selected:
        print(f"// ===== {fpath}  (PageRank {score:.5f}) =====")
        print(content)
        print()


def mode_ampliado(args: argparse.Namespace) -> None:
    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    if not paths:
        print("ERROR: --paths vacío", file=sys.stderr)
        sys.exit(1)
    if len(paths) > MAX_AMPLIADO_PATHS:
        print(
            f"AVISO: se recibieron {len(paths)} paths. Límite duro = {MAX_AMPLIADO_PATHS}. "
            f"Se usarán solo los primeros {MAX_AMPLIADO_PATHS}.",
            file=sys.stderr,
        )
        paths = paths[:MAX_AMPLIADO_PATHS]

    # Build include pattern for repomix
    # Repomix accepts --include with globs
    include_globs = []
    for p in paths:
        p = p.rstrip("/")
        if Path(p).suffix:  # file
            include_globs.append(p)
        else:  # directory
            include_globs.append(f"{p}/**/*")

    include_arg = ",".join(include_globs)

    cmd = [
        "npx",
        "repomix",
        "--style",
        "json",
        "--no-file-summary",
        "--no-directory-structure",
        "-o",
        "-",  # stdout
        "--include",
        include_arg,
    ]
    # deliberately NO --compress

    print("=" * 60)
    print("MODO: ampliado (código real, sin compress)")
    print(f"Paths solicitados: {', '.join(paths)}")
    print(f"Comando: {' '.join(cmd)}")
    print("=" * 60)
    print()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.getcwd(),
        )
    except subprocess.TimeoutExpired:
        print("ERROR: repomix timeout", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: npx/repomix no encontrado", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        print("ERROR de repomix:", result.stderr, file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        # fallback: maybe plain output, just print it
        print(result.stdout)
        return

    files = data.get("files", {})
    total_tokens = 0
    print(f"Archivos devueltos: {len(files)}")
    for fpath, content in files.items():
        toks = estimate_tokens(content)
        total_tokens += toks
        print(f"  ~{toks} tok  {fpath}")
    print(f"Tokens estimados totales: ~{total_tokens}")
    print("\n--- CONTENIDO REAL ---\n")
    for fpath, content in files.items():
        print(f"// ===== {fpath} =====")
        print(content)
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="repo-packager — empaqueta contexto con PageRank + Repomix"
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # reducido
    p_red = sub.add_parser("reducido", help="Pack rankeado + candidatos")
    p_red.add_argument("--json", required=True, help="JSON de repomix --style json --compress")
    p_red.add_argument("--budget", type=int, default=8000, help="Token budget (default 8000)")
    p_red.add_argument(
        "--personalize",
        nargs="*",
        default=[],
        help="Archivos a potenciar (contexto actual)",
    )
    p_red.add_argument(
        "--signatures-only",
        action="store_true",
        help="Solo firmas + imports (máxima compresión)",
    )

    # drill-down
    p_dd = sub.add_parser("drill-down", help="Mapa fino centrado en una zona")
    p_dd.add_argument("--json", required=True, help="JSON de repomix --style json --compress")
    p_dd.add_argument("--focus", required=True, help="Path o directorio a centrar")
    p_dd.add_argument("--budget", type=int, default=6000, help="Token budget (default 6000)")
    p_dd.add_argument(
        "--personalize",
        nargs="*",
        default=[],
        help="Archivos extra a potenciar",
    )
    p_dd.add_argument(
        "--signatures-only",
        action="store_true",
        help="Solo firmas + imports",
    )

    # ampliado
    p_amp = sub.add_parser("ampliado", help="Código real de paths concretos (max 10)")
    p_amp.add_argument(
        "--paths",
        required=True,
        help="Lista separada por comas de paths/directorios (máx 10)",
    )
    p_amp.add_argument(
        "--json",
        default=None,
        help="Opcional, solo para metadata (no se usa el contenido)",
    )

    args = parser.parse_args()

    if args.mode == "reducido":
        mode_reducido(args)
    elif args.mode == "drill-down":
        mode_drill_down(args)
    elif args.mode == "ampliado":
        mode_ampliado(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()