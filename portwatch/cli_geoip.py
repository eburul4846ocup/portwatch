"""CLI sub-commands for GeoIP lookups."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from portwatch.geoip import lookup


def _default_cache_path() -> Path:
    return Path.home() / ".portwatch" / "geoip_cache.json"


def cmd_geoip_lookup(args: argparse.Namespace) -> None:
    cache_path = Path(args.cache) if args.cache else _default_cache_path()
    results = []
    for ip in args.ip:
        info = lookup(ip, cache_path=cache_path)
        results.append(info.as_dict())

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        header = f"{'IP':<18} {'Country':<10} {'City':<18} {'ASN'}"
        print(header)
        print("-" * len(header))
        for r in results:
            print(
                f"{r['ip']:<18} {r['country']:<10} {r['city']:<18} {r['asn']}"
            )


def cmd_geoip_clear_cache(args: argparse.Namespace) -> None:
    cache_path = Path(args.cache) if args.cache else _default_cache_path()
    if cache_path.exists():
        cache_path.unlink()
        print(f"Cache cleared: {cache_path}")
    else:
        print("No cache file found.")


def register_geoip_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # geoip lookup
    p_lookup = subparsers.add_parser(
        "geoip", help="Look up geographic info for one or more IP addresses"
    )
    p_lookup.add_argument("ip", nargs="+", help="IP address(es) to look up")
    p_lookup.add_argument(
        "--cache", default="", help="Path to GeoIP cache file (JSON)"
    )
    p_lookup.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )
    p_lookup.set_defaults(func=cmd_geoip_lookup)

    # geoip clear-cache
    p_clear = subparsers.add_parser(
        "geoip-clear-cache", help="Remove the local GeoIP cache"
    )
    p_clear.add_argument(
        "--cache", default="", help="Path to GeoIP cache file (JSON)"
    )
    p_clear.set_defaults(func=cmd_geoip_clear_cache)
