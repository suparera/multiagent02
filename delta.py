from dataclasses import dataclass


@dataclass
class DeltaResult:
    fixed: list[dict]
    remaining: list[dict]
    new: list[dict]


def analyze_delta(first_review: list[dict], re_review: list[dict]) -> DeltaResult:
    first_types = {f["type"] for f in first_review}
    re_types = {f["type"] for f in re_review}

    fixed = [f for f in first_review if f["type"] not in re_types]
    remaining = [f for f in re_review if f["type"] in first_types]
    new = [f for f in re_review if f["type"] not in first_types]

    return DeltaResult(fixed=fixed, remaining=remaining, new=new)


def print_delta(delta: DeltaResult) -> None:
    sections = [
        ("FIXED", delta.fixed, "Issues resolved by the fixer"),
        ("REMAINING", delta.remaining, "Issues still present after fixing"),
        ("NEW", delta.new, "Issues newly surfaced in re-review"),
    ]

    for label, findings, subtitle in sections:
        print(f"\n{'='*60}")
        print(f"{label} ({len(findings)}) — {subtitle}")
        print("=" * 60)
        if not findings:
            print("  (none)")
        for f in findings:
            print(f"  [{f['severity']}] {f['type']}")
            print(f"    {f['description'][:120]}{'...' if len(f['description']) > 120 else ''}")
