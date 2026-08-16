#!/usr/bin/env python3
"""
PageRank sobre salida JSON de Repomix (--style json --compress).
Construye grafo de dependencias a partir de imports/requires y rankea archivos.
Cero tokens de IA. Todo local.
"""

import json
import re
import argparse
from pathlib import Path
from collections import defaultdict
import networkx as nx

# Regex simples y robustas para imports (cubre la mayoría de casos prácticos)
IMPORT_PATTERNS = [
    # Python
    re.compile(r'^\s*(?:from\s+([\w.]+)|import\s+([\w.]+))', re.MULTILINE),
    # JS/TS (ESM + CommonJS)
    re.compile(r'''(?:import\s+(?:[\w*{}\s,]+from\s+)?|require\s*\(\s*)['"]([^'"]+)['"]''', re.MULTILINE),
    # Go
    re.compile(r'^\s*import\s+(?:\(|")([\w./-]+)', re.MULTILINE),
    # Java / Kotlin / Scala (simplificado)
    re.compile(r'^\s*import\s+([\w.]+)', re.MULTILINE),
    # Rust
    re.compile(r'^\s*(?:use|mod)\s+([\w:]+)', re.MULTILINE),
]

def extract_imports(content: str) -> set[str]:
    """Extrae posibles módulos/archivos referenciados."""
    imports = set()
    for pat in IMPORT_PATTERNS:
        for m in pat.finditer(content):
            # toma el primer grupo no vacío
            for g in m.groups():
                if g:
                    imports.add(g.strip())
                    break
    return imports

def resolve_to_file(imp: str, all_files: dict[str, str], current_file: str) -> str | None:
    """
    Intenta mapear un import a un path real del repo.
    Heurística simple y rápida (suficiente para ranking).
    """
    # Normalizar
    imp = imp.replace("\\", "/").lstrip("./")
    # Quitar extensión si el import no la trae
    candidates = []
    for fpath in all_files:
        # coincidencia exacta o con extensiones comunes
        if fpath == imp or fpath.startswith(imp + ".") or fpath.endswith("/" + imp) or fpath.endswith("/" + imp + ".py") \
           or fpath.endswith("/" + imp + ".ts") or fpath.endswith("/" + imp + ".js") \
           or fpath.endswith("/" + imp + ".go") or fpath.endswith("/" + imp + ".rs"):
            candidates.append(fpath)
        # también por basename
        if Path(fpath).stem == Path(imp).stem or Path(fpath).name == imp:
            candidates.append(fpath)

    if not candidates:
        return None
    # Preferir el más cercano al archivo actual (misma carpeta o subcarpeta)
    current_dir = str(Path(current_file).parent)
    candidates.sort(key=lambda c: (0 if c.startswith(current_dir) else 1, len(c)))
    return candidates[0]

def build_graph(files: dict[str, str]) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(files.keys())

    for src, content in files.items():
        imports = extract_imports(content)
        for imp in imports:
            dst = resolve_to_file(imp, files, src)
            if dst and dst != src:
                # arista src → dst (src depende de dst)
                if G.has_edge(src, dst):
                    G[src][dst]["weight"] += 1
                else:
                    G.add_edge(src, dst, weight=1)
    return G

def main():
    parser = argparse.ArgumentParser(description="PageRank sobre JSON de Repomix")
    parser.add_argument("json_file", help="Archivo JSON generado por repomix --style json --compress")
    parser.add_argument("--top", type=int, default=30, help="Cuántos archivos mostrar (default 30)")
    parser.add_argument("--personalize", nargs="*", default=[], help="Archivos a dar peso extra (contexto actual)")
    parser.add_argument("--token-budget", type=int, default=None, help="Si se indica, imprime solo hasta ese presupuesto aproximado")
    parser.add_argument("--output", choices=["ranked", "prompt"], default="ranked",
                        help="ranked = lista ordenada; prompt = listo para pegar en el LLM")
    args = parser.parse_args()

    with open(args.json_file, encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("files", {})
    if not files:
        raise SystemExit("No se encontró la clave 'files' en el JSON")

    print(f"Archivos cargados: {len(files)}")
    G = build_graph(files)
    print(f"Nodos: {G.number_of_nodes()} | Aristas: {G.number_of_edges()}")

    # Personalization (estilo Aider): da más peso a los archivos del contexto actual
    personalization = None
    if args.personalize:
        personalization = {f: 100.0 for f in args.personalize if f in G}
        # el resto recibe un peso residual pequeño
        residual = 1.0 / max(len(G) - len(personalization), 1)
        for n in G:
            if n not in personalization:
                personalization[n] = residual

    ranked = nx.pagerank(G, alpha=0.85, personalization=personalization, weight="weight")
    sorted_files = sorted(ranked.items(), key=lambda x: x[1], reverse=True)

    if args.output == "ranked":
        print("\n=== Ranking PageRank (mayor = más central) ===")
        for i, (fpath, score) in enumerate(sorted_files[:args.top], 1):
            print(f"{i:3d}. {score:.6f}  {fpath}")
        return

    # Modo prompt: construye el contexto filtrado por ranking + budget
    selected = []
    total_chars = 0
    for fpath, score in sorted_files:
        content = files[fpath]
        # estimación burda de tokens (~4 chars/token)
        est_tokens = len(content) // 4
        if args.token_budget and total_chars // 4 + est_tokens > args.token_budget:
            break
        selected.append((fpath, content, score))
        total_chars += len(content)

    print(f"\n=== Contexto seleccionado ({len(selected)} archivos, ~{total_chars//4} tokens) ===\n")
    for fpath, content, score in selected:
        print(f"// ===== {fpath} (PageRank {score:.5f}) =====")
        print(content)
        print()

if __name__ == "__main__":
    main()