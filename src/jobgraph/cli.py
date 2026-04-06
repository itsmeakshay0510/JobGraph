from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local job scraping and resume tailoring agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the full scrape-tailor-email pipeline.")
    run_parser.add_argument("--project-root", default=".", help="Project root directory.")
    run_parser.add_argument("--settings", default="configs/settings.yaml", help="Path to settings YAML.")
    run_parser.add_argument("--profile", default="configs/candidate_profile.yaml", help="Path to candidate profile YAML.")
    run_parser.add_argument("--companies", default="configs/companies.yaml", help="Path to company sources YAML.")
    run_parser.add_argument("--dry-run", action="store_true", help="Run without writing resumes or sending email.")

    preview_parser = subparsers.add_parser("preview", help="Run and print generated roles as JSON.")
    preview_parser.add_argument("--project-root", default=".", help="Project root directory.")
    preview_parser.add_argument("--settings", default="configs/settings.yaml", help="Path to settings YAML.")
    preview_parser.add_argument("--profile", default="configs/candidate_profile.yaml", help="Path to candidate profile YAML.")
    preview_parser.add_argument("--companies", default="configs/companies.yaml", help="Path to company sources YAML.")

    return parser


def _handle_run(args: argparse.Namespace) -> int:
    generated = run_agent(
        project_root=Path(args.project_root).resolve(),
        settings_path=Path(args.settings).resolve(),
        profile_path=Path(args.profile).resolve(),
        companies_path=Path(args.companies).resolve(),
        dry_run=args.dry_run,
    )
    print(f"Generated {len(generated)} tailored resume(s).")
    return 0


def _handle_preview(args: argparse.Namespace) -> int:
    generated = run_agent(
        project_root=Path(args.project_root).resolve(),
        settings_path=Path(args.settings).resolve(),
        profile_path=Path(args.profile).resolve(),
        companies_path=Path(args.companies).resolve(),
        dry_run=True,
    )
    preview = [{"company": item.company, "role": item.role, "summary": item.summary} for item in generated]
    print(json.dumps(preview, indent=2))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run":
        return _handle_run(args)
    if args.command == "preview":
        return _handle_preview(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
