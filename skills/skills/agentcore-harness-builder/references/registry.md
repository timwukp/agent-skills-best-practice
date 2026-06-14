# Agent Registry

The **AWS Agent Registry** (preview) is a centralized catalog for discovering and managing **agents, MCP servers,
tools, and skills** across an organization. Use it to make a finished harness (and its skills/tools) discoverable and
governed, rather than tribal knowledge.

## What it's for

- **Discover** resources org-wide via semantic search and filters.
- **Manage** agents, MCP servers, tools, and skills in one place.
- **Govern** what gets published through approval workflows and IdP-backed authorization.

## How it works (3 steps)

1. **Create a registry** — a centralized registry for the org's AI resources. Configure an **approval configuration**
   and integrate with your **identity provider** for authorization.
2. **Add records** — add agents, MCP servers, tools, and skills; submit them for approval per the configured workflow.
3. **Browse records** — search and discover with semantic search + filters.

A registry record carries: name, status, description, auth type, ARN, created/updated timestamps.

## When to use it in this workflow

Phase 8 (govern), after the harness is built, verified, and (ideally) evaluated/optimized:
- Publish the **harness/agent** so other teams can discover and reuse it.
- Publish reusable **skills** (e.g. a `ui-testing` skill) and **MCP servers/tools** so they're shared rather than
  re-implemented.
- Route publication through the **approval workflow** if your org requires review before a resource is broadly
  discoverable.

## Approval workflows

If you've also reviewed the *Kiro Service Approval Accelerator* material, the same principle applies: registry records
can require approval before they're visible/usable org-wide. Configure the approval configuration on the registry and
integrate the IdP so the right approvers authorize new records.

## API surface (verified, boto3 1.43.29)

Control plane: `CreateRegistry`, `GetRegistry`, `UpdateRegistry`, `DeleteRegistry`,
`CreateRegistryRecord`, `GetRegistryRecord`, `ListRegistryRecords`, `UpdateRegistryRecord`,
`UpdateRegistryRecordStatus`, `SubmitRegistryRecordForApproval`, `DeleteRegistryRecord`.
Data plane: `SearchRegistryRecords` (semantic search/discovery).

`CreateRegistry` input: `name` **[req]**, `description`, `authorizerType`, `authorizerConfiguration`,
`approvalConfiguration`, `clientToken`. Configure `authorizerType`/`authorizerConfiguration` to integrate your IdP and
`approvalConfiguration` to require approval before records are broadly discoverable. Re-introspect for record-shape
details before scripting:
```bash
python scripts/preflight.py --show-shape CreateRegistry --show-shape CreateRegistryRecord
```
Provide feedback to AWS via the console's feedback link, as the experience is evolving.
