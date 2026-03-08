# AGENTS — Operating instructions

How this agent should behave and use its tools. Loaded at the start of every session.

## Behavior

- Follow the personality and values in SOUL.md.
- Use the default model (google-vertex/gemini-2.0-flash) unless overridden.
- For simple prompts (e.g. “Reply with exactly: OK Carnitas”), respond with exactly what is asked.

## Memory and workspace

- The workspace is the agent’s working directory. File tools resolve relative paths against it.
- Do not commit secrets or credentials into the workspace; use placeholders if needed.
