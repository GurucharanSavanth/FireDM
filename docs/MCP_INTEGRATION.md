# MCP Integration Guide

## Overview

FireDM supports Model Context Protocol (MCP) servers for extending capabilities through structured data access and tool usage. This guide covers available MCP servers, usage patterns, and troubleshooting.

## Available MCP Servers

### 1. Filesystem Server
**Purpose:** Read/write file system operations  
**Use Cases:**
- Inspect local download archives
- Validate post-processing output paths
- Query plugin manifest files

**Example:**
```python
# Via CLI plugin hook
def on_download_complete(self, d):
    # Plugin can request filesystem access to verify final file
    return True
```

### 2. Context7 Server
**Purpose:** Codebase semantic search and navigation  
**Use Cases:**
- Discover plugin interfaces and hooks
- Find usage examples of download pipeline
- Inspect test coverage for features

### 3. Puppeteer Server
**Purpose:** Browser automation (headless rendering and extraction)  
**Use Cases:**
- Test JavaScript-heavy media sites
- Verify yt-dlp extractor compatibility
- Validate DASH/HLS stream list parsing

### 4. PostgreSQL Server
**Purpose:** Structured query execution (if local DB available)  
**Use Cases:**
- Not currently used; reserved for future telemetry/logging schemas

### 5. Python REPL Server
**Purpose:** Execute Python code in sandboxed environment  
**Use Cases:**
- Validate plugin code logic before deployment
- Test edge cases in extractor chain
- Prototype new download pipeline features

## Usage Patterns

### Pattern 1: Plugin Manifest Discovery
```python
# Plugin wants to inspect other plugins safely
from firedm.plugins import PluginRegistry

meta_list = PluginRegistry.get_plugin_list()
for meta in meta_list:
    print(f"{meta.name}: {meta.description}")
```

### Pattern 2: Validate External Tool Paths
```python
# Plugin needs to locate ffmpeg without blocking
from firedm.tool_discovery import discover_tool

ffmpeg_path = discover_tool("ffmpeg")
if ffmpeg_path:
    # Tool found; safe to proceed
    pass
```

### Pattern 3: Sandbox Code Validation
Use the Python REPL server to test extraction logic in isolation before enabling a plugin:
```bash
# Example: test yt-dlp extractor compatibility
python -c "
import yt_dlp
with yt_dlp.YoutubeDL() as ydl:
    info = ydl.extract_info('https://example.com/video', download=False)
    print(info['format'])
"
```

## Troubleshooting

### MCP Server Connection Failures

**Symptom:** "MCP server unavailable" error  
**Diagnosis:**
1. Verify server is running: `netstat -an | findstr :PORT` (Windows) or `lsof -i :PORT` (Linux)
2. Check firewall rules: MCP servers default to localhost loopback
3. Verify Python environment has required MCP client library installed

**Fix:**
```powershell
.\.venv\Scripts\python.exe -m pip install mcp-client
```

### Timeout Errors on Puppeteer Operations

**Symptom:** Browser automation times out  
**Diagnosis:**
1. Verify Deno is installed: `deno --version`
2. Check firewall allows external network access (if testing remote sites)
3. Inspect browser console logs: enable debug logging in download settings

**Fix:**
```bash
# Deno installation
choco install deno  # Windows
# or
brew install deno   # macOS
```

### Plugin Manifest Sync Issues

**Symptom:** Plugin appears in registry but not in UI manifest  
**Diagnosis:**
1. Run manifest discovery in test mode: `python -m firedm.plugins.manifest`
2. Check blocked_plugin_reason() returns empty string for plugin
3. Verify plugin class has valid META attribute

**Fix:**
```python
from firedm.plugins.manifest import discover_plugin_manifest
section = discover_plugin_manifest(scan=True)
print(f"Blocked plugins: {[e.plugin_id for e in section.blocked]}")
```

## Configuration

### Enable User Plugins (Unsafe)
User plugins are **disabled by default**. To enable with explicit allowlist:

```python
# In firedm/config.py or settings UI
allow_user_plugins = True
plugin_dir = "~/.firedm/plugins"
```

### Set MCP Server Timeout
```python
# Default is 30 seconds per MCP call
mcp_timeout_seconds = 60
```

## Best Practices

1. **Always validate plugin code** before enabling: use Python REPL to check syntax and imports
2. **Limit plugin scope**: plugins run in main thread; long operations block UI
3. **Test with mock data**: use fixtures, not real downloads, in plugin development
4. **Document hook contracts**: each plugin hook has expected arguments and return types
5. **Use blocked_plugin_reason()** before shipping: check security review results

## See Also

- `firedm/plugins/registry.py` — Hook dispatcher and lifecycle
- `firedm/plugins/policy.py` — Plugin blocking rules
- `docs/architecture/ENGINE_PLUGIN_SYSTEM.md` — Plugin design doc
