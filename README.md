# project-template

Starter template for new Bulzi-Org projects. Includes an `AGENTS.md` with coding standards, architecture conventions, and AI agent instructions that work across all major AI coding tools (Warp/Oz, Claude Code, GitHub Copilot, Cursor, Windsurf, and others).

## What's included

| File | Purpose |
|---|---|
| `AGENTS.md` | AI agent instructions — coding standards, architecture rules, project structure template, git workflow, and done criteria. Read automatically by 20+ AI tools. |
| `.gitignore` | Language-agnostic starter ignore file covering build artifacts, IDE files, secrets, runtime data, and common ecosystems (.NET, Node, Python, Docker). |

## Using this template

### Option 1: GitHub template repo (recommended)

This repo is configured as a **GitHub template repository**. Create a new project from it via the GitHub UI or CLI.

**GitHub web UI:**

1. Click the green **"Use this template"** button at the top of this repo.
2. Choose **"Create a new repository"**.
3. Fill in the repo name, visibility, and owner.
4. Click **"Create repository"**.
5. Clone locally and start filling in the `AGENTS.md` placeholders.

**GitHub CLI (`gh`):**

```bash
# Create a new private repo from the template and clone it
gh repo create Bulzi-Org/my-new-project \
  --template Bulzi-Org/project-template \
  --private \
  --clone

cd my-new-project
```

### Option 2: Shell function (local projects)

Add a shell function to create new projects with the template files automatically.

**Bash (~/.bashrc or ~/.bash_profile):**

```bash
new-project() {
  if [ -z "$1" ]; then
    echo "Usage: new-project <project-name>"
    return 1
  fi
  mkdir -p "$1" && cd "$1" && git init -b main
  cp ~/.project-templates/AGENTS.md ./AGENTS.md
  cp ~/.project-templates/.gitignore ./.gitignore
  git add -A && git commit -m "chore: scaffold from project-template"
  echo "Project '$1' created with AGENTS.md and .gitignore"
}
```

**PowerShell ($PROFILE):**

```powershell
function New-Project {
  param(
    [Parameter(Mandatory)][string]$Name
  )
  New-Item -ItemType Directory -Path $Name -Force | Out-Null
  Set-Location $Name
  git init -b main
  Copy-Item "$HOME/.project-templates/AGENTS.md" -Destination "./AGENTS.md"
  Copy-Item "$HOME/.project-templates/.gitignore" -Destination "./.gitignore"
  git add -A
  git commit -m "chore: scaffold from project-template"
  Write-Host "Project '$Name' created with AGENTS.md and .gitignore"
}
```

**Setup (one-time) — copy the templates to your home directory:**

```bash
# Bash / Linux / macOS
mkdir -p ~/.project-templates
cp AGENTS.md ~/.project-templates/AGENTS.md
cp .gitignore ~/.project-templates/.gitignore
```

```powershell
# PowerShell / Windows
New-Item -ItemType Directory -Path "$HOME/.project-templates" -Force
Copy-Item AGENTS.md -Destination "$HOME/.project-templates/AGENTS.md"
Copy-Item .gitignore -Destination "$HOME/.project-templates/.gitignore"
```

Then use it:

```bash
# Bash
new-project my-new-service
```

```powershell
# PowerShell
New-Project -Name my-new-service
```

### Option 3: AI cloud agents

When instructing an AI agent (Oz cloud agent, GitHub Copilot coding agent, etc.) to create a new project, include this in your prompt:

> Use the template repo `Bulzi-Org/project-template` as the starting point.
> Clone or copy its `AGENTS.md` and `.gitignore` into the new repo root.
> Fill in the `AGENTS.md` placeholders with the actual project details.

For **Oz cloud agents**, you can reference the template in your environment setup:

```bash
oz agent run-cloud \
  --env my-env \
  --prompt "Create a new .NET 10 project called 'my-service'. Use the template from Bulzi-Org/project-template as the starting point — copy AGENTS.md and .gitignore, then fill in the placeholders."
```

For **GitHub Copilot coding agent**, mention the template repo in your issue or prompt and Copilot will use it as a reference when scaffolding.

## After creating a new project

1. Open `AGENTS.md` and fill in the placeholders:
   - Replace `<build command>`, `<test command>`, etc. with real commands.
   - Update the **Tech stack** section for your actual stack.
   - Update the **Project structure** tree as you add directories.
2. Trim sections that don't apply and add project-specific rules.
3. Review `.gitignore` and add any project-specific patterns.
4. Commit: `git commit -am "chore: customize AGENTS.md for project"`

## Keeping templates in sync

When you update this template repo, existing projects won't automatically get the changes. To pull in updates:

```bash
# Add the template as a remote (one-time)
git remote add template https://github.com/Bulzi-Org/project-template.git

# Fetch and review changes
git fetch template
git diff main template/main -- AGENTS.md

# Cherry-pick or manually merge what you need
```

## License

See [LICENSE](LICENSE).
