"""
Auto-discovery loader for built-in and custom MCP tools.

Built-in tools:  backend/mcp/tools/<name>/tool.py
Custom tools:    /app/data/custom_tools/<name>/tool.py

Each tool.py must export:
  TOOL_DEFINITION  — dict with name, description, input_schema
  handler          — callable (or function named like TOOL_DEFINITION['name'])

Optionally:
  SETTINGS_SCHEMA  — list of setting definitions
  TOOL_DEFINITIONS — list of dicts (for tool.py files that register multiple tools)
  HANDLERS         — dict {tool_name: callable} (paired with TOOL_DEFINITIONS)
"""

import os
import sys
import importlib.util
import logging

from mcp.registry import registry, MCPTool
from config import DATA_DIR

logger = logging.getLogger(__name__)


def _load_module(tool_py_path, module_name):
    """Import a tool.py file by path and return the module."""
    tool_dir = os.path.dirname(tool_py_path)
    # Add tool directory to sys.path so helper modules in the same dir are importable
    if tool_dir not in sys.path:
        sys.path.insert(0, tool_dir)
    spec = importlib.util.spec_from_file_location(module_name, tool_py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _register_module(mod, source_label='', custom=False):
    """
    Extract tool definitions and handlers from a module and register them.
    Supports single (TOOL_DEFINITION) and multi-tool (TOOL_DEFINITIONS) conventions.
    Returns number of registered tools.
    """
    count = 0

    # ── Multi-tool convention ──────────────────────────────────────────────────
    defs = getattr(mod, 'TOOL_DEFINITIONS', None)
    handlers_map = getattr(mod, 'HANDLERS', None)
    if defs is not None:
        usage = getattr(mod, 'USAGE', None)
        for td in defs:
            name = td['name']
            h = (handlers_map or {}).get(name) or getattr(mod, name, None)
            if h is None:
                logger.warning(f"[loader] {source_label}: no handler for '{name}', skipping")
                continue
            schema = getattr(mod, 'SETTINGS_SCHEMA', None)
            info = getattr(mod, 'SETTINGS_INFO', None)
            is_custom = custom or bool(getattr(mod, 'IS_CUSTOM', False))
            registry.register(MCPTool(
                name=name,
                description=td['description'],
                input_schema=td['input_schema'],
                handler=h,
                settings_schema=schema,
                settings_info=info,
                custom=is_custom,
                usage=usage,
            ))
            logger.info(f"[loader] Registered '{name}' from {source_label}")
            count += 1
        return count

    # ── Single-tool convention ─────────────────────────────────────────────────
    td = getattr(mod, 'TOOL_DEFINITION', None)
    if td is None:
        logger.warning(f"[loader] {source_label}: no TOOL_DEFINITION found, skipping")
        return 0

    name = td['name']
    # Accept 'handler' or the function named after the tool
    h = getattr(mod, 'handler', None) or getattr(mod, name, None)
    if h is None:
        logger.warning(f"[loader] {source_label}: no handler for '{name}', skipping")
        return 0

    schema = getattr(mod, 'SETTINGS_SCHEMA', None)
    info = getattr(mod, 'SETTINGS_INFO', None)
    usage = getattr(mod, 'USAGE', None)
    is_custom = custom or bool(getattr(mod, 'IS_CUSTOM', False))
    registry.register(MCPTool(
        name=name,
        description=td['description'],
        input_schema=td['input_schema'],
        handler=h,
        settings_schema=schema,
        settings_info=info,
        custom=is_custom,
        usage=usage,
    ))
    logger.info(f"[loader] Registered '{name}' from {source_label}")
    return 1


def load_builtin_tools():
    """Scan backend/mcp/tools/<name>/tool.py and register all built-in tools."""
    tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
    total = 0
    for entry in sorted(os.listdir(tools_dir)):
        tool_py = os.path.join(tools_dir, entry, 'tool.py')
        if not os.path.isfile(tool_py):
            continue
        try:
            mod = _load_module(tool_py, f'mcp.tools.{entry}')
            total += _register_module(mod, f'builtin/{entry}')
        except Exception as e:
            logger.error(f"[loader] Failed to load builtin tool '{entry}': {e}", exc_info=True)
    logger.info(f"[loader] {total} built-in tool(s) registered")
    return total


def load_custom_tools():
    """Scan /app/data/custom_tools/<name>/tool.py and register custom tools."""
    custom_dir = os.path.join(DATA_DIR, 'custom_tools')
    os.makedirs(custom_dir, exist_ok=True)
    total = 0
    for entry in sorted(os.listdir(custom_dir)):
        tool_py = os.path.join(custom_dir, entry, 'tool.py')
        if not os.path.isfile(tool_py):
            continue
        try:
            mod = _load_module(tool_py, f'custom_tools.{entry}')
            total += _register_module(mod, f'custom/{entry}', custom=True)
        except Exception as e:
            logger.error(f"[loader] Failed to load custom tool '{entry}': {e}", exc_info=True)
    if total:
        logger.info(f"[loader] {total} custom tool(s) registered")
    return total
