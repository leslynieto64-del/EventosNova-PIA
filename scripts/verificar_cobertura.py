"""Comprueba el requisito de cobertura del PIA a partir de `coverage json`.

    coverage run -m unittest discover -s tests
    coverage json -o coverage.json -q
    python scripts/verificar_cobertura.py coverage.json [--minimo 80]

La métrica del requisito del 80 % es la cobertura de SENTENCIAS (líneas); también se informa la de ramas. Sale con código 1 si la
cobertura de sentencias no alcanza el mínimo. No modifica ninguna evidencia."""
import argparse
import json
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verifica la cobertura mínima de sentencias")
    parser.add_argument("archivo", help="salida de `coverage json`")
    parser.add_argument("--minimo", type=float, default=80.0)
    args = parser.parse_args(argv)
    with open(args.archivo, encoding="utf-8") as f:
        t = json.load(f)["totals"]
    sentencias = t["percent_statements_covered"]
    ramas = 100.0 * t["covered_branches"] / t["num_branches"] if t.get("num_branches") else 100.0
    print(f"Cobertura de sentencias: {sentencias:.2f} % ({t['covered_lines']} de {t['num_statements']}; sin cubrir {t['missing_lines']})")
    print(f"Cobertura de ramas:      {ramas:.2f} % ({t.get('covered_branches', 0)} de {t.get('num_branches', 0)})")
    if sentencias < args.minimo:
        print(f"FALLO: la cobertura de sentencias {sentencias:.2f} % es menor que el mínimo {args.minimo:.0f} %.", file=sys.stderr)
        return 1
    print(f"OK: cumple el mínimo de {args.minimo:.0f} %.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
