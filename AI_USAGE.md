# AI usage disclosure

This file records AI assistance used during the assignment. Review it and correct anything that does not match your experience before submitting.

## Tools used

- **ChatGPT (OpenAI):** planning, initial Django implementation, code and security review, optimization, documentation, and verification support.
- **GitHub Copilot:** reviewed the partial project and added database constraints and model-validation tests. Its work stopped when the monthly credit limit was reached.
- **Claude (Anthropic):** completed the project from the partial source and assignment requirements, adding the placement heuristic, JSON endpoint, management command, tests, CI workflow, and documentation.

## Prompts given

These are concise summaries, not verbatim copies of every prompt:

- **ChatGPT:** asked to translate the assignment into an implementation plan and build a small Django project with models, recommendation logic, tests, README, AI disclosure, and test output. The prompt explicitly reserved the chat transcript and personal learning reflection for the human.
- **GitHub Copilot:** provided the assignment and project, then asked it to inspect requirements, run and fix checks/tests, update documentation, and leave the transcript and reflection to the human. Copilot stopped before completing verification because its credit limit was reached.
- **Claude:** provided the assignment and partially completed project and asked it to finish the work. Claude returned a completed project ZIP and a summary of its additions and verification.
- **ChatGPT follow-ups:** asked it to inspect Claude's ZIP, review packing edge cases and security, optimize where appropriate, run the final tests, prepare the README and AI usage disclosure, and provide a submission checklist. After the security findings were reported, I asked it to make the needed changes.
- **Final Claude ZIP review:** ChatGPT rechecked the newer ZIP, ran checks and tests, tried `seed_demo` and `recommend_box DEMO-1`, and refreshed the final verification output.

## Output accepted

- Django models for products, shipping boxes, orders, and order items, including field validators and database constraints.
- A deterministic low-cost-first recommendation service that checks weight and volume and attempts a non-overlapping 3D placement of every unit with axis-aligned rotations.
- A JSON recommendation endpoint, management command, tests, README, CI workflow, and recorded test output.
- Security hardening for non-debug operation: environment-based secret/host/token settings, security and CSRF middleware, bearer-token protection when configured, and startup checks requiring a secret and token when `DEBUG=False`.
- Small packing optimizations: remove duplicate candidate points, reject individually oversized units early, and try candidate boxes in recommendation order.

## Output rejected or modified

- The original volume-only recommendation was replaced because it could accept a box where the products could not physically be arranged together.
- Copilot used `CheckConstraint(condition=...)`, which is incompatible with the project's pinned Django 4.2 API. It was changed to `check=...`, and the migration was generated with Django 4.2.28.
- The extreme-point packing heuristic is retained with its limitation documented: it only reports success when it finds a valid layout, but can miss a feasible layout and therefore recommend a larger box.
- AI was not used to create, edit, summarize, or reconstruct the required chat transcript or the personal learning reflection. Those remain for me to produce independently.

## Mistakes and limitations found

- The initial volume-only approach did not prove that multiple products could fit together; it was replaced with an explicit placement attempt.
- Copilot's constraint keyword did not match Django 4.2 and required correction.
- Earlier verification notes referred to older versions and fewer tests. The completed project was rerun against Django 4.2.28 and its current 28-test suite; see `TEST_OUTPUT.md`.
- The packing heuristic is not complete and does not model padding, fragile products, orientation labels, non-rectangular products, or weight distribution. It has not been validated against real warehouse data.

## Verification performed

Using Python 3.11.9 and Django 4.2.28, I ran:

- `python manage.py check` — no issues.
- `python manage.py makemigrations --check --dry-run` — no changes detected.
- `python manage.py test` — all 28 tests passed under local development settings and under non-debug settings with test-only secret and API token values.
- Under non-debug settings, `python manage.py seed_demo` created its sample data and `python manage.py recommend_box DEMO-1` returned the expected `Medium` box recommendation.

A separate local benchmark placed 100 unit cubes in 0.011 seconds. This is one measurement, not a performance guarantee. GitHub Actions is configured but has not run on GitHub because the repository has not yet been pushed.

## Additional Claude session (finishing pass)

- **Prompt (summary):** gave Claude the near-complete project ZIP and the assignment and asked to complete the remaining work.
- **Accepted:** a randomized soundness test for the packer (seeded; checks bounds, no overlaps, and that placed units match the input), a `seed_demo` management command, and README count/usage updates.
- **Mistake by the AI:** its first `seed_demo` test expected order DEMO-1 (two 10x8x12 mugs) to fit the "Small" 15x12x10 box. That was wrong, since two mugs need 16 cm along some axis. The code was right; the test expectation was fixed to "Medium".
- **Verification:** reran `check`, `makemigrations --check`, and the full suite (28 tests) under dev and non-debug settings; separately ran a 20,000-case random fuzz of the packer with 9,025 successful layouts and 0 invalid ones.
- **Not done by AI:** the chat transcript and `LEARNINGS.md` are left for you.
