#!/usr/bin/env python3
"""verificar_entorno.py — Clase 00: Setup Profesional.

Verifica que todas las herramientas del curso estan instaladas
y funcionando correctamente.

Ejecutar (desde la raiz del repo publico):
    uv run python verificar_entorno.py

# Windows (PowerShell)
    uv run python verificar_entorno.py

# Linux
    uv run python verificar_entorno.py
"""

import os
import platform
import shutil
import subprocess


def check(nombre: str, ok: bool, detalle: str = "") -> bool:
    """Imprime el resultado de una verificacion y retorna su estado."""
    estado = "[OK]" if ok else "[FALTA]"
    print(f"  {estado} {nombre}", end="")
    if detalle:
        print(f" — {detalle}", end="")
    print()
    return ok


def run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Ejecuta un comando y retorna el resultado sin lanzar excepciones."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=30)


print("\n=== Verificacion del entorno PyCommute ===\n")
resultados: list[bool] = []

# --- Python ---
version = platform.python_version()
resultados.append(check("Python 3.12", version.startswith("3.12"), version))

# --- UV ---
uv_path = shutil.which("uv")
resultados.append(
    check(
        "UV instalado",
        uv_path is not None,
        uv_path or "ejecutar: curl -LsSf https://astral.sh/uv/install.sh | sh",
    )
)

# --- Git ---
r = run(["git", "config", "user.name"])
nombre_git = r.stdout.strip()
resultados.append(
    check(
        "Git configurado",
        bool(nombre_git),
        nombre_git or "ejecutar: git config --global user.name 'Tu Nombre'",
    )
)

# --- SSH GitHub ---
try:
    r = run(["ssh", "-T", "git@github.com", "-o", "StrictHostKeyChecking=no"])
    ssh_ok = "successfully authenticated" in r.stderr
except Exception:
    ssh_ok = False
resultados.append(
    check(
        "SSH GitHub",
        ssh_ok,
        "OK" if ssh_ok else "agregar SSH key en github.com/settings/keys",
    )
)

# --- Docker ---
r = run(["docker", "--version"])
docker_ok = r.returncode == 0
resultados.append(
    check(
        "Docker",
        docker_ok,
        r.stdout.strip()[:40] if docker_ok else "preinstalado — contactar instructor",
    )
)

# --- Docker sin sudo ---
r = run(["docker", "ps"])
resultados.append(
    check(
        "Docker sin sudo",
        r.returncode == 0,
        "OK" if r.returncode == 0 else "ejecutar: newgrp docker",
    )
)

# --- Ollama ---
r = run(["ollama", "list"])
ollama_ok = r.returncode == 0
gemma_ok = "gemma3:1b" in r.stdout if ollama_ok else False
resultados.append(
    check(
        "Ollama",
        ollama_ok,
        "OK" if ollama_ok else "preinstalado — contactar instructor",
    )
)
resultados.append(
    check(
        "Modelo gemma3:1b",
        gemma_ok,
        "disponible" if gemma_ok else "ejecutar: ollama pull gemma3:1b",
    )
)

# --- VS Code ---
resultados.append(check("VS Code", shutil.which("code") is not None))

# --- Repo PyCommute Elite ---
repo = os.path.expanduser("~/pycommute-ai")
repo_ok = os.path.exists(repo)
resultados.append(
    check(
        "Repo PyCommute clonado",
        repo_ok,
        repo if repo_ok else "git clone https://github.com/qx-sudo/pycommute-ai.git",
    )
)

# --- Tests de PyCommute ---
if repo_ok:
    r = run(["uv", "run", "pytest", "tests/", "-q"], cwd=repo)
    tests_ok = "57 passed" in r.stdout
    resultados.append(
        check(
            "57 tests en verde",
            tests_ok,
            "57 passed" if tests_ok else r.stdout.strip().split("\n")[-1],
        )
    )

# --- Resumen ---
total = len(resultados)
ok = sum(resultados)
print(f"\n{'=' * 40}")
print(f"  {ok}/{total} verificaciones pasadas")
if ok == total:
    print("  Entorno listo para Clase 1")
else:
    print(f"  {total - ok} items pendientes — ver detalles arriba")
print()
