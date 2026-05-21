# CoachPrash: Google Slides Generation with Claude Code
### Complete Setup Guide — May 2026

---

## Overview

This guide walks you through wiring **Claude Code in VSCode** to **Google Slides** so you can
generate branded, content-rich lesson decks with a single prompt. The stack uses:

- **Google Workspace CLI (`gws`)** — the official Google-released CLI for all Workspace APIs
- **`gws-mcp-server`** — a community MCP wrapper that exposes a curated, Claude-friendly subset of tools
- **Claude Code** — running inside your existing `CoachPrash` VSCode project
- **A `CLAUDE.md` brand file** — your persistent "deck DNA": colors, fonts, layout rules, tone

> **⚠️ Architecture note (important):** The original built-in MCP server in `gws` was removed in v0.8.0
> because it exposed 200–400 tools to Claude, causing context bloat. The correct 2026 path is the
> community `gws-mcp-server`, which exposes only the tools you need.

---

## Phase 1: Prerequisites Checklist

Before starting, confirm you have these:

| Requirement | Check |
|---|---|
| Node.js 18+ installed | `node --version` |
| Claude Code installed globally | `claude --version` |
| A Google account (personal Gmail is fine) | — |
| Access to [Google Cloud Console](https://console.cloud.google.com) | — |
| VSCode open with `CoachPrash` project | — |

---

## Phase 2: Google Cloud Project Setup (~20–30 min, one-time)

This is the most involved part. Do it carefully and you'll never touch it again.

### Step 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top left) → **New Project**
3. Name it `coach-prash-automation` → **Create**
4. Make sure this new project is selected in the dropdown

### Step 2: Enable Required APIs

In the left sidebar go to **APIs & Services → Library**. Search for and enable each of these:

- **Google Slides API** ← most important for you
- **Google Drive API** ← needed to save/list presentations
- **Google Docs API** ← useful for reference content
- **Google Sheets API** ← optional, useful for tracking content

> After enabling each one, wait ~30 seconds before testing. Google propagates these with a small delay.

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth 2.0 Client ID**
3. If prompted to configure the consent screen:
   - Choose **External** (fine for personal use)
   - App name: `CoachPrash Automation`
   - Add your Gmail as both developer and test user
   - Scopes: add `Google Drive API`, `Google Slides API`, `Google Docs API`
4. Back at Create Credentials → Application type: **Desktop app**
5. Name: `claude-code-desktop`
6. Click **Create** → note your **Client ID** and **Client Secret** (or download the JSON)

---

## Phase 3: Install the CLI and MCP Server

Open a terminal (inside or outside VSCode — both work):

### Step 4: Install `gws` globally

```bash
npm install -g @googleworkspace/cli
```

Verify:
```bash
gws --version
```

### Step 5: Authenticate `gws`

Set your credentials as environment variables first. On **macOS/Linux**:

```bash
export GOOGLE_WORKSPACE_CLI_CLIENT_ID="your-client-id-here"
export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="your-client-secret-here"
```

On **Windows (PowerShell)**:
```powershell
$env:GOOGLE_WORKSPACE_CLI_CLIENT_ID="your-client-id-here"
$env:GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="your-client-secret-here"
```

On **Windows CMD**:
```cmd
set GOOGLE_WORKSPACE_CLI_CLIENT_ID=your-client-id-here
set GOOGLE_WORKSPACE_CLI_CLIENT_SECRET=your-client-secret-here
```

On **Windows (Git Bash)**:
```bash
export GOOGLE_WORKSPACE_CLI_CLIENT_ID="your-client-id-here"
export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="your-client-secret-here"
```

> **Windows users:** Skip `gws auth setup` — it has a known bug with Windows paths.
> Use `gws auth login` directly (next step).

Then authenticate:
```bash
gws auth login
```

A browser window will open. Log in with your Google account, grant all requested scopes.
Credentials are stored encrypted (AES-256-GCM) in your OS keyring.

### Step 6: Test the connection

```bash
gws drive files list --params '{"pageSize": 5}'
```

You should see a JSON list of your Drive files. If you get a 403 error, go back to the
Cloud Console and enable the missing API (it will tell you which URL to visit).

### Step 7: Install `gws-mcp-server`

```bash
npm install -g gws-mcp-server
```

---

## Phase 4: Wire into Claude Code (Your CoachPrash Project)

### Step 8: Configure MCP for your project

In the **root of your `CoachPrash` project folder**, create `.mcp.json`:

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "npx",
      "args": [
        "gws-mcp-server",
        "--services",
        "drive,slides,docs"
      ],
      "env": {
        "GOOGLE_WORKSPACE_CLI_CLIENT_ID": "your-client-id-here",
        "GOOGLE_WORKSPACE_CLI_CLIENT_SECRET": "your-client-secret-here"
      }
    }
  }
}
```

> Only expose the services you need (`drive,slides,docs`). Adding everything (`gmail,calendar,...`)
> burns your MCP tool budget unnecessarily.

### Step 9: Verify Claude Code sees the MCP server

In your terminal, from the `CoachPrash` project root:

```bash
claude mcp list
```

You should see `google-workspace` listed. If not:
```bash
claude mcp test google-workspace
```

This will show any connection errors. Common fix: make sure the env vars with your credentials
are set in the same shell session, or hardcode them temporarily in `.mcp.json`.

---

## Phase 5: Create Your Brand File (`CLAUDE.md`)

This is your "deck DNA" — Claude Code reads this file automatically at the start of every session
in your project. It makes every deck follow your CoachPrash brand without you having to repeat
yourself.

### Step 10: Create `CLAUDE.md` in your project root

```markdown
# CoachPrash — Claude Code Project Instructions

## Project Purpose
CoachPrash is an education coaching site for elementary, middle, and high school students.
All generated content should be age-appropriate, academically accurate, engaging, and original.
Do not copy from textbooks — synthesize and explain in your own words.

---

## Brand Identity

### Color Palette (matches Navy & Gold default theme)
- **Primary**: #1B365D (deep navy — sidebar, headings, text)
- **Secondary**: #B5121B (crimson — CTA banners, secondary buttons)
- **Accent**: #F4A100 (golden amber — highlights, progress bars)
- **Background**: #F0F4F8 (cool off-white — page background)
- **Text**: #1B365D (same as primary — readability)
- **Highlight**: #E8F4FD (light blue — for callout boxes)

### Typography
- **Slide titles**: Bold, large, sentence case (not ALL CAPS)
- **Body text**: Clean, readable, 18–24pt in actual slides
- **Avoid**: decorative/script fonts for body text

### Logo / Branding
- Always include "CoachPrash" in the presenter notes or title slide
- Use the tagline on title slides (update this with your actual tagline)

---

## Slide Deck Standards

### Layout Rules
- **Title slide**: Full-color background (navy), white title, amber subtitle
- **Content slides**: Off-white background, navy headings, amber section markers
- **Max bullet points per slide**: 4 (never cram more)
- **One big idea per slide** — if you have two, split into two slides
- **End every deck** with a "Key Takeaways" slide and a "Check Your Understanding" slide

### Content Quality Rules
- All content must be **original** — do not reproduce textbook text verbatim
- Use **analogies, examples, and real-world connections** the audience can relate to
- Vary **question types** on the Check Your Understanding slide (MCQ, short answer, diagram label)
- **Grade-appropriate language**: use vocabulary slightly above the student's level but always define new terms

### Deck Size by Grade Band
- **Elementary (K-5)**: 8–12 slides, large text, lots of visuals described, simple language
- **Middle (6-8)**: 12–16 slides, mix of explanation and practice
- **High School (9-12)**: 16–22 slides, can include more depth and nuance

---

## Slide Generation Workflow

When I ask you to generate a deck, follow these steps:

1. **Confirm**: restate the topic, grade level, and number of slides before building
2. **Outline first**: list all slide titles and ask me to approve before generating full content
3. **Generate slide-by-slide**: write the title, 3–4 bullet points, and presenter notes for each
4. **Create in Google Slides**: use the gws MCP tools to create the deck and save to Drive
5. **Report back**: share the Drive link when done

---

## Folder Structure in Google Drive
Save all decks to the folder: `CoachPrash / Decks / [Subject] / [Grade Band]`
Create subfolders if they don't exist.

Example path: `CoachPrash / Decks / Science / Middle School`
```

> **Customize everything in the Brand Identity section** — especially the hex codes and tagline.
> This file is the most important artifact in the whole system.

---

## Phase 6: Generate Your First Deck

### Step 11: Open Claude Code in VSCode

In your `CoachPrash` project terminal:

```bash
claude
```

You're now in an interactive Claude Code session with your CLAUDE.md loaded and your
Google Workspace MCP tools available.

### Step 12: Your first prompt

Start simple to test the full pipeline:

```
Create a Google Slides deck on "Introduction to Fractions" for 4th grade students.
Follow the CoachPrash deck standards. Start by giving me the slide outline first.
```

Claude Code will:
1. Read your `CLAUDE.md` brand file
2. Propose an outline
3. After your approval, generate full slide content
4. Use the MCP tools to create the presentation in Google Slides
5. Return a Drive link

### Step 13: Iterate with follow-up prompts

Once you're comfortable, you can get more specific:

```
Now generate a deck on "Newton's Three Laws of Motion" for 8th grade.
Use real-world examples like sports and everyday objects.
Make the Check Your Understanding slide have 2 multiple-choice and 1 diagram-label question.
```

---

## Phase 7: Reusable Prompt Templates

Save these in a `prompts/` folder in your project for quick reuse:

### Template: Standard Lesson Deck
```
Create a CoachPrash Google Slides deck on "[TOPIC]" for [GRADE LEVEL] students.
Subject area: [SCIENCE / MATH / ELA / HISTORY / etc.]
Key concepts to cover: [LIST 3-5 CONCEPTS]
Learning objective: By the end of this lesson, students should be able to [OBJECTIVE].
Special instructions: [ANY SPECIFIC REQUESTS]

Show me the outline first. Wait for my approval before generating the full deck.
```

### Template: Review / Test Prep Deck
```
Create a test prep review deck on "[UNIT TOPIC]" for [GRADE LEVEL].
Cover these subtopics: [LIST]
Include at least one practice problem slide per subtopic.
End with a full mixed-review "Check Your Understanding" slide with 5 questions.
```

### Template: Concept Introduction (Single Idea)
```
Create a focused 8-slide deck introducing the concept of "[CONCEPT]" to [GRADE LEVEL] students.
Assume students have NO prior knowledge. Build from the ground up.
Use at least 2 real-world analogies.
```

---

## Best Practices Summary

| Practice | Why It Matters |
|---|---|
| Always approve the outline before full generation | Saves tokens; avoids regenerating 20 slides |
| Keep `CLAUDE.md` updated as your brand evolves | It's read every session automatically |
| Use `/compact` in long Claude Code sessions | Reduces context bloat, saves tokens |
| Save prompt templates in `prompts/` folder | Consistent, repeatable deck quality |
| Test one API at a time when first setting up | Easier to debug 403 errors |
| Commit `.mcp.json` to your repo (without secrets) | Use env vars, not hardcoded credentials |
| Create Drive folders in advance | Cleaner organization from day one |

---

## Troubleshooting Quick Reference

| Error | Fix |
|---|---|
| `403 accessNotConfigured` | Enable the missing API in Cloud Console → wait 30s → retry |
| `gws auth setup` fails on Windows | Skip it; use `gws auth login` with env vars instead |
| `claude mcp list` doesn't show google-workspace | Check `.mcp.json` JSON syntax; run `claude mcp test google-workspace` |
| MCP tools not showing up in session | Restart Claude Code after editing `.mcp.json` |
| Slides created but wrong folder | Update the Drive folder path in `CLAUDE.md` |
| Content feels generic | Add more specifics to `CLAUDE.md`; use the detailed prompt templates |

---

## What's Next

Once this baseline is working, consider:

- **Batch generation**: Ask Claude Code to generate a full unit's worth of decks in one session
- **Template slide**: Create a "master" Google Slide template in Drive and tell Claude to copy it each time (preserves pixel-perfect branding)
- **Skills**: Run `npx skills add https://github.com/googleworkspace/cli/tree/main/skills/gws-drive` to give Claude Code pre-built knowledge of advanced Drive operations
- **Service account**: For fully headless/automated generation, set up a Google service account so no browser OAuth is needed

---

*Guide version: May 2026 | Based on gws v0.22+ and Claude Code with MCP*
