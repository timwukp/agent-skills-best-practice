# AWS Kiro Credit Estimation Guide

## The Problem

You need to know: **"How many Kiro credits will my team use this sprint?"**

You can't answer that without measurement, because credit costs depend on your Kiro
account, model, and the complexity of your code. The numbers in a README are just
samples -- your mileage will vary.

This guide gives you a simple system to measure your own costs and predict future ones.

---

## The Big Picture

The whole system works in 4 phases:

```
┌─────────────────────┐
│  1. BENCHMARK       │  One-time: run a simple sample test in Kiro.
│                     │  Record how many credits it cost.
│                     │  This is your "baseline" -- the cost of the
│                     │  easiest possible test on YOUR account.
└─────────┬───────────┘
          |
          v
┌─────────────────────┐
│  2. ESTIMATE        │  Before testing your real code, ask:
│                     │  "How much more complex is my code than the sample?"
│                     │  Multiply your baseline by that complexity score.
│                     │  Now you have a predicted cost.
└─────────┬───────────┘
          |
          v
┌─────────────────────┐
│  3. MEASURE         │  Run the skill on your real code.
│                     │  Record the actual credits used.
│                     │  Compare to your estimate.
└─────────┬───────────┘
          |
          v
┌─────────────────────┐
│  4. REFINE          │  Your actual measurements make future
│                     │  estimates more accurate.
│                     │  The more you measure, the better
│                     │  the predictions get.
└─────────────────────┘
```

That's it. The rest of this guide walks you through each phase.

---

## Phase 1: Measure Your Baseline (One-Time, ~10 Minutes)

A "baseline" is simply: **what does the cheapest, simplest test cost on my account?**

We provide sample prompts for you to paste into Kiro. You just note your credit balance
before and after.

### What You Need

- AWS Kiro CLI installed and authenticated
- Python 3.8+
- Your Kiro credit balance (check the Kiro dashboard or `/credits` in CLI)

### Run It

```bash
cd Skills-examples-javatest-UItest
python track_credits.py init
```

Then, for each category, start a **fresh Kiro conversation** and run the benchmark.
The tool shows you the prompt to paste and asks for your before/after balance:

```bash
python track_credits.py benchmark java-simple   # ~2 min
python track_credits.py benchmark api-simple     # ~2 min
python track_credits.py benchmark ui-simple      # ~2 min
```

### What Happens

For example, when you run `benchmark java-simple`:

1. The tool displays a prompt (a simple 20-line Java class)
2. You paste it into a fresh Kiro conversation
3. Kiro generates 3 unit tests
4. You enter your credit balance before (e.g., 2000.00) and after (e.g., 1999.81)
5. The tool calculates: **0.19 credits for 3 tests = 0.063 credits per test**

That 0.063 is your java-unit baseline.

### See Your Results

```bash
python track_credits.py baselines
```

Example output:
```
java-unit   : 0.0633 credits/test
api         : 0.0767 credits/test
ui          : 0.2100 credits/test
```

These three numbers are the foundation for everything else.

### Why "Fresh Conversation" Matters

Each message in a Kiro conversation includes all previous messages as context.
A 10-message conversation costs more per message than a 1-message conversation.
Starting fresh ensures you measure the true cost of a single generation task,
not the accumulated cost of a long conversation.

---

## Phase 2: Estimate Your Real Code

Your real code is more complex than a 20-line sample. A 200-line service with
mocking, branching, and annotations will cost more because:

- The AI reads more code (bigger input)
- The AI writes more test code (bigger output)
- The AI reasons about more scenarios (more computation)

### How Complexity Scoring Works

We score your code's complexity by counting things that make tests harder to generate:

| What to Count | How to Score | Why It Costs More |
|---------------|-------------|-------------------|
| Lines of source code | +1 for every 50 lines | AI reads more code |
| Mock dependencies | +1 for each mock | AI writes more setup/verify code |
| Branches (if/else/switch/try-catch) | +1 for every 3 branches | AI reasons about more paths |
| Framework annotations (@Entity, @Valid, etc.) | +1 for every 3 annotations | AI handles more framework patterns |
| JSON nesting depth (API tests) | +1 for each nesting level | AI generates deeper assertions |
| Dynamic UI elements (UI tests) | +2 for each dynamic element | AI handles state-dependent selectors |

The minimum score is always 1 (that's the benchmark sample itself).

### Example: Estimating a Real Class

Say you want to generate tests for `OrderService.java`:
- 200 lines of code
- 3 repository/service mocks
- 8 if/else branches
- 5 Spring annotations

Score it:

```
Start with:                           1
200 lines / 50 = 4, so add:        + 4
3 mocks, so add:                    + 3
8 branches / 3 = 3 (rounded up):   + 3
5 annotations / 3 = 2 (rounded up):+ 2
                                   ----
Complexity score:                    13
```

Now multiply:

```
Your java-unit baseline:    0.063 credits/test
Complexity score:           x 13
Number of tests:            x 3
                            --------
Estimated cost:             2.46 credits
Add 20% buffer for retries: 0.49
                            --------
Total estimate:             ~2.95 credits
```

### Use the Tool

You don't have to do the math yourself:

```bash
python track_credits.py estimate \
  --type java-unit \
  --source-lines 200 \
  --mocks 3 \
  --branches 8 \
  --annotations 5 \
  --tests 3
```

The tool uses your measured baselines automatically.

---

## Phase 3: Measure the Actual Cost

After you run the skill on your real code, record what it actually cost:

```bash
# 1. Check your credit balance (e.g., 1995.50)
# 2. Run the skill in a fresh Kiro conversation
# 3. Check your balance again (e.g., 1993.10)
# 4. Record it:

python track_credits.py add \
  "OrderService-placeOrder-3tests" \
  1995.50 \
  1993.10 \
  "3 JUnit5 tests, 200-line class, 3 Mockito mocks"
```

### Compare Estimate vs Actual

```
Estimated: 2.95 credits
Actual:    2.40 credits
Difference: -19% (estimate was a bit high -- that's fine, better safe than sorry)
```

If estimates are consistently off by more than 50%, re-run your benchmarks. The model
or pricing may have changed.

### Why Record Everything?

Every measurement you record feeds back into the baseline calculation. The tool averages
all your simple-case measurements to improve future estimates. After 10 measurements,
your estimates will be much more accurate than after 1.

---

## Phase 4: Plan Your Sprint Budget

Once you have baselines, you can estimate credit needs for a whole sprint.

### The Quick Way

```bash
python track_credits.py plan \
  --java-classes 10 \
  --api-endpoints 5 \
  --ui-flows 2 \
  --avg-complexity medium \
  --developers 5
```

Output:
```
Java unit tests: 10 classes x 3 tests x 0.063/test x 5x = 9.50 credits
API tests:       5 endpoints x 3 tests x 0.077/test x 5x = 5.75 credits
UI tests:        2 flows x 1 test x 0.21/test x 5x       = 2.10 credits

Subtotal:              17.35 credits
Fix iterations (20%):   3.47 credits
Safety margin (30%):    5.21 credits
TOTAL:                 26.03 credits
Per developer:          5.21 credits
```

### What "avg-complexity" Means

Since you can't score every class individually for sprint planning, we use a shorthand:

| Level | Multiplier | Typical Code |
|-------|------------|-------------|
| low | 2x baseline | Simple POJOs, getters/setters, no mocking |
| medium | 5x baseline | Typical services, 1-3 mocks, some branching |
| high | 10x baseline | Complex domain logic, many dependencies, deep nesting |

### What the Buffers Mean

- **Fix iterations (20%)**: About 1 in 5 generated tests needs a retry. Each retry
  costs roughly the same as the original generation. The skills cap retries at 2 per
  test to prevent runaway costs.

- **Safety margin (30%)**: Covers surprises -- a class that's more complex than
  expected, a model update that changes pricing, or an unusually long conversation.

### Per-Developer Budget Template

Fill this in with your measured baselines:

| Activity | Tests/Week | Your Cost/Test | Weekly Credits |
|----------|-----------|----------------|----------------|
| Unit tests (new features) | 15 | _____ | _____ |
| Unit tests (bug fixes) | 5 | _____ | _____ |
| API tests (new endpoints) | 6 | _____ | _____ |
| UI tests (critical flows) | 2 | _____ | _____ |
| Fix iterations (~20%) | -- | _____ | _____ |
| **Total per developer** | | | **_____** |

### Real-World Team Example

```
Team of 5 developers, 2-week sprint.
Each dev generates ~30 unit tests, 10 API tests, 3 UI tests per sprint.
Measured baselines: unit=0.07, api=0.08, ui=0.21

Per developer per sprint:
  Unit: 30 x 0.07                 = 2.10 credits
  API:  10 x 0.08                 = 0.80 credits
  UI:    3 x 0.21                 = 0.63 credits
  Fix iterations (20% of above):  = 0.71 credits
  Total per dev:                   ~4.24 credits/sprint

Team total:     5 x 4.24          = ~21.2 credits/sprint
Monthly:        2 sprints          = ~42.4 credits
With 30% safety:                   = ~55 credits/month
```

---

## Ongoing: Keep Your Estimates Accurate

### Record Usage After Each Session

```bash
python track_credits.py add "feature-X-unit-tests" <start> <end> "brief description"
```

### Check Weekly Burn Rate

```bash
python track_credits.py summary --period weekly
```

### Export for Team Review

```bash
python track_credits.py export   # creates credit-test-results.md
```

### Warning Signs

| What You See | What It Means | What to Do |
|-------------|---------------|-----------|
| A single test costs 5x your baseline | Class is very complex, or AI is looping | Break the class into smaller methods before testing |
| More than 2 fix retries per test | Environment/setup issue, not a test issue | Fix the build/config, then regenerate |
| UI test costs 10x+ a unit test | Normal -- UI tests are inherently more expensive | Only test critical user flows (login, checkout) |
| Actual costs consistently exceed estimates | Model or pricing changed | Re-run your benchmarks |

### When to Re-Benchmark

- Kiro updates the underlying AI model
- Kiro changes their credit pricing
- Your project switches frameworks (e.g., JUnit 4 to JUnit 5)
- Your codebase complexity changes significantly
- Every quarter as a routine check

---

## FAQ

**Q: Why are actual credits so different from what I expected?**

A: Credit costs depend on your specific Kiro account, model tier, and code complexity.
That's why we recommend measuring your own baselines rather than relying on anyone
else's numbers.

**Q: Should I budget based on my benchmark, or add extra?**

A: Always add 30-50% on top. Complex classes, fix retries, and long conversations all
add up in ways that are hard to predict exactly.

**Q: Do retries cost extra credits?**

A: Yes. When the AI retries a failing test, it sends the entire conversation history
again, so each retry costs at least as much as the original. This is why the skills
limit retries to 2 per test -- to prevent runaway costs.

**Q: Why do I need a "fresh conversation" for each benchmark?**

A: Each new message in a conversation includes all prior messages. In a long
conversation, later messages cost significantly more than earlier ones. Starting
fresh ensures you measure the true one-shot cost.

**Q: Can I use a cheaper model to save credits?**

A: If Kiro supports model selection, yes. Smaller models (like Haiku) cost less per
test but may produce lower quality tests that need more retries. Try benchmarking both
to find the right tradeoff.

**Q: What if my estimate is way off from actual?**

A: If you're consistently off by more than 50%, re-run your benchmarks. If the
complexity scoring seems wrong for your code patterns, adjust by running more benchmarks
with code that matches your typical complexity.

---

## Reference: Data Format

All measurements are stored in `credit-test-results.json`:

```json
{
  "test_date": "2026-03-10T08:14:35",
  "model": "claude-opus-4.6",
  "kiro_version": "1.x.x",
  "tests": [
    {
      "name": "Java-SimplePOJO-3tests",
      "start_credits": 2000.0,
      "end_credits": 1999.81,
      "credits_used": 0.19,
      "category": "java-unit",
      "complexity_score": 1,
      "test_count": 3,
      "source_lines": 20,
      "timestamp": "2026-03-10T08:19:13",
      "notes": "Baseline benchmark"
    }
  ]
}
```

The more entries you add, the better the tool's estimates become.
