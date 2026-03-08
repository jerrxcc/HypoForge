#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from hypoforge.application.services import build_default_services, build_fake_services


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a HypoForge topic pipeline")
    parser.add_argument("topic", help="Research topic to analyze")
    parser.add_argument("--fake", action="store_true", help="Use deterministic fake services")
    parser.add_argument(
        "--database-url",
        default="sqlite:///./hypoforge.cli.db",
        help="Override the SQLite database URL",
    )
    args = parser.parse_args()

    services = (
        build_fake_services(database_url=args.database_url)
        if args.fake
        else build_default_services()
    )
    result = services.coordinator.run_topic(args.topic)
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "status": result.status,
                "hypothesis_count": len(result.hypotheses),
                "trace_url": result.trace_url,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if result.report_markdown:
        print("\n--- REPORT ---\n")
        print(result.report_markdown)


if __name__ == "__main__":
    main()
