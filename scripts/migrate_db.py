import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import engine, init_db
from app.database.migrations import migration_status


def main() -> None:
    init_db()
    status = migration_status(engine)
    print(
        "Database migrations current: "
        f"{status['current']} ({len(status['applied'])}/{len(status['available'])} applied)"
    )
    if status["pending"]:
        print("Pending migrations:", ", ".join(status["pending"]))


if __name__ == "__main__":
    main()
