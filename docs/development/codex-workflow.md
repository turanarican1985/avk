# Codex Workflow

AVK development follows a stable-context workflow:

1. maintain a master project context that defines product language, architecture rules, and non-negotiable state boundaries
2. define bounded implementation phases in follow-up prompts
3. implement only the requested phase
4. avoid speculative future work unless the phase explicitly asks for it

## Why This Workflow Exists

The project has several easily conflated concerns such as legal verification, billing, moderation, review publication, website state, and support. A master context keeps those concerns visible while bounded phase prompts prevent overbuilding.

## Expected Behavior

- respect the shared `institution` model direction
- keep state families separate
- keep user-facing copy Turkish
- keep engineering documentation in English
- prefer clear module seams over quick shortcuts
- avoid implementing future workflows when the active phase does not require them

## Practical Rule

If a phase says bootstrap only, do bootstrap only. The repository should move forward through explicit layers rather than hidden scope expansion.

