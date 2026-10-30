"""Fallback-pinned coverage for the simplified 10-tool registry.

`LCM_SIMPLIFIED_TOOL_SCHEMAS` swaps the advertised set from the full 16-tool
registry to a merged 10-tool registry behind thin dispatchers. These tests
freeze:

- registry selection by the gate (OFF = full 16, ON = simplified 10),
- the exposed schema counts in each mode (dormant tools omitted),
- that the simplified schemas carry no top-level provider-forbidden combinator,
- that `lcm_grep` keeps its externalized-search parameters after simplification,
- that every simplified dispatcher routes to the correct original handler.

The plugin is loaded through the conftest-registered ``hermes_lcm`` package
path (never a top-level ``from hermes_lcm.engine import ...``), which re-execs
``engine.py`` against the host ``agent.context_engine`` import and fails in
this test environment.
"""

import os
import sys

import pytest


@pytest.fixture(scope="module")
def plugin():
    """Load the plugin as a package via its conftest-registered submodules."""
    name = "hermes_lcm"
    module = sys.modules.get(name)
    if module is None:
        raise RuntimeError("conftest did not register the hermes_lcm package")
    return module


@pytest.fixture
def env(tmp_path, monkeypatch):
    for key in list(os.environ):
        if key.startswith("LCM_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LCM_DATABASE_PATH", str(tmp_path / "registry.db"))
    monkeypatch.setenv("LCM_EMBEDDINGS_ENABLED", "false")


@pytest.fixture
def plugin_env(plugin, env):
    """(plugin, tools submodule) so dispatchers and patches share one module."""
    return plugin, plugin.tools


def _engine(plugin, tmp_path, **cfg):
    config = plugin.config.LCMConfig(database_path=str(tmp_path / "e.db"), **cfg)
    return plugin.engine.LCMEngine(config=config)


# ---------------------------------------------------------------------------
# Registry selection by gate
# ---------------------------------------------------------------------------

def test_active_registry_selected_by_gate(plugin_env, tmp_path):
    plugin, _tools = plugin_env
    registry = plugin.tool_registry
    off = _engine(plugin, tmp_path)
    on = _engine(plugin, tmp_path, simplified_tool_schemas=True)
    try:
        assert off._active_tool_registry() is registry.TOOL_REGISTRY
        assert on._active_tool_registry() is registry.TOOL_REGISTRY_SIMPLIFIED

        # Full registry: 16 specs, 3 dormant by default (query_state, retrieve, memory).
        off_names = [s["name"] for s in off.get_tool_schemas()]
        assert len(off_names) == 13
        assert set(off_names) == {
            spec.name for spec in registry.TOOL_REGISTRY
        } - {"lcm_query_state", "lcm_retrieve", "lcm_memory"}

        # Simplified registry: 10 specs, lcm_assertions dormant by default.
        on_schemas = on.get_tool_schemas()
        assert len(on_schemas) == 9
        assert {s["name"] for s in on_schemas} == {
            spec.name for spec in registry.TOOL_REGISTRY_SIMPLIFIED
        } - {"lcm_assertions"}
    finally:
        off.shutdown()
        on.shutdown()


def test_registry_sizes_are_stable(plugin):
    registry = plugin.tool_registry
    assert len(registry.TOOL_REGISTRY) == 16
    assert len(registry.TOOL_REGISTRY_SIMPLIFIED) == 10
    # No name is advertised twice within a registry.
    full = [spec.name for spec in registry.TOOL_REGISTRY]
    simplified = [spec.name for spec in registry.TOOL_REGISTRY_SIMPLIFIED]
    assert len(full) == len(set(full))
    assert len(simplified) == len(set(simplified))


def test_simplified_schemas_have_no_top_level_combinator(plugin):
    forbidden = ("allOf", "anyOf", "oneOf", "enum", "not")
    for spec in plugin.tool_registry.TOOL_REGISTRY_SIMPLIFIED:
        params = spec.schema.get("parameters") or {}
        for key in forbidden:
            assert key not in params, f"{spec.name}:{key}"


# ---------------------------------------------------------------------------
# Restored grep capability (externalized search) survives simplification
# ---------------------------------------------------------------------------

def test_simplified_grep_keeps_externalized_search(plugin):
    props = plugin.schemas.SIMPLIFIED_SCHEMAS["lcm_grep"]["parameters"]["properties"]
    assert "content_scope" in props
    assert "externalized_refs" in props
    assert props["content_scope"]["enum"] == ["history", "externalized", "both"]
    assert props["content_scope"].get("default") == "history"


# ---------------------------------------------------------------------------
# Dispatcher routing (each simplified tool -> the correct original handler)
# ---------------------------------------------------------------------------

def test_diagnostics_routes_by_action(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    calls = []
    for name in ("lcm_status", "lcm_inspect", "lcm_doctor"):
        monkeypatch.setattr(
            tools, name, lambda args, *, engine=None, _n=name: (calls.append(_n), f"ok:{_n}")[1]
        )
    assert tools.lcm_diagnostics({"action": "status"}) == "ok:lcm_status"
    assert tools.lcm_diagnostics({"action": "inspect", "limit": 5}) == "ok:lcm_inspect"
    assert tools.lcm_diagnostics({"action": "doctor", "repair_action": "x"}) == "ok:lcm_doctor"
    assert calls == ["lcm_status", "lcm_inspect", "lcm_doctor"]


def test_evidence_routes_by_proposal_presence(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    calls = []
    monkeypatch.setattr(
        tools, "lcm_compile_evidence", lambda args, **kw: (calls.append("compile"), "ok:compile")[1]
    )
    monkeypatch.setattr(
        tools, "lcm_evidence_pack", lambda args, **kw: (calls.append("pack"), "ok:pack")[1]
    )
    assert tools.lcm_evidence_unified({"question": "q"}) == "ok:pack"
    proposal = {"version": "evidence-selector-v1", "selections": [], "missing_facets": []}
    assert tools.lcm_evidence_unified({"question": "q", "proposal": proposal}) == "ok:compile"
    assert calls == ["pack", "compile"]


def test_assertions_routes_by_mode(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    calls = []
    monkeypatch.setattr(
        tools, "lcm_query_state", lambda args, **kw: (calls.append("query_state"), "ok:qs")[1]
    )
    monkeypatch.setattr(
        tools, "lcm_memory", lambda args, **kw: (calls.append("memory"), "ok:mem")[1]
    )
    assert tools.lcm_assertions_unified({"mode": "query"}) == "ok:qs"
    assert tools.lcm_assertions_unified({"mode": "lookup", "name": "n"}) == "ok:mem"
    assert tools.lcm_assertions_unified({"mode": "list"}) == "ok:mem"
    assert calls == ["query_state", "memory", "memory"]


def test_expand_routes_by_query_presence(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    calls = []
    monkeypatch.setattr(
        tools, "lcm_expand_query", lambda args, **kw: (calls.append("query"), "ok:eq")[1]
    )
    monkeypatch.setattr(
        tools, "lcm_expand", lambda args, **kw: (calls.append("direct"), "ok:ex")[1]
    )
    assert tools.lcm_expand_unified({"node_id": 5}) == "ok:ex"
    assert tools.lcm_expand_unified({"query": "what happened"}) == "ok:eq"
    assert calls == ["direct", "query"]


# ---------------------------------------------------------------------------
# Dispatcher arg mapping (simplified names -> original handler args)
# ---------------------------------------------------------------------------

def test_grep_simplified_maps_and_passes_through(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    captured = {}
    monkeypatch.setattr(tools, "lcm_grep", lambda args, **kw: (captured.update(args), "ok")[1])
    tools.lcm_grep_simplified({
        "query": "x",
        "session_id": "abc",
        "exclude_sessions": ["s1"],
        "content_scope": "both",
        "externalized_refs": ["r.json"],
    })
    assert captured["session_scope"] == "session"
    assert captured["session_id"] == "abc"
    assert captured["exclude_session_ids"] == ["s1"]
    # Restored externalized-search parameters reach the original handler.
    assert captured["content_scope"] == "both"
    assert captured["externalized_refs"] == ["r.json"]


def test_grep_simplified_omits_session_mapping_when_absent(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    captured = {}
    monkeypatch.setattr(tools, "lcm_grep", lambda args, **kw: (captured.update(args), "ok")[1])
    tools.lcm_grep_simplified({"query": "x"})
    assert "session_scope" not in captured
    assert "exclude_session_ids" not in captured


def test_recall_simplified_maps_exclude_sessions(plugin_env, monkeypatch):
    _plugin, tools = plugin_env
    captured = {}
    monkeypatch.setattr(tools, "lcm_recall", lambda args, **kw: (captured.update(args), "ok")[1])
    tools.lcm_recall_simplified({"query": "q", "exclude_sessions": ["s1"]})
    assert captured["exclude_session_ids"] == ["s1"]
    assert "exclude_sessions" not in captured
