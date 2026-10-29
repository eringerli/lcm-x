"""Ordered tool metadata shared by the two Hermes exposure paths.

Handler names are resolved on the tools module at dispatch time.
"""

from typing import NamedTuple

from . import schemas


class ToolSpec(NamedTuple):
    name: str
    schema: dict
    handler_name: str
    emoji: str
    dormant_unless: str | None


TOOL_REGISTRY = (
    ToolSpec("lcm_grep", schemas.LCM_GREP, "lcm_grep", "🔍", None),
    ToolSpec("lcm_recall", schemas.LCM_RECALL, "lcm_recall", "🧠", None),
    ToolSpec("lcm_query_state", schemas.LCM_QUERY_STATE, "lcm_query_state", "🧾", "assertions_enabled"),
    ToolSpec("lcm_compute", schemas.LCM_COMPUTE, "lcm_compute", "🧮", None),
    ToolSpec("lcm_compile_evidence", schemas.LCM_COMPILE_EVIDENCE, "lcm_compile_evidence", "🧷", None),
    ToolSpec("lcm_evidence_pack", schemas.LCM_EVIDENCE_PACK, "lcm_evidence_pack", "📦", None),
    ToolSpec("lcm_retrieve", schemas.LCM_RETRIEVE, "lcm_retrieve", "🧭", "adaptive_retrieval_enabled"),
    ToolSpec("lcm_recent", schemas.LCM_RECENT, "lcm_recent", "🕒", None),
    ToolSpec("lcm_load_session", schemas.LCM_LOAD_SESSION, "lcm_load_session", "📋", None),
    ToolSpec("lcm_describe", schemas.LCM_DESCRIBE, "lcm_describe", "📊", None),
    ToolSpec("lcm_expand", schemas.LCM_EXPAND, "lcm_expand", "🔎", None),
    ToolSpec("lcm_expand_query", schemas.LCM_EXPAND_QUERY, "lcm_expand_query", "❓", None),
    ToolSpec("lcm_status", schemas.LCM_STATUS, "lcm_status", "💚", None),
    ToolSpec("lcm_inspect", schemas.LCM_INSPECT, "lcm_inspect", "🧭", None),
    ToolSpec("lcm_doctor", schemas.LCM_DOCTOR, "lcm_doctor", "🏥", None),
    ToolSpec("lcm_memory", schemas.LCM_MEMORY, "lcm_memory", "🗂️", "entities_enabled"),
)


# Consolidated 10-tool registry (gated by LCM_SIMPLIFIED_TOOL_SCHEMAS). Merges
# diagnostics (status/inspect/doctor), evidence (pack/compile), assertions
# (query_state/memory), and expand (expand/expand_query); reduces grep/recall
# params. Schemas come from the SIMPLIFIED_SCHEMAS container in schemas.py;
# handler names route to dispatcher wrappers in tools.py. lcm_retrieve is
# intentionally absent (adaptive retrieval stays on the full registry).
TOOL_REGISTRY_SIMPLIFIED = (
    ToolSpec("lcm_grep", schemas.SIMPLIFIED_SCHEMAS["lcm_grep"], "lcm_grep_simplified", "🔍", None),
    ToolSpec("lcm_recall", schemas.SIMPLIFIED_SCHEMAS["lcm_recall"], "lcm_recall_simplified", "🧠", None),
    ToolSpec("lcm_assertions", schemas.SIMPLIFIED_SCHEMAS["lcm_assertions"], "lcm_assertions_unified", "🧾", "assertions_enabled"),
    ToolSpec("lcm_compute", schemas.SIMPLIFIED_SCHEMAS["lcm_compute"], "lcm_compute", "🧮", None),
    ToolSpec("lcm_evidence", schemas.SIMPLIFIED_SCHEMAS["lcm_evidence"], "lcm_evidence_unified", "📦", None),
    ToolSpec("lcm_recent", schemas.SIMPLIFIED_SCHEMAS["lcm_recent"], "lcm_recent", "🕒", None),
    ToolSpec("lcm_load_session", schemas.SIMPLIFIED_SCHEMAS["lcm_load_session"], "lcm_load_session", "📋", None),
    ToolSpec("lcm_describe", schemas.SIMPLIFIED_SCHEMAS["lcm_describe"], "lcm_describe", "📊", None),
    ToolSpec("lcm_expand", schemas.SIMPLIFIED_SCHEMAS["lcm_expand"], "lcm_expand_unified", "🔎", None),
    ToolSpec("lcm_diagnostics", schemas.SIMPLIFIED_SCHEMAS["lcm_diagnostics"], "lcm_diagnostics", "💚", None),
)
