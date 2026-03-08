# Workspace skills

Custom skills placed here override bundled/managed skills with the same name. The gateway loads this directory when `workspace` is mounted.

## Example: `hello-world`

This repo includes a minimal skill at **`hello-world/`**. It only needs a `SKILL.md` with YAML frontmatter (`name`, `description`) and Markdown instructions. When the user asks for a greeting, the agent will use this skill to respond. Restart the gateway (or wait for the skills watcher) and ask the agent for a greeting to try it.

## Adding another skill

1. Create a subfolder (e.g. `my-skill/`) with a **SKILL.md** file. Use YAML frontmatter for `name` and `description`, then add instructions in Markdown (see [Creating skills](https://docs.openclaw.ai/tools/creating-skills)).
2. Optionally add scripts or a `package.json` if the skill needs to run code.
3. No need to add it to `allowBundled` — workspace skills are loaded with highest precedence.
4. Restart the gateway or wait for the skills watcher to pick up changes.

Bundled skills are configured in `config/openclaw.json` under `skills.allowBundled` and `skills.entries`.
