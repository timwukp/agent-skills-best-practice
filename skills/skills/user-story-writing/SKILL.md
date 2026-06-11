---
name: user-story-writing
description: >
  Writes and refines user stories for product backlogs: splits epics into INVEST-compliant stories,
  drafts Given/When/Then and EARS-format acceptance criteria, and runs definition-of-ready checks.
  Triggers on: "write user stories", "split this epic", "acceptance criteria for", "refine this
  story", "is this story ready", "turn these requirements into stories".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: secure-sdlc
---

# User Story Writing

Turn requirements, feature ideas, and epics into stories a team can estimate and deliver. The product is the story set, not prose about the feature.

## Story Format

```markdown
### [ID] [Title — verb phrase, outcome-oriented]
**As a** [specific user role — not "user"], **I want to** [action], **so that** [value the role actually cares about].

#### Acceptance Criteria
- Given [precondition], when [action], then [observable outcome]
- ...
```

For system-level or compliance-driven requirements where the persona format gets artificial, use EARS instead:

| EARS pattern | Template | Use for |
|--------------|----------|---------|
| Ubiquitous | The [system] shall [behavior] | Invariants |
| Event-driven | When [trigger], the [system] shall [behavior] | Responses to events |
| State-driven | While [state], the [system] shall [behavior] | Mode-dependent behavior |
| Unwanted behavior | If [undesired condition], then the [system] shall [behavior] | Error and abuse handling |
| Optional | Where [feature is included], the [system] shall [behavior] | Configurable capabilities |

## INVEST Check

Run every story against INVEST before delivering; fix violations rather than annotating them:

- **I**ndependent — schedulable without forcing another story into the same sprint
- **N**egotiable — captures intent, not implementation; the "how" stays open
- **V**aluable — the "so that" names value for the role; "so that the database is updated" fails
- **E**stimable — a developer could size it; unknowns extracted into spike stories
- **S**mall — fits comfortably in a sprint; otherwise split (see below)
- **T**estable — every criterion observable; "works correctly" fails

## Epic Splitting Patterns

Apply the first pattern that yields shippable slices:

1. **By workflow step** — each step of the user journey is a story (browse → select → pay → confirm).
2. **Happy path first** — story 1 is the simplest successful flow; error handling, edge cases, and limits follow as separate stories.
3. **By business rule** — base behavior first, each rule variation (discounts, regions, roles) its own story.
4. **By data variation** — support one input type first (e.g. domestic transfers), add types incrementally.
5. **CRUD split** — create first, then read/update/delete if each carries real value.

Never split by architectural layer — a "backend story" with nothing demonstrable is not a story.

## Definition of Ready

A story is ready for sprint planning when:

- [ ] Acceptance criteria cover the happy path AND at least one failure/edge path
- [ ] Dependencies identified (other stories, external teams, data)
- [ ] Security consideration noted where the story touches auth, money, or personal data (one line; use the security-story-writing skill for dedicated security stories)
- [ ] UX reference attached where there's a user interface
- [ ] Team can estimate it without a meeting-length discussion

## Guidelines

- Write criteria the QA engineer can execute verbatim. Vague criteria are deferred arguments.
- Keep the user role honest: if every story says "as a user", the personas were never real. Use the actual role names from the product.
- When given a batch of raw requirements, first group them into epics, present the grouping for confirmation, then split — don't generate 40 stories in one shot.
- Resist gold-plating: if a criterion doesn't trace back to the "so that", cut it.
