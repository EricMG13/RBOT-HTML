"""The optional ``module_options`` block of ``context.json``."""

import json
from pathlib import Path

import pytest

from deploy_workflow.context import ContextRefused, ModuleOptions, load_context

FIXTURE = json.loads(
    (Path(__file__).resolve().parents[1] / "cases/context/research-minimal.json").read_text(
        encoding="utf-8"
    )
)


def with_key(key: str, value: object) -> bytes:
    return json.dumps({**FIXTURE, key: value}).encode()


def test_a_context_without_module_options_loads_and_equals_the_default():
    ctx = load_context(json.dumps(FIXTURE).encode())
    assert ctx.module_options == ModuleOptions()


def test_module_options_are_read():
    ctx = load_context(
        with_key("module_options", {"cp3_mode": "single_name_rv", "cp6_deep_debate": True})
    )
    assert ctx.module_options.cp3_mode == "single_name_rv"
    assert ctx.module_options.cp6_deep_debate is True


@pytest.mark.parametrize("bad", [{"cp3_mode": "fast"}, {"cp6_deep_debate": "yes"}, {"cp9": 1}])
def test_a_wrong_module_option_is_refused(bad):
    with pytest.raises(ContextRefused):
        load_context(with_key("module_options", bad))
