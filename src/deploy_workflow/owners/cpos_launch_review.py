"""What a live run's events leave for review after it ends: context summaries, repairs that
removed values and charges not settled. Moved from ``cpos_launch``; the launcher
re-exports every name.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, TextIO

from deploy_workflow.model.budget import exact_sum
from deploy_workflow.model.handoff import FAILED_NO_USAGE
from deploy_workflow.owners.cpos import review_line
from deploy_workflow.run_events import EVENTS, read_events


def _run_events(directory: Path) -> tuple[list[dict[str, Any]], str | None]:
    """The run's events, or why they could not be read. No event file: nothing was recorded."""
    try:
        return read_events(directory / EVENTS), None
    except FileNotFoundError:
        return [], None
    except (OSError, ValueError) as error:
        return [], f"the run events could not be read ({error})"


def _review_lines(directory: Path) -> tuple[str, ...]:
    """One line per module whose accepted handoff was written after GitHub Copilot summarised its
    context, and one per module that had more than one summary billed in a call, from the run's
    events (the last ``module_accepted`` of each module, so a resumed run lists a module once)."""
    events, problem = _run_events(directory)
    if problem is not None:
        return (f"Review: {problem}; check each module's calls.",)
    accepted = {str(e.get("module")): e for e in events if e.get("event") == "module_accepted"}
    lines = []
    for module, event in accepted.items():
        if event.get("written_after_compaction") is True:
            before = event.get("compaction_tokens_before")
            lines.append(review_line(module, before if isinstance(before, int) else None))
    multiple = dict.fromkeys(
        str(e.get("module")) for e in events if e.get("event") == "compaction_multiple"
    )
    lines += [
        f"Review: {module} had more than one context summary billed in one call; check the "
        "run's charge."
        for module in multiple
    ]
    return (*lines, *_dropped_value_lines(events))


def _dropped_value_lines(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """One line per module whose accepted repair removed sourced values (the last such event of a
    module), and one per module whose removed-values check failed."""
    dropped = {
        str(e.get("module")): e.get("count")
        for e in events
        if e.get("event") == "values_dropped_on_repair"
    }
    lines = []
    for module, count in dropped.items():
        one = count == 1
        what = "1 sourced value" if one else f"{count} sourced values"
        lines.append(
            f"Review: {module} was accepted after a repair that removed {what}; the list is in "
            f"that module's review.json (dropped_values). Check {'it' if one else 'them'}."
        )
    failed = dict.fromkeys(
        str(e.get("module")) for e in events if e.get("event") == "dropped_values_check_failed"
    )
    lines += [
        f"Review: {module} had a repair whose removed values could not be checked "
        "(dropped_values_error in its review.json); compare the repair with the rejected draft."
        for module in failed
    ]
    return lines


def _attempt(event: Mapping[str, Any]) -> str:
    value = event.get("attempt_id")
    return value if isinstance(value, str) else ""


def _uncharged_summaries(events: Sequence[Mapping[str, Any]]) -> dict[Any, tuple[Any, Any]]:
    """The context summaries with no reported charge, key -> (module, call). One attempt is one
    summary however many events name it; an event with no attempt id is one summary of its own.
    A start that never ended is counted from its events too (a killed run wrote no disclosure),
    and a summary charged late is only that charge."""
    found: dict[Any, tuple[Any, Any]] = {}
    started: dict[Any, tuple[Any, Any]] = {}
    ended: set[Any] = set()
    anonymous: dict[Any, list[int]] = {}  # module -> [starts, ends, disclosed], no attempt id
    for number, e in enumerate(events):
        name, module, call = e.get("event"), e.get("module"), e.get("call_index")
        attempt = _attempt(e)
        counts = anonymous.setdefault(module, [0, 0, 0])
        if name == "compaction_uncharged":
            found[(module, attempt) if attempt else (module, number)] = (module, call)
            # a failed completion's own record is not a second sign that a start ended
            counts[2] += not attempt and e.get("reason") != FAILED_NO_USAGE
        elif name == "context_compaction_started":
            if attempt:
                started[(module, attempt)] = (module, call)
            else:
                counts[0] += 1
        elif name in {"context_compacted", "compaction_charge_late"}:
            if attempt:
                ended.add((module, attempt))
            else:
                counts[1] += 1
    for key, where in started.items():
        if key not in ended:
            found.setdefault(key, where)
    for module, (starts, ends, disclosed) in anonymous.items():
        for extra in range(max(0, starts - ends - disclosed)):
            found[(module, "unmatched", extra)] = (module, None)
    late = {
        (e.get("module"), _attempt(e)) for e in events if e.get("event") == "compaction_charge_late"
    }
    return {k: v for k, v in found.items() if k not in late}


def _charge_notes(directory: Path) -> tuple[str, ...]:
    """What ``Charged:`` leaves out, from the run's events, each compaction counted once (a
    relaunch reads the same events and cannot count one again): context summaries with no
    reported charge, and charges the runtime reported after their module ended (not settled)."""
    events, _ = _run_events(directory)
    uncharged = _uncharged_summaries(events)
    late = {
        (e.get("module"), _attempt(e) or number, e.get("call_index")): e.get("usd")
        for number, e in enumerate(events)
        if e.get("event") == "compaction_charge_late"
    }
    notes = []
    if uncharged:
        modules = ", ".join(
            dict.fromkeys(str(m) for m, _ in sorted(uncharged.values(), key=_order))
        )
        count = len(uncharged)
        noun = "summary" if count == 1 else "summaries"
        notes.append(
            f"Charged excludes {count} context {noun} with no reported charge ({modules}); "
            "Copilot may bill them."
        )
    if late:
        amounts, unreadable = [], 0
        for usd in late.values():
            try:
                amounts.append(Decimal(str(usd)))
            except InvalidOperation:  # a hand-edited or damaged event: shown, not hidden
                unreadable += 1
        named = ", ".join(dict.fromkeys(str(m) for m, _, _ in late))
        total = f"USD {exact_sum(amounts)} " if amounts else ""
        more = ""
        if unreadable:
            more = (
                f", and {unreadable} amount{'s' if unreadable > 1 else ''} that could not be read"
                if amounts
                else f"{unreadable} amount{'s' if unreadable > 1 else ''} that could not be read "
            )
        notes.append(
            f"Charged excludes {total}of context-summary charges reported after their "
            f"module ended ({named}){more}; they were not settled."
        )
    return tuple(notes)


def _order(item: tuple[Any, Any]) -> tuple[int, str]:
    return (item[1] if isinstance(item[1], int) else 0, str(item[0]))


def _print_review(directory: Path, stream: TextIO) -> None:
    for line in (*_charge_notes(directory), *_review_lines(directory)):
        print(line, file=stream)
