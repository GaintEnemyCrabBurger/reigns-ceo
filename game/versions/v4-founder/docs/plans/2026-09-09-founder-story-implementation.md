# Founder Story Implementation Plan

**Goal:** Build an isolated, complete, replayable founder-story fork of the current V3 game.

**Architecture:** Keep the offline HTML build and swipe interaction. Extract the condition/weighted-draw/choice state machine into logic.js, shared by browser and deterministic simulation. Author the story in story.py, exporting the existing 22-column CSV plus a readable story manuscript. Rendering remains separate from game state.

**Tech Stack:** Vanilla JavaScript, HTML/CSS, Python standard library, Node.js standard library. No external network dependencies.

---

### Task 1: Isolate and document
Create versions/v4-founder from the current working files; preserve other dirty files. Document narrative decisions, source baseline, and build/run commands. Do not commit or publish.

### Task 2: Author a concrete world
Create story.py. Write two product promises, distinct recurring characters, expressive comic beats, weighted branching episodes, uncertain long bets, contextual finales and cross-company echoes. Export cards.csv and 故事手册.md. Verify each ending has a causal setup and each important choice has a later reader.

### Task 3: Share a deterministic state machine
Create logic.js with seeded random phase timing, weighted selection, run/legacy flags, resource consequences, bounded recovery, ending conditions and versioned save validation. Extend build.py for 22-column, condition, flag, placeholder and ending validation.

### Task 4: Let choices breathe
Adapt engine.js and index.html for the workshop identity, permanent left/right action buttons, untimed result beat, contextual milestone shelf, restart/continue controls and readable nonnumeric resource descriptions. Preserve substantial-swipe threshold and keyboard accessibility.

### Task 5: Audit and iterate
Create sim.py as the CLI entry for simulate.js, using the exact browser logic. Exercise random, balanced and characterful policies over seeded runs and multiple generations. Audit reachability, unanswered episodes, resource balance, option feedback, repeated cards and saved state. Run Python/Node syntax checks and git diff --check.

### Task 6: Visual and narrative review
Play both promises in the browser; inspect mobile and desktop screenshots, result reading, final report, next company and save restore. Revise weak writing and impossible causal combinations. Generate 玩.html and a concise delivery/QA record. Do not sync deployment mirrors without a separate publication request.
