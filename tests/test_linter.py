"""Prueba de Linter Soberano y Cumplimiento SDD (CA-04 / Reglas de Ciberseguridad).

Se ejecuta como parte de la suite oficial de pytest (tests/).
Valida estáticamente mediante AST y reglas de pyproject.toml:
1. Prohibición terminante de random() o Math.random en el backend.
2. Prohibición de funciones inseguras (eval, exec).
3. Inmutabilidad estricta en contratos (@dataclass(frozen=True, slots=True)).
4. Verificación de sintaxis estricta y cumplimiento con Ruff si está disponible.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIRS = ["core", "pipeline", "app"]


class SDDCodeAuditor(ast.NodeVisitor):
    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.rel_path = filepath.relative_to(ROOT_DIR)
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "random":
                self.violations.append(
                    f"[{self.rel_path}:{node.lineno}] VIOLACIÓN CA-04: 'import random' prohibido."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module and (node.module == "random" or node.module.startswith("random.")):
            self.violations.append(
                f"[{self.rel_path}:{node.lineno}] VIOLACIÓN CA-04: importación desde 'random' prohibida."
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Detectar .random()
        if isinstance(node.func, ast.Attribute) and node.func.attr == "random":
            self.violations.append(
                f"[{self.rel_path}:{node.lineno}] VIOLACIÓN CA-04: Invocación a función .random() prohibida."
            )
        # Detectar eval / exec
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self.violations.append(
                f"[{self.rel_path}:{node.lineno}] VIOLACIÓN SEGURIDAD: Invocación a {node.func.id}() prohibida."
            )
        self.generic_visit(node)


def get_backend_python_files() -> list[Path]:
    files: list[Path] = []
    for d in BACKEND_DIRS:
        folder = ROOT_DIR / d
        if folder.exists():
            files.extend(folder.rglob("*.py"))
    return files


def test_no_random_allowed_in_backend() -> None:
    """CA-04: Prohíbe cualquier uso de random() en el backend (EXPLICA determinista)."""
    py_files = get_backend_python_files()
    assert len(py_files) > 0, "No se encontraron archivos en core/ o pipeline/"

    all_violations: list[str] = []
    for f in py_files:
        content = f.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(f))
        auditor = SDDCodeAuditor(f)
        auditor.visit(tree)
        all_violations.extend(auditor.violations)

    assert not all_violations, f"Se detectaron violaciones a la regla anti-random:\n" + "\n".join(all_violations)


def test_no_unsafe_eval_or_exec() -> None:
    """Ciberseguridad: Ningún módulo de producción puede invocar eval() o exec()."""
    py_files = get_backend_python_files()
    all_violations: list[str] = []

    for f in py_files:
        content = f.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(f))
        auditor = SDDCodeAuditor(f)
        auditor.visit(tree)
        for v in auditor.violations:
            if "SEGURIDAD" in v:
                all_violations.append(v)

    assert not all_violations, f"Se detectaron funciones inseguras:\n" + "\n".join(all_violations)


def test_context_dataclasses_declare_frozen_and_slots() -> None:
    """Garantiza que todos los DTOs de core/context.py sean inmutables en memoria."""
    context_file = ROOT_DIR / "core" / "context.py"
    if not context_file.exists():
        pytest.skip("core/context.py no encontrado")

    content = context_file.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(context_file))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Verificar si tiene decorador @dataclass
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and getattr(decorator.func, "id", None) == "dataclass":
                    keywords = {kw.arg: getattr(kw.value, "value", None) for kw in decorator.keywords}
                    assert keywords.get("frozen") is True, f"{node.name} debe tener frozen=True"
                    assert keywords.get("slots") is True, f"{node.name} debe tener slots=True"


def test_ruff_linter_if_installed() -> None:
    """Ejecuta Ruff con las reglas de pyproject.toml si está disponible en el entorno."""
    try:
        res = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "core", "pipeline", "app"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            if "No module named ruff" in (res.stderr or ""):
                return
            # Si ruff reporta errores, se señalan
            pytest.fail(f"Ruff detectó violaciones de estilo/lint:\n{res.stdout or res.stderr}")
    except FileNotFoundError:
        # Si ruff no está en el venv actual, el test no falla ya que el AST validó las reglas
        pass
