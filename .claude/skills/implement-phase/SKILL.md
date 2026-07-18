---
name: implement-phase
description: Implements the next pending phase of the chess-web project from docs/TODO.md, acting as a senior engineer — confirms the real starting point against the code, implements the whole phase, writes and runs pytest tests, and only then checks the phase off in TODO.md. Use when the user asks to implement, continue, or advance the next phase/step of this project.
---

# Implement the next pending phase

You are acting as a senior software engineer on this repository. `docs/TODO.md`,
`docs/TECH_DESIGN.md`, and `docs/PRD.md` are the authoritative spec. Work one
phase at a time and never skip ahead.

Any argument passed to this skill (`$ARGUMENTS`) is the user's specific comments
or considerations **for this phase**. Treat them as binding constraints that
refine — but do not replace — the spec. If they contradict TECH_DESIGN.md or
TODO.md, stop and raise the conflict with the user instead of silently picking
one.

## 1. Establish the real starting point

Do not trust the checkboxes alone.

1. Read `docs/TODO.md` and find the last item marked `[x]` — note both the phase
   and the last completed step inside it.
2. Verify that claim against the actual repository: the files, functions,
   endpoints, and behaviour that step's *Verify* line promises must really
   exist. Read the code, not just the file names.
3. Also check the *first pending* step — it may already be implemented but left
   unchecked.
4. Resolve any mismatch before writing code:
   - Checked but missing/incomplete in the code → treat the phase as pending,
     and tell the user what you found.
   - Unchecked but genuinely complete and correct → say so, and check it off as
     part of this run.

State the confirmed starting point in one or two lines before continuing.

## 2. Pick and plan the phase

The target is the **next pending phase** (all of its remaining steps), not a
single step — unless the user's arguments explicitly scope it smaller.

Before coding, re-read the TECH_DESIGN sections the phase's steps reference so
the implementation matches the contract rather than an invented one. Pay
attention to the load-bearing rules in `CLAUDE.md`: server is the single source
of truth, the move list is the state (the board is replayed), one canonical
Game-State DTO, `chess_service.py` is the only module importing `python-chess`,
and errors use `{error:{code,message}}` with the documented statuses.

## 3. Implement

Implement every step of the phase completely, honouring each step's *Verify*
line as the acceptance criterion. All code, comments, and docs in English.
Follow the planned layout (`backend/`, `frontend/`, `tests/`) and match the
style of existing code once code exists.

## 4. Test with pytest

Write unit tests covering the new code, in `tests/` following TECH_DESIGN §8/§10
(`tests/test_chess_service.py` for engine logic, API tests via the Flask test
client). Cover the *Verify* assertions the phase's steps spell out, plus the
edge cases the spec calls out (all draw types, promotion pieces, illegal-move
errors).

Run them:

```bash
pytest                                   # full suite
pytest tests/test_chess_service.py -x    # focused, fail fast
```

For frontend-only phases (4–6) there is little to unit-test directly: still test
whatever backend surface the phase touches, and for the browser behaviour
perform the step's *Verify* manually (the `run` skill can launch the app) and
report what you observed. Never fabricate a passing check.

## 5. Iterate on failures — and know when to stop

When a test fails, read the code and find the actual cause. Fix and re-run;
iterate until green. Never weaken or delete a test to make it pass, and never
mark something green that isn't.

If the problem is **not** an implementation bug but a design/planning problem —
the approach doesn't cover what TODO.md or TECH_DESIGN.md asks for, the spec is
ambiguous or self-contradictory, or the step can't be satisfied as written —
**stop and tell the user**. Explain what you found, why it isn't a coding fix,
and what the options are. Do not guess your way past a spec problem.

## 6. Check off TODO.md

Only once the tests pass (and any manual verification genuinely succeeded):

- Change `- [ ]` to `- [x]` for every completed step of the phase.
- Do not check off steps you did not actually complete and verify.
- If a decision made during the phase changed the design, update
  `docs/TECH_DESIGN.md` (and `docs/PRD.md` if relevant) to keep the docs in sync.

## 7. Report

Close with a short summary in Spanish:

- confirmed starting point and any TODO.md/code mismatch found;
- the phase implemented and the files touched;
- the test command run and its result (paste the real output if it failed);
- anything raised for the user's decision;
- the next pending phase.

## 8. User review and commit to `develop`

Work happens on `develop` (see `CLAUDE.md` → Git branching). Do not commit
automatically:

1. Explicitly ask the user to review the code for this phase and confirm it's
   good before committing anything.
2. If the user requests changes, apply them, re-run the affected tests, and ask
   for confirmation again.
3. Once the user confirms, create a commit on `develop` whose message describes
   what was implemented in this phase (the phase name/number, the main pieces
   added, e.g. models, endpoints, tests). Stage only the files belonging to
   this phase's work — don't blindly add everything.
4. Report the commit hash and a one-line summary of what was committed.
