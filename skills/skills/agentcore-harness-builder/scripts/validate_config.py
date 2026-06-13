#!/usr/bin/env python3
"""Validate a harness.json (and optionally a SKILL.md) against AgentCore best-practice rules.

Runs entirely OFFLINE — no AWS calls. Catches the mistakes that otherwise only surface as a
rejected create_harness / update_harness or a failed session start. Run this before every deploy.

Usage:
    python validate_config.py --config harness.json
    python validate_config.py --config harness.json --skill path/to/SKILL.md

Exit code 0 = no errors (warnings allowed); non-zero = at least one error.
"""
import argparse
import json
import re
import sys

ERRORS: list[str] = []
WARNINGS: list[str] = []


def err(msg: str) -> None:
    ERRORS.append(msg)


def warn(msg: str) -> None:
    WARNINGS.append(msg)


# Tool type -> the config union key that actually wires it
TOOL_CONFIG_KEY = {
    "agentcore_browser": "agentCoreBrowser",
    "agentcore_code_interpreter": "agentCoreCodeInterpreter",
    "agentcore_gateway": "agentCoreGateway",
    "remote_mcp": "remoteMcp",
    "inline_function": "inlineFunction",
}
# Tool type -> glob you'd expect in allowedTools so the agent can actually call it
TOOL_GLOB_HINT = {
    "agentcore_browser": "browser_*",
    "agentcore_code_interpreter": "code_interpreter*",
}


def validate_model(cfg: dict) -> None:
    model = cfg.get("model")
    if not model:
        err("model: missing. Provide {'bedrockModelConfig': {'modelId': '...'}}.")
        return
    bm = model.get("bedrockModelConfig", {})
    model_id = bm.get("modelId")
    if not model_id:
        err("model.bedrockModelConfig.modelId: missing.")
        return
    if not (model_id.startswith(("global.", "us.", "eu.", "apac.")) or "inference-profile" in model_id):
        warn(f"model.modelId '{model_id}' looks like a bare foundation-model id; prefer an "
             "inference-profile id (global.* / us.*) for cross-region capacity.")


def validate_system_prompt(cfg: dict) -> None:
    sp = cfg.get("systemPrompt")
    if not sp:
        err("systemPrompt: missing.")
        return
    if not isinstance(sp, list):
        err("systemPrompt: must be a LIST of content blocks, e.g. [{'text': '...'}], not a bare string.")
        return
    if not any(isinstance(b, dict) and b.get("text") for b in sp):
        err("systemPrompt: no block contains non-empty 'text'.")


def validate_tools(cfg: dict) -> None:
    tools = cfg.get("tools", [])
    allowed = cfg.get("allowedTools", [])
    if not isinstance(allowed, list):
        err("allowedTools: must be a list of glob strings.")
        allowed = []
    if tools and not allowed:
        err("allowedTools: empty but tools are declared — the agent will see nothing. "
            "Add globs like ['browser_*','code_interpreter*','skills'].")
    for i, t in enumerate(tools):
        ttype = t.get("type")
        name = t.get("name", f"<tool[{i}]>")
        if ttype not in TOOL_CONFIG_KEY:
            warn(f"tools[{i}] '{name}': unrecognized type '{ttype}'. Known: {sorted(TOOL_CONFIG_KEY)}.")
            continue
        # config is documented-optional but practically required to wire
        if "config" not in t or not t["config"]:
            err(f"tools[{i}] '{name}' (type {ttype}): missing 'config'. Without it the tool is stored "
                f"but NOT wired — the agent can't use it. Add config.{TOOL_CONFIG_KEY[ttype]}.")
        else:
            if TOOL_CONFIG_KEY[ttype] not in t["config"]:
                err(f"tools[{i}] '{name}': config present but missing the '{TOOL_CONFIG_KEY[ttype]}' key "
                    f"that matches type '{ttype}'.")
        # allowedTools glob coverage for built-in tools
        hint = TOOL_GLOB_HINT.get(ttype)
        if hint and "*" not in "".join(allowed):
            # only warn when no globs at all are present
            warn(f"tools[{i}] '{name}': allowedTools has no glob; built-in tools need a glob like "
                 f"'{hint}' (the plain name '{name}' will NOT match and is filtered out).")
    # plain-name-without-glob trap
    for a in allowed:
        if a in ("browser", "code_interpreter"):
            err(f"allowedTools entry '{a}': plain name does not match declared built-in tool primitives. "
                f"Use a glob: '{a}_*' or '{a}*'.")


def validate_skills(cfg: dict) -> None:
    skills = cfg.get("skills", [])
    for i, s in enumerate(skills):
        sources = [k for k in ("git", "s3", "path") if k in s]
        if len(sources) != 1:
            err(f"skills[{i}]: must have EXACTLY ONE source of git/s3/path (found {sources or 'none'}).")
            continue
        src = sources[0]
        if src == "path":
            if not isinstance(s["path"], str):
                err(f"skills[{i}].path: must be a STRING (e.g. \"/skills/ui-testing\"), not an object.")
        elif src == "s3":
            if not isinstance(s["s3"], dict) or not s["s3"].get("uri"):
                err(f"skills[{i}].s3: must be {{'uri': 's3://bucket/prefix'}} (single 'uri', not bucket/prefix).")
        elif src == "git":
            g = s["git"]
            if "branch" in g:
                err(f"skills[{i}].git: has a 'branch' field — git source has NO branch field; it always "
                    "uses the repo default branch. Remove it.")
            if not g.get("url"):
                err(f"skills[{i}].git: needs 'url' (and usually 'path').")


def validate_limits_and_advanced(cfg: dict) -> None:
    for f in ("maxIterations", "maxTokens", "timeoutSeconds"):
        if f not in cfg:
            warn(f"{f}: not set. Set an explicit limit (recommended: maxIterations 100, maxTokens 65536, "
                 "timeoutSeconds 1800).")
        elif not isinstance(cfg[f], int):
            err(f"{f}: must be a plain integer (no optionalValue wrapper).")
    trunc = cfg.get("truncation")
    if trunc and isinstance(trunc, dict):
        if "slidingWindowMessagesCount" in trunc:
            err("truncation: 'slidingWindowMessagesCount' is not the real shape. Use "
                "config.slidingWindow.messagesCount, i.e. {'strategy':'sliding_window',"
                "'config':{'slidingWindow':{'messagesCount':150}}}.")
        if trunc.get("strategy") == "sliding_window":
            sw = trunc.get("config", {}).get("slidingWindow", {})
            if "messagesCount" not in sw:
                warn("truncation: sliding_window without config.slidingWindow.messagesCount (recommended ~150).")
    # network + lifecycle live under environment.agentCoreRuntimeEnvironment, NOT top-level
    if "network" in cfg:
        err("network: not a top-level field. It lives under "
            "environment.agentCoreRuntimeEnvironment.networkConfiguration.networkMode.")
    if "lifecycle" in cfg:
        err("lifecycle: not a top-level field. It lives under "
            "environment.agentCoreRuntimeEnvironment.lifecycleConfiguration "
            "{idleRuntimeSessionTimeout, maxLifetime}.")
    env = cfg.get("environment", {}).get("agentCoreRuntimeEnvironment", {}) if isinstance(cfg.get("environment"), dict) else {}
    if env:
        nc = env.get("networkConfiguration", {})
        if nc and not nc.get("networkMode"):
            err("environment...networkConfiguration: 'networkMode' is required (e.g. 'PUBLIC').")
    else:
        warn("environment.agentCoreRuntimeEnvironment not set; network mode + session lifecycle use defaults.")
    auth = cfg.get("authorizerConfiguration")
    if isinstance(auth, dict) and "type" in auth:
        err("authorizerConfiguration: there is no 'type' field. Omit it entirely for default IAM (SigV4); "
            "for JWT use {'customJWTAuthorizer': {'discoveryUrl': '...', 'allowedAudience': [...]}}.")


def validate_memory(cfg: dict) -> None:
    mem = cfg.get("memory")
    if not mem:
        return  # memory is optional
    acc = mem.get("agentCoreMemoryConfiguration")
    if not acc:
        err("memory: present but missing 'agentCoreMemoryConfiguration'.")
        return
    rc = acc.get("retrievalConfig", {})
    for ns, conf in rc.items():
        if "memoryStrategyId" in conf:
            err(f"memory.retrievalConfig['{ns}']: uses 'memoryStrategyId' — the correct field is 'strategyId'.")
        if "strategyId" not in conf:
            warn(f"memory.retrievalConfig['{ns}']: no 'strategyId' set (fill from CreateMemory response).")


def validate_skill_md(path: str) -> None:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        err(f"SKILL.md: cannot read '{path}': {e}")
        return
    if not text.startswith("---"):
        err(f"SKILL.md '{path}': MUST start with YAML frontmatter ('---' on line 1). Session start fails "
            "without it (undocumented requirement).")
        return
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        err(f"SKILL.md '{path}': frontmatter block not closed with a second '---'.")
        return
    fm = m.group(1)
    if not re.search(r"^name:\s*\S", fm, re.MULTILINE):
        err(f"SKILL.md '{path}': frontmatter missing 'name'.")
    if not re.search(r"^description:\s*\S", fm, re.MULTILINE):
        err(f"SKILL.md '{path}': frontmatter missing 'description'.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a harness.json against best-practice rules")
    ap.add_argument("--config", required=True, help="Path to harness.json")
    ap.add_argument("--skill", action="append", default=[], help="Path to a SKILL.md to validate (repeatable)")
    args = ap.parse_args()

    try:
        with open(args.config, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL  cannot load config '{args.config}': {e}")
        return 2

    # strip _-prefixed comment/note keys recursively so templates validate cleanly
    def _strip(o):
        if isinstance(o, dict):
            return {k: _strip(v) for k, v in o.items() if not k.startswith("_")}
        if isinstance(o, list):
            return [_strip(v) for v in o]
        return o
    cfg = _strip(cfg) if isinstance(cfg, dict) else cfg

    if isinstance(cfg, dict) and "harnessName" not in cfg:
        if "name" in cfg:
            warn("config uses 'name'; the real CreateHarness field is 'harnessName' "
                 "(create_harness.py maps it for you, but prefer 'harnessName').")
        else:
            warn("harnessName: not set (required by CreateHarness).")

    validate_model(cfg)
    validate_system_prompt(cfg)
    validate_tools(cfg)
    validate_skills(cfg)
    validate_limits_and_advanced(cfg)
    validate_memory(cfg)
    for sp in args.skill:
        validate_skill_md(sp)

    print(f"\nValidation of {args.config}")
    print("-" * 40)
    if ERRORS:
        print(f"ERRORS ({len(ERRORS)}):")
        for e in ERRORS:
            print(f"  ✗ {e}")
    if WARNINGS:
        print(f"WARNINGS ({len(WARNINGS)}):")
        for w in WARNINGS:
            print(f"  ! {w}")
    if not ERRORS and not WARNINGS:
        print("  ✓ no issues found")
    print("-" * 40)
    if ERRORS:
        print(f"RESULT: {len(ERRORS)} error(s) — fix before calling AWS.")
        return 1
    print("RESULT: OK" + (f" ({len(WARNINGS)} warning(s) to review)" if WARNINGS else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
