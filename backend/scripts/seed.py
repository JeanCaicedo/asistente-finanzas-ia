"""CLI: siembra la BD con datos de ejemplo.

Uso (desde backend/):  python -m scripts.seed  [--reset]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar como script suelto (añade backend/ al path).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_connection, init_schema  # noqa: E402
from app.repositories import categories as cat_repo  # noqa: E402
from app.services import seed as seed_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Siembra datos de ejemplo.")
    parser.add_argument(
        "--reset", action="store_true", help="Borra datos de usuario antes de sembrar."
    )
    args = parser.parse_args()

    init_schema()
    conn = get_connection()
    try:
        if args.reset:
            conn.execute("DELETE FROM goal_contribution")
            conn.execute("DELETE FROM savings_goal")
            conn.execute("DELETE FROM budget")
            conn.execute('DELETE FROM "transaction"')
            conn.execute("DELETE FROM category WHERE is_system = 0")
        cat_repo.seed_system_categories(conn)
        seed_service.generate(conn)
        print("Datos de ejemplo sembrados.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
