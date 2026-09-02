# Enforcement — turning the SDLC gate from advisory into binding

`sdlc_gate.py` has always been able to decide correctly. What it lacked was the
**power to be invoked**. These two mechanisms give it that, at two different moments.

| | Local hook | CI |
|---|---|---|
| Moment | write time, one session | merge time, every change |
| Trigger | the agent calls a write tool | a pull request |
| Scope | this machine, this repo | anyone, any session, manual edits too |
| Failure posture | **fails OPEN** | **fails CLOSED** |
| Bypassable | yes (delete `.sdlc/`, disable the hook) | only by an admin removing the required check |

They are complements, not alternatives. The hook gives fast feedback and stops a
session drifting; CI is the thing that actually holds when the hook is missing,
disabled, or the change came from somewhere else entirely. **CI is the real gate.**

---

## 1. Local hook (`.kiro/hooks/`)

Per-repo, and it travels with the repo — the official Kiro hook format is read by
the IDE, the CLI, and KiroCrew.

```bash
# SKILL = wherever this skill is installed, e.g.
#   ~/.claude/skills/ai-native-sdlc  |  ~/.kiro/skills/ai-native-sdlc
SKILL=~/.claude/skills/ai-native-sdlc

mkdir -p .kiro/hooks .sdlc
cp "$SKILL"/templates/kiro-hooks/sdlc-gate.json .kiro/hooks/
echo "my-feature-slug" > .sdlc/active
```

Then create `intent/my-feature-slug/intent.md` and work the stages. Until
`plan.md` is accepted, a write to a source file is refused with the reason on
stderr, which the agent reads back.

**Facts worth knowing before you rely on it**

- `matcher: "write"` is an official built-in tool **category** (alongside `read`,
  `shell`, `web`, `spec`, `*`, and the `@mcp` / `@builtin` / `@powers` prefixes).
  It is not a regex over tool names. **KiroCrew's own global `~/.kiro/crew/hooks.json`
  is different**: its `matcher` is glob/regex/contains against the tool title, so
  there `"write"` matches only a tool literally named `write` — use `*write*` or an
  empty matcher on that path.
- Exit-code contract differs between runtimes, which is why the hook exits **2**:
  official Kiro blocks on *any* non-zero, while KiroCrew's ScriptHook blocks only
  on exactly 2 and treats other non-zero codes as a warning that still allows.
  `2` is the intersection that blocks on both.
- The STDIN payload's `hook_event_name` is **camelCase** (`preToolUse`) in official
  Kiro but PascalCase (`PreToolUse`) on KiroCrew's own path. The hook accepts both,
  casefolded. Getting this wrong does not error — it silently allows everything.
- **An infrastructure failure must exit 0, not block.** Because official Kiro blocks
  on any non-zero, a missing `python3`, an unexpanded `~`, or an uninstalled gate
  script would block *every write in the repo*, not merely disable the gate. The
  shipped command therefore guards both prerequisites and exits 0 when either is
  absent, and uses `"$HOME"` rather than `~`. `test_hook_config.py` asserts all
  three paths; the pre-hardening version failed them (exit 127 with no `python3`,
  exit 2 with the skill uninstalled).
- `PreToolUse` is available on IDE and CLI but **not on Web**, per the official
  surface table. On Web there is no local gate; CI is your only enforcement.
- The hook fails **open** by design. A crash must not stop you editing files.
- Keep the command fast. It is on the write path for every write tool call, and the
  official guidance is to keep command actions quick; the shipped timeout is 15s
  against a gate that normally returns in milliseconds.

## 2. CI (`.github/workflows/`)

CI cannot read `~/.kiro`, so the gate script is vendored into the repo:

```bash
SKILL=~/.claude/skills/ai-native-sdlc
mkdir -p .sdlc/scripts .github/workflows
cp "$SKILL"/scripts/sdlc_ci_gate.py .sdlc/scripts/
cp "$SKILL"/templates/github-workflows/sdlc-gate.yml .github/workflows/
```

**A green-or-red check is not a gate.** Until you make it required, a red X can
still be merged:

> Settings → Branches → branch protection rule on your default branch →
> *Require status checks to pass* → select **sdlc-gate**

What CI checks that the hook cannot:
- the **status ladder** is not skipped (an accepted `plan.md` demands a signed-off
  `spec.md`, which demands an accepted `intent.md`)
- no artifact is still the unfilled template placeholder
- every source file in the diff is covered by a fully accepted chain
- **every `evals/check_*.py` passes** — this is what makes "write the eval first,
  watch it fail, then implement" enforceable rather than a habit

### The optional `sdlc-review` job (Stage 5)

The workflow also carries an **advisory** second job that runs `REVIEW.md`'s passes
over the diff with `kiro-cli chat --no-interactive --trust-tools=read,grep`. Three
deliberate choices:

- It **self-skips** when there is no `KIRO_API_KEY` secret, so a repo without one
  does not see every PR fail. (API keys require Pro/Pro+/Pro Max/Power.)
- `--trust-tools=read,grep`, never `--trust-all-tools`: a reviewer reads, it never
  writes. This is the official least-privilege guidance.
- It is **not** a required check. Findings inform a human; the agent that wrote the
  code must not be the thing that passes it. Add it to branch protection only if you
  consciously accept an LLM in the merge path.

## Test coverage of the enforcement itself

Four suites, all runnable offline with stdlib only:

| Suite | Covers |
|---|---|
| `scripts/test_gate.py` | the stage-ordering decision |
| `scripts/test_pretooluse_hook.py` | the hook's allow/block logic, both event-name spellings, fail-open paths |
| `scripts/test_hook_config.py` | the **shipped JSON's command string** — the shell wrapper that actually runs |
| `sdlc_ci_gate.py` scenarios | ladder skips, placeholders, source coverage |

Honest note on method: only `test_hook_config.py` was written test-first (red →
green, with the red state proven against the previous config). The other three were
written after their implementation. Both bugs found so far — the template
placeholder parsing and the camelCase event name — show why that ordering matters:
a test written after the code tends to encode the same wrong assumption the code
made. `test_pretooluse_hook.py` originally passed while the hook was completely
inert under real Kiro, because the test sent the same wrong spelling the hook
checked for.

## What neither mechanism can do

Both check that the *process* was followed. Neither can judge whether an eval is
any **good**. A deliberately weak eval — one asserting that an id exists when the
requirement was that the element be reachable — passes both gates while proving
nothing. That failure has happened twice in this skill's own history, and it is
still a human review responsibility. `REVIEW.md` is where you write down the traps
so the next reviewer looks for them.

---

## Hardening (artifact schema 1)

Four defects were found by auditing the gates rather than by using them. Each is now
a rule the gate enforces and a test the mutation harness proves can fail.

**Coverage names the file.** The old rule asked only whether *some* accepted chain
existed anywhere in the repo, so one historical acceptance permanently satisfied it —
any later change passed. The gate now resolves `.sdlc/active`, requires *that*
intent's chain to be complete, and requires its `plan.md` to **name every changed
source file**. A repo with no `.sdlc/` directory still gets the old coarse rule, but
the output now says `coarse check only` instead of implying precision.

**Separation of duties is attested.** `Author` and `Accepted-by` are required on any
artifact claiming approval, and must differ (case- and whitespace-insensitive). This
is not cryptographic proof — someone can type two names — but the claim is committed,
reviewable and attributable, where before there was nothing but a sentence in a doc.

**The slug cannot escape the repo.** `.sdlc/active` is validated against
`^[A-Za-z0-9][A-Za-z0-9._-]*$`. Two real traversals were possible: `..` made
`root/intent/..` resolve back to the repo root — which *is* a directory, so it looked
valid — and an absolute slug like `/etc` made pathlib discard the prefix entirely.

**The schema is versioned.** `.sdlc/version` holds an integer; the gate refuses
outright when the repo declares a version newer than the gate understands, rather
than emitting findings derived from artifacts it may misparse.

### Two bugs found along the way

The value pattern used `\s*` around the captured group, and **`\s` matches
newlines** — so an artifact with an *empty* field value captured the **next line's**
text as its value. Confirmed in practice: an empty `Accepted-by:` returned
`- **Status:** accepted`. Both gates now use `[ \t]*` so a value cannot cross a line.

Separately, a missing `import re` made the hook raise `NameError`, which its
fail-open handler converted into a **silent allow** — every traversal slug passed.
Fail-open is deliberate (a buggy gate must not stop you editing files) but it turns a
crash into a permission, which is exactly why CI must fail *closed*.

### Mutation coverage caveat

The first mutation run after this work had four survivors, and none was a code bug —
each was an assertion too weak to distinguish the mutant. The instructive one: with
the traversal guard removed, a slug of `..` still *blocked*, because the repo root has
no artifacts in it. The test passed while the guard was gone. Asserting the exit code
was not enough; the test now asserts the **reason** in the message.

### Upgrading an existing repo

This is a **breaking change** for artifacts written before it. An accepted artifact
with no `Author` / `Accepted-by` is now a violation, so a repo that adopted the gate
earlier will go red until those fields are added. Add them to every artifact whose
status is `accepted` or `signed-off`, and make sure each plan lists the files its
change touched.
