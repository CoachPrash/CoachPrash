# CoachPrash Admin Manual

> **Version:** 3.0 (Phase 3)
> **Last Updated:** May 2026
> **Platform:** Flask + PostgreSQL, deployed on Railway

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Admin Dashboard](#2-admin-dashboard)
3. [Content Architecture](#3-content-architecture)
4. [Creating a New Course](#4-creating-a-new-course)
5. [Writing Content (Concepts)](#5-writing-content-concepts)
6. [Creating Problems & Quizzes](#6-creating-problems--quizzes)
7. [Bulk Import with qhsJSON](#7-bulk-import-with-qhsjson)
8. [Generating Content with Claude AI](#8-generating-content-with-claude-ai)
9. [Using Images (Railway Storage Bucket)](#9-using-images-railway-storage-bucket)
10. [Resources (Slides, Docs, Videos)](#10-resources-slides-docs-videos)
11. [Freemium Gating & Access Control](#11-freemium-gating--access-control)
12. [Managing Students](#12-managing-students)
13. [Access Codes](#13-access-codes)
14. [Blog & Resources Page](#14-blog--resources-page)
15. [Testimonials](#15-testimonials)
16. [Contact Messages](#16-contact-messages)
17. [SEO & Sitemap](#17-seo--sitemap)
18. [Security & Rate Limiting](#18-security--rate-limiting)
19. [Seeding & Demo Data](#19-seeding--demo-data)
20. [Deployment & Environment Variables](#20-deployment--environment-variables)
21. [Troubleshooting](#21-troubleshooting)
22. [Quick Reference](#22-quick-reference)

---

## 1. Getting Started

### Accessing the Admin Panel

1. Log in at `/auth/login` with your admin account
2. Navigate to `/admin/` or click **Admin** in the sidebar (gear icon)
3. All admin pages require the `admin` role — students see a 403 error if they try to access `/admin/*`

### Your Admin Account

The admin account is created during seeding. Default credentials (change immediately in production):

| Field | Default |
|-------|---------|
| Email | Value of `ADMIN_EMAIL` env var (default: `admin@coachprash.com`) |
| Password | Value of `ADMIN_PASSWORD` env var (default: `admin123`) |
| Role | `admin` |
| Tier | `premium` |

### Admin Navigation

The admin panel is accessible via the sidebar gear icon. Admin pages include:

| Page | URL | Purpose |
|------|-----|---------|
| Dashboard | `/admin/` | Overview stats and analytics |
| Content | `/admin/content` | Manage subjects, topics, concepts |
| Students | `/admin/students` | View and manage student accounts |
| Access Codes | `/admin/codes` | Generate and manage access codes |
| Blog | `/admin/blog` | Manage blog/resource posts |
| Testimonials | `/admin/testimonials` | Manage student testimonials |
| Messages | `/admin/messages` | Read contact form submissions |
| Resources | `/admin/resources` | Manage slides, docs, video links |
| Image Upload | `/admin/images` | Upload images to storage bucket |
| Bulk Import | `/admin/content/import` | Import content from JSON files |
| Changelog | `/admin/changelog` | View development history |

---

## 2. Admin Dashboard

The dashboard (`/admin/`) shows a real-time snapshot of your site:

### Stats Cards
- **Total Students** — registered student accounts
- **Premium Students** — students with `tier = premium`
- **Active Concepts** — published concept pages
- **Total Problems** — problems across all problem sets

### Recent Activity
- **Last 10 Registrations** — newest student accounts
- **Last 5 Contact Messages** — most recent messages (unread first)

### Practice Analytics
- **Attempts Today / This Week / Total** — problem attempt counts
- **Overall Accuracy** — percentage of correct attempts across all students
- **Top 5 Most-Attempted Problems** — your most popular practice content
- **Top 5 Hardest Problems** — lowest success rate (minimum 5 attempts to qualify)

---

## 3. Content Architecture

CoachPrash uses a four-level content hierarchy:

```
Subject (e.g., Mathematics)
  └── Topic (e.g., Algebra 1)
       └── Concept (e.g., Solving Linear Equations)
            └── Problem Set (e.g., Practice: One-Step Equations)
                 └── Problems (MCQ, Fill-in-Blank, or FRQ)
                      ├── Choices (for MCQ)
                      ├── Hints (progressive, 0-N per problem)
                      └── Solution (step-by-step, one per problem)
```

### What Each Level Does

| Level | Purpose | Student Sees |
|-------|---------|-------------|
| **Subject** | Top-level category (Math, Physics, etc.) | Subject catalog at `/subjects/` |
| **Topic** | A course within a subject (Algebra 1, AP Physics C) | Topic list at `/subjects/<slug>` |
| **Concept** | A single lesson/explainer (~5 min read) | Concept page with content + "Practice" button |
| **Problem Set** | A quiz attached to a concept | Quiz interface with timer, progress bar |
| **Problem** | An individual question (MCQ, fill-in, or FRQ) | Question with choices/input, hints, solution |

### Slugs

Every subject, topic, and concept has a **slug** — a URL-friendly identifier:

- Must be lowercase, use hyphens instead of spaces
- Subject slug is globally unique
- Topic slug is unique within its subject
- Concept slug is unique within its topic

Examples:
- Subject: `mathematics`
- Topic: `algebra-1`
- Concept: `solving-linear-equations`

The resulting URL would be: `/subjects/mathematics/algebra-1/solving-linear-equations`

### Display Order

Every level has a `display_order` field (integer, starting from 0). Lower numbers appear first. Use this to control the sequence students see when browsing content.

### Active/Inactive

Every level has an `is_active` boolean. Setting this to `false` hides the item from students without deleting it. Useful for draft content or seasonal topics.

---

## 4. Creating a New Course

To add a completely new course (e.g., "AP Chemistry"):

### Step 1: Create or Verify the Subject

Go to `/admin/content`. If the subject already exists (e.g., "Chemistry"), skip to Step 2.

To create a new subject:
1. Click **New Subject**
2. Fill in:
   - **Name**: `Chemistry` (display name)
   - **Slug**: `chemistry` (URL identifier)
   - **Description**: Brief description for the catalog page
   - **Icon**: An emoji like `🧪` (displayed in sidebar and catalog)
   - **Display Order**: Position among other subjects (0 = first)
   - **Is Active**: Check to make visible to students
3. Click **Save**

### Step 2: Create the Topic

1. From `/admin/content`, click **New Topic** under the relevant subject
2. Fill in:
   - **Name**: `AP Chemistry` (display name)
   - **Slug**: `ap-chemistry`
   - **Description**: What students will learn
   - **Difficulty Level**: Choose from: `elementary`, `middle_school`, `high_school`, `ap`, `college`
   - **Display Order**: Position within the subject
   - **Is Active**: Check when ready for students
3. Click **Save**

### Step 3: Add Concepts

For each lesson/explainer within the topic:
1. Click **New Concept** under the topic
2. Fill in:
   - **Title**: `Introduction to Atomic Structure`
   - **Slug**: `intro-atomic-structure`
   - **Content**: Write your lesson content (see [Section 5](#5-writing-content-concepts))
   - **Estimated Minutes**: Reading time (aim for 3-7 minutes)
   - **Access Tier**: `free` (first concept) or `premium` (subsequent concepts)
   - **Display Order**: Sequence within the topic
3. Click **Save**

### Step 4: Add Problems

You can add problems either:
- **Manually** via the admin forms (tedious for many problems)
- **Via Bulk Import** using the qhsJSON format (recommended — see [Section 7](#7-bulk-import-with-qhsjson))
- **Generated by Claude AI** (fastest — see [Section 8](#8-generating-content-with-claude-ai))

### Recommended Workflow

The fastest way to create a complete course:

1. Create Subject and Topic via the admin panel (Steps 1-2)
2. Use the Claude AI prompt template to generate a qhsJSON file with concepts + problems
3. Validate the JSON via `/admin/content/import` (click **Validate**)
4. Import the validated JSON (click **Import**)
5. Review imported content on the live site
6. Adjust access tiers and display orders as needed

---

## 5. Writing Content (Concepts)

Concept content is stored as HTML and rendered to students with KaTeX math support. You write content in the admin concept editor.

### LaTeX Math

Use KaTeX syntax for all mathematical notation:

| Type | Syntax | Example | Renders As |
|------|--------|---------|-----------|
| Inline math | `\( ... \)` | `The slope is \(m = 3\)` | The slope is *m* = 3 |
| Display math | `\[ ... \]` | `\[F = ma\]` | Centered equation on its own line |

Common LaTeX commands:
```
Fractions:    \(\frac{a}{b}\)
Exponents:    \(x^2\), \(x^{n+1}\)
Subscripts:   \(x_1\), \(a_{ij}\)
Square root:  \(\sqrt{x}\), \(\sqrt[3]{x}\)
Greek:        \(\alpha\), \(\beta\), \(\theta\), \(\pi\)
Vectors:      \(\vec{F}\)
Sum:          \(\sum_{i=1}^{n} x_i\)
Integral:     \(\int_0^1 f(x)\,dx\)
Inequality:   \(\leq\), \(\geq\), \(\neq\)
Multiplication: \(\times\), \(\cdot\)
```

### Callout Boxes

Use styled callout boxes to highlight important information:

```html
<div class="callout-key">
  <strong>Key Takeaway:</strong> A linear equation produces a straight
  line when graphed.
</div>

<div class="callout-warning">
  <strong>Common Mistake:</strong> Don't confuse velocity with speed —
  velocity includes direction!
</div>

<div class="callout-tip">
  <strong>Tip:</strong> When in doubt, check your units. They must
  match on both sides of the equation.
</div>
```

| Class | Color | Use For |
|-------|-------|---------|
| `callout-key` | Green border | Key takeaways, essential facts |
| `callout-warning` | Red border | Common mistakes, pitfalls |
| `callout-tip` | Blue border | Study tips, shortcuts, strategies |

### Code Blocks

For programming content (Computer Science), use HTML code blocks:

```html
<pre><code class="language-java">
int[] scores = {90, 85, 78, 92, 88};
for (int i = 0; i < scores.length; i++) {
    System.out.println(scores[i]);
}
</code></pre>
```

Do NOT use LaTeX for code — use `<pre><code>` tags.

### Content Structure Best Practices

A well-structured concept should follow this pattern:

1. **Introduction** — What the topic is and why it matters (1-2 paragraphs)
2. **Core Explanation** — The main lesson content with examples
3. **Worked Examples** — 1-2 fully worked problems showing the method
4. **Key Takeaway** — A `callout-key` box summarizing the main point
5. **Common Mistakes** — A `callout-warning` box about pitfalls (if applicable)

Keep each concept to approximately 5 minutes of reading time. Break longer topics into multiple concepts.

### KaTeX Preview

When editing a concept in the admin panel, click the **Preview** button below the content textarea to see how your LaTeX will render. This lets you catch syntax errors before saving.

### HTML Sanitization

All content HTML is automatically sanitized using the `nh3` library when saved. This strips potentially dangerous tags (like `<script>`) while preserving educational content tags. The following are preserved:

- Text formatting: `<p>`, `<strong>`, `<em>`, `<h1>`-`<h6>`, `<br>`, `<hr>`
- Lists: `<ul>`, `<ol>`, `<li>`
- Code: `<pre>`, `<code>` (with `class` attribute)
- Tables: `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`
- Media: `<img>` (with `src`, `alt`, `data-bucket-key`, `width`, `height`)
- Layout: `<div>`, `<span>` (with `class` attribute)
- Links: `<a>` (with `href`, `title`, `target`)
- Callout boxes: `<div class="callout-key">`, etc.

---

## 6. Creating Problems & Quizzes

Each concept can have one or more **Problem Sets** (quizzes). Each problem set contains individual **Problems**.

### Problem Types

| Type | Code | Student Interface | Grading |
|------|------|-------------------|---------|
| Multiple Choice | `mcq` | 4 clickable choice cards | Automatic — compares selected choice to `is_correct` flag |
| Fill in the Blank | `fill_in_blank` | Text input field | Automatic — case-insensitive comparison |
| Free Response | `frq` | Multi-line textarea | Self-graded — student compares to model answer |

### Multiple Choice (MCQ)

Each MCQ problem needs:
- **Question HTML**: The question text (supports LaTeX)
- **4 Choices**: Each with `text` and `is_correct` (exactly one must be `true`)
- **Difficulty**: `easy`, `medium`, or `hard`

Example:
```json
{
  "question_html": "<p>What is the slope of \\(y = 3x - 7\\)?</p>",
  "problem_type": "mcq",
  "difficulty": "easy",
  "choices": [
    {"text": "\\(7\\)", "is_correct": false},
    {"text": "\\(-7\\)", "is_correct": false},
    {"text": "\\(3\\)", "is_correct": true},
    {"text": "\\(-3\\)", "is_correct": false}
  ]
}
```

### Fill in the Blank

For fill-in-blank problems, specify the correct answer. Students type their answer and it's compared case-insensitively with whitespace stripped.

**Multiple accepted answers:** Use `||` to separate alternatives:
```json
{
  "question_html": "<p>Solve: \\(2x + 4 = 10\\). \\(x = \\) ?</p>",
  "problem_type": "fill_in_blank",
  "correct_answer": "3||x=3||x = 3",
  "difficulty": "easy"
}
```

All of `3`, `x=3`, `x = 3`, and `X = 3` would be accepted as correct.

### Free Response (FRQ)

FRQ problems are not auto-graded. Instead:
1. Student writes their response in a textarea
2. After submitting, the **model answer** is displayed
3. Student self-grades by clicking "Yes, I got it right" or "No, I got it wrong"
4. The self-grade counts toward their quiz score

```json
{
  "question_html": "<p>Explain why Newton's Third Law does not mean forces cancel out.</p>",
  "problem_type": "frq",
  "correct_answer": "Newton's Third Law states that forces come in pairs acting on different objects. The action and reaction forces do not cancel because they act on different objects, not the same object.",
  "difficulty": "medium"
}
```

The `correct_answer` field becomes the model answer shown to the student.

### Hints

Each problem can have multiple hints, revealed progressively:

```json
"hints": [
  {"text": "Think about what operation undoes addition.", "cost_points": 0},
  {"text": "Subtract 4 from both sides first, then divide.", "cost_points": 1}
]
```

- **`cost_points: 0`** — Free hint (available to all users)
- **`cost_points: 1`** — Premium hint (only premium users can reveal it)

Hint order matters — hints are revealed in the order listed. Write hints from general to specific:
1. First hint: A nudge in the right direction
2. Second hint: More specific guidance (but don't give away the answer)

### Step-by-Step Solutions

Each problem can have a solution with numbered steps:

```json
"solution_steps": [
  {"text": "Start with the equation \\(2x + 4 = 10\\)."},
  {"text": "Subtract 4 from both sides: \\(2x = 6\\)."},
  {"text": "Divide both sides by 2: \\(x = 3\\)."},
  {"text": "Check: \\(2(3) + 4 = 6 + 4 = 10\\) ✓"}
]
```

Solutions are displayed as an accordion — students click to reveal each step one at a time. Solutions are **premium-only** by default.

Each step should explain **why** that step works, not just show the mechanics. Think "coaching voice."

### Difficulty Guidelines

| Level | Description | Example |
|-------|-------------|---------|
| `easy` | Direct application of one concept | Solve \(x + 5 = 12\) |
| `medium` | Requires 2-3 steps or combining ideas | Solve \(3(x - 2) + 4 = 13\) |
| `hard` | Multi-step, requires insight or multiple concepts | Word problem requiring equation setup + solving |

Aim for a mix: ~40% easy, ~40% medium, ~20% hard.

---

## 7. Bulk Import with qhsJSON

The most efficient way to add content is via **bulk import** using the qhsJSON (Questions, Hints, Solutions JSON) format.

### How to Import

1. Go to `/admin/content/import`
2. Either:
   - **Paste JSON** into the textarea, or
   - **Upload a `.json` file**
3. Click **Validate** to check for errors
4. If valid, click **Import** to load into the database

### Prerequisites

Before importing, the **Subject** and **Topic** must already exist in the database. The JSON references them by slug:

```json
{
  "subject_slug": "mathematics",
  "topic_slug": "algebra-1",
  "concepts": [...]
}
```

If the subject or topic slug doesn't match an existing record, the import will fail with an error message.

### Complete qhsJSON Format

```json
{
  "subject_slug": "mathematics",
  "topic_slug": "algebra-1",
  "concepts": [
    {
      "title": "What is a Linear Equation?",
      "slug": "what-is-a-linear-equation",
      "content_html": "<h2>Understanding Linear Equations</h2><p>A <strong>linear equation</strong>...</p>",
      "content_raw": "Plain text version of the content",
      "estimated_minutes": 6,
      "access_tier": "free",
      "display_order": 0,
      "problem_sets": [
        {
          "title": "Practice: Identifying Linear Equations",
          "access_tier": "free",
          "display_order": 0,
          "problems": [
            {
              "question_html": "<p>Which of the following is a linear equation?</p>",
              "question_raw": "Which of the following is a linear equation?",
              "problem_type": "mcq",
              "difficulty": "easy",
              "points": 1,
              "choices": [
                {"text": "\\(x^2 + 3x = 10\\)", "is_correct": false},
                {"text": "\\(2x + 5 = 11\\)", "is_correct": true},
                {"text": "\\(\\sqrt{x} = 4\\)", "is_correct": false},
                {"text": "\\(\\frac{1}{x} + 2 = 5\\)", "is_correct": false}
              ],
              "hints": [
                {
                  "text": "A linear equation has the variable raised to the first power only.",
                  "cost_points": 0
                },
                {
                  "text": "Look for the equation where \\(x\\) appears with an exponent of exactly 1.",
                  "cost_points": 1
                }
              ],
              "solution_steps": [
                {"text": "A linear equation has the variable to the first power only."},
                {"text": "\\(x^2 + 3x = 10\\) has \\(x^2\\), so it's quadratic."},
                {"text": "\\(2x + 5 = 11\\) has \\(x\\) to the first power, so it is linear."}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Field Reference

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `subject_slug` | Yes | — | Must match existing subject |
| `topic_slug` | Yes | — | Must match existing topic under that subject |
| `concepts[].title` | Yes | — | Display title |
| `concepts[].slug` | No | Auto-generated from title | URL-friendly identifier |
| `concepts[].content_html` | No | `""` | Lesson content with LaTeX |
| `concepts[].content_raw` | No | `""` | Plain text version |
| `concepts[].estimated_minutes` | No | `5` | Reading time estimate |
| `concepts[].access_tier` | No | `"free"` | `"free"` or `"premium"` |
| `concepts[].display_order` | No | Index in array | Sort order |
| `problem_sets[].title` | Yes | — | Quiz title |
| `problem_sets[].access_tier` | No | `"free"` | `"free"` or `"premium"` |
| `problems[].problem_type` | No | `"mcq"` | `"mcq"`, `"fill_in_blank"`, or `"frq"` |
| `problems[].difficulty` | No | `"medium"` | `"easy"`, `"medium"`, or `"hard"` |
| `problems[].points` | No | `1` | Point value |
| `problems[].correct_answer` | Required for `fill_in_blank` | — | Use `\|\|` for multiple accepted answers |
| `choices[].text` | Yes (MCQ) | — | Choice text (supports LaTeX) |
| `choices[].is_correct` | Yes (MCQ) | — | Exactly one must be `true` |
| `hints[].text` | Yes | — | Hint text (supports LaTeX) |
| `hints[].cost_points` | No | `0` | `0` = free, `1` = premium |
| `solution_steps[].text` | Yes | — | Step explanation (supports LaTeX) |

### Validation Rules

The validator checks:
- `subject_slug` and `topic_slug` exist in the database
- Every concept has a `title`
- MCQ problems have a `choices` array
- Fill-in-blank problems have a `correct_answer`
- `problem_type` is one of: `mcq`, `fill_in_blank`, `frq`

### Idempotency Warning

The bulk import does **not** check for duplicate concepts. If you import the same JSON twice, you'll get duplicate concepts. The content loader utility (`load_content_json`) used by the seed script does check — it skips a topic if it already has concepts — but the admin bulk import page does not.

---

## 8. Generating Content with Claude AI

The fastest way to create high-quality educational content is to use Claude AI with a structured prompt.

### The Prompt Template

Use this template (also found in `COACHPRASH_BUILD_PROMPTS.md`):

```
Generate original educational content in CoachPrash qhsJSON format.

SUBJECT: [e.g., Mathematics]
TOPIC: [e.g., Algebra 1]
CONCEPT: [e.g., Solving Systems of Equations by Substitution]
GRADE LEVEL: [e.g., 9th-10th grade]
DIFFICULTY MIX: [e.g., 3 easy, 4 medium, 3 hard]
PROBLEM TYPES: [e.g., 7 MCQ, 2 fill-in-blank, 1 frq]
ACCESS TIER: [free or premium]

LEARNING OBJECTIVES:
1. [e.g., Students can solve a 2-variable system using substitution]
2. [e.g., Students can identify when substitution is most efficient]
3. [e.g., Students can verify solutions by plugging into both equations]

REQUIREMENTS:
- All content must be 100% ORIGINAL
- Use \( ... \) for inline LaTeX, \[ ... \] for display LaTeX
- Include 2 progressive hints per problem (general then specific)
- Hints can include cost_points: first hint 0, second hint 1
- Include step-by-step solutions for every problem
- Concept explanation should be ~5 minutes reading time
- 4 choices per MCQ, exactly 1 correct
- For fill_in_blank, use || separator for multiple accepted answers
- For frq, correct_answer is a model answer shown after submission
- If images are needed, use:
  <img data-bucket-key='images/{subject}/{topic}/{filename}' alt='description' />

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown fencing, no commentary)
```

### Workflow

1. **Fill in** the template with your subject/topic/concept details
2. **Paste** into Claude (Pro or Claude Code)
3. **Review** the output for accuracy — especially:
   - Correct answers (verify the math!)
   - LaTeX syntax (check `\(` and `\)` are balanced)
   - `is_correct` flags (exactly one `true` per MCQ)
4. **Validate** via `/admin/content/import` → click **Validate**
5. **Import** once validated

### Tips for Better Output

- Be specific about grade level — "AP Physics C" produces harder content than "Honors Physics"
- Specify the exact difficulty mix you want
- Include 2-3 learning objectives to focus the content
- Ask for callout boxes: "Include a callout-key and callout-warning box"
- For CS content, specify the language: "Use Java code blocks, NOT LaTeX for code"
- Generate one concept at a time for better quality
- Always verify mathematical accuracy before importing

---

## 9. Using Images (Railway Storage Bucket)

Images are stored in a Railway Storage Bucket (S3-compatible) and served via presigned URLs.

### Uploading Images

1. Go to `/admin/images`
2. Select the **image file** to upload
3. Choose a **Subject** and **Topic** (for organizing files)
4. Click **Upload**
5. On success, the page shows the **bucket key** — copy this for use in content

The bucket key follows the pattern: `images/{subject_slug}/{topic_slug}/{filename}`

Example: `images/mathematics/algebra-1/linear-graph.png`

### Using Images in Content

Reference uploaded images in your content HTML using the `data-bucket-key` attribute:

```html
<img data-bucket-key="images/mathematics/algebra-1/linear-graph.png"
     alt="Graph of y = 2x + 1" />
```

At render time, the `data-bucket-key` is automatically replaced with a presigned URL (valid for 1 hour). Students never see the bucket key — they get a temporary direct URL to the image.

### Using Images in qhsJSON

In your JSON content, use the same `data-bucket-key` attribute:

```json
{
  "content_html": "<p>Consider the graph below:</p><img data-bucket-key='images/physics/honors-physics/free-body-diagram.png' alt='Free body diagram of a box on a ramp' /><p>Identify all forces acting on the box.</p>"
}
```

### Important Notes

- **Upload the image first**, then reference it in content — the bucket key must match exactly
- Image files are stored permanently until manually deleted
- Presigned URLs expire after 1 hour but are regenerated on each page load
- If the storage bucket is not configured (missing `AWS_ENDPOINT_URL`), images will not render but the page will still load
- Supported formats: PNG, JPG, GIF, SVG, WebP
- Spaces in filenames are automatically replaced with hyphens

### Viewing Uploaded Images

The `/admin/images` page lists all images currently in the `images/` prefix of the bucket, showing their key, size, and last modified date.

---

## 10. Resources (Slides, Docs, Videos)

Resources are external learning materials (Google Slides, Docs, videos, PDFs, links) attached to a topic or subject.

### Creating a Resource

1. Go to `/admin/resources`
2. Click **New Resource**
3. Fill in:
   - **Title**: Display name (e.g., "Newton's Laws Lecture Slides")
   - **Resource Type**: Choose from:
     - `google_slides` — Google Slides presentation
     - `google_docs` — Google Docs document
     - `video_link` — YouTube or other video URL
     - `pdf_link` — PDF document URL
     - `external_link` — Any other URL
   - **URL**: The sharing link
   - **Description**: Brief description shown to students
   - **Access Tier**: `free` or `premium`
   - **Attach To**: Select a **Topic** or **Subject** (at least one required)
   - **Display Order**: Position among other resources
   - **Is Active**: Check to make visible

### Google Slides/Docs Embedding

For Google Slides and Docs, paste the **sharing URL** (the link you get from "Share" → "Copy link"). The system automatically converts it to an embeddable format:

| Type | Sharing URL | Converted To |
|------|------------|-------------|
| Slides | `https://docs.google.com/presentation/d/ABC123/edit?...` | `https://docs.google.com/presentation/d/ABC123/embed?start=false&loop=false` |
| Docs | `https://docs.google.com/document/d/ABC123/edit?...` | `https://docs.google.com/document/d/ABC123/preview` |

The embedded version is displayed in an iframe on the topic overview page.

### Freemium Gating for Resources

Resources follow the same gating rules as concepts:
- `access_tier: "free"` — visible to everyone
- `access_tier: "premium"` — only premium students can access

Free users see the resource title and description but cannot click through to view premium resources.

---

## 11. Freemium Gating & Access Control

CoachPrash uses a tiered access system to provide value to free users while incentivizing premium upgrades.

### Access Tiers

| Feature | Anonymous | Free (Logged In) | Premium |
|---------|-----------|-------------------|---------|
| Free concepts | Full access | Full access | Full access |
| Premium concepts | Teaser (blurred) | Teaser (blurred) | Full access |
| Problems per quiz | First 3 | First 3 | All |
| Hint #1 | Yes | Yes | Yes |
| Hints #2+ | No | No | Yes |
| Step-by-step solutions | No | No | Yes |
| Progress tracking | No | No | Yes |
| Free resources | Yes | Yes | Yes |
| Premium resources | No | No | Yes |

### How It Works

#### Concept Gating
- Each concept has an `access_tier` field: `free` or `premium`
- **Recommended pattern**: Make the first concept in each topic `free` and the rest `premium`
- Free/anonymous users see a blurred overlay with a "Upgrade to Premium" call-to-action on premium concepts
- The concept content is never sent to the client for gated concepts — gating is server-side

#### Problem Gating
- Free users get the **first 3 problems** of any quiz, regardless of the problem set's `access_tier`
- After 3 problems, a "More problems available with Premium" card appears
- This is enforced server-side — the practice page only sends 3 problems in the JSON for free users

#### Hint Gating
- Hint at index 0 (`cost_points: 0`) is available to everyone
- Subsequent hints (`cost_points: 1+`) are premium-only
- Free users see "Additional hints available with Premium" after the first hint

#### Solution Gating
- All step-by-step solutions are premium-only by default
- The solution API endpoint checks the user's tier before sending solution data

#### Anonymous User Prompts
- Anonymous users see a "Create a free account" prompt after every 3rd problem
- This encourages registration without blocking access

### Setting Access Tiers

When creating content via the admin panel or qhsJSON:

```json
{
  "concepts": [
    {"title": "Intro", "access_tier": "free", ...},
    {"title": "Advanced", "access_tier": "premium", ...}
  ]
}
```

For hints:
```json
"hints": [
  {"text": "General hint", "cost_points": 0},
  {"text": "Specific hint", "cost_points": 1}
]
```

---

## 12. Managing Students

### Viewing Students

Go to `/admin/students` to see all registered students (role = `student`), ordered by newest first.

Use the **search box** to filter by username or email (case-insensitive).

### Editing a Student

Click **Edit** next to any student to change:
- **Tier**: Switch between `free` and `premium`
- **Is Active**: Deactivate to prevent login (without deleting the account)

### Student Data

Each student has:
- **Username** and **Email** — set during registration
- **Auth Provider**: `local` (email/password), `google` (Google OAuth), or `both`
- **Tier**: `free` or `premium`
- **Progress**: StudentProgress records tracking concept completion and mastery scores
- **Attempts**: AttemptLog records for every problem attempt

### Demo Accounts

Two demo accounts are created by the seed script for testing:

| Email | Password | Tier |
|-------|----------|------|
| `demo.student@example.com` | `demo1234` | Premium |
| `demo.free@example.com` | `demo1234` | Free |

---

## 13. Access Codes

Access codes let you grant premium access to students without a payment system.

### Creating an Access Code

1. Go to `/admin/codes`
2. Click **New Code**
3. Fill in:
   - **Code**: Leave blank to auto-generate an 8-character alphanumeric code, or type a custom code (forced to uppercase)
   - **Tier**: `free` or `premium` — the tier granted to students who use this code
   - **Max Uses**: Maximum number of times this code can be used (leave blank for unlimited)
   - **Expires At**: Optional expiration date/time
4. Click **Save**

### How Students Use Access Codes

During registration at `/auth/register`, students can optionally enter an access code. If valid:
- Their account tier is set to the code's tier
- The code's `current_uses` counter increments by 1
- If `current_uses` reaches `max_uses`, the code becomes invalid

### Code Validation Rules

A code is **valid** if all of these are true:
- `is_active` = true
- `expires_at` is null or in the future
- `current_uses` < `max_uses` (or `max_uses` is null)

### Deactivating a Code

Click **Deactivate** next to any code to toggle its `is_active` status. This immediately prevents further use without deleting the code.

### Seed Access Codes

The seed script creates three demo codes:

| Code | Tier | Max Uses | Notes |
|------|------|----------|-------|
| `FREEACCS` | free | Unlimited | For testing free registration |
| `PREM2026` | premium | 10 | For testing premium registration |
| `EXPIRED1` | premium | 5 | Expired 30 days ago (for testing expiry) |

---

## 14. Blog & Resources Page

The blog serves as a resources section at `/resources/` for study tips, subject guides, and educational articles.

### Creating a Blog Post

1. Go to `/admin/blog`
2. Click **New Post**
3. Fill in:
   - **Title**: Post title
   - **Slug**: URL-friendly version (e.g., `5-tips-for-ap-calculus`)
   - **Content**: Post body in HTML (supports LaTeX via `\( \)` and `\[ \]`)
   - **Excerpt**: Short summary shown in the post list (max 500 characters)
   - **Is Published**: Check to make visible on the site
4. Click **Save**

### Publishing

- **Draft** (is_published = false): Only visible in the admin panel
- **Published** (is_published = true): Visible to all visitors at `/resources/<slug>`
- The `published_at` timestamp is set automatically when you first publish a post
- Posts are displayed newest-first with pagination (20 per page)

### Content Tips

Blog posts support the same HTML as concepts:
- LaTeX math with `\( \)` and `\[ \]`
- Callout boxes (`callout-key`, `callout-warning`, `callout-tip`)
- Images via `data-bucket-key`
- Code blocks with `<pre><code>`

Blog content is sanitized with nh3 on save, same as concept content.

---

## 15. Testimonials

### Managing Testimonials

Go to `/admin/testimonials` to view, create, edit, or delete testimonials.

### Creating a Testimonial

1. Click **New Testimonial**
2. Fill in:
   - **Student Name**: e.g., "Sarah K."
   - **Student Grade**: e.g., "11th Grade" (optional)
   - **Content**: The testimonial text
   - **Rating**: 1-5 stars (default: 5)
   - **Is Featured**: Check to highlight on the home page
   - **Is Active**: Check to display on the testimonials page
3. Click **Save**

### Display

- All active testimonials appear on `/testimonials`
- Featured testimonials appear on the home page
- Each testimonial shows: name, grade, star rating, and content

---

## 16. Contact Messages

### Viewing Messages

Go to `/admin/messages` to see all contact form submissions. Messages are ordered with **unread first**, then by date (newest first).

### Reading a Message

Click any message to view the full details:
- **Sender Name** and **Email**
- **Subject** line
- **Full Message** body
- **Received At** timestamp

Messages are automatically marked as **read** when you open them.

### Contact Form Rate Limiting

The contact form at `/contact` is rate-limited to **2 submissions per minute** per IP address to prevent spam.

---

## 17. SEO & Sitemap

### Meta Tags

Every page has customizable SEO meta tags. The base template provides defaults that individual pages can override:

- **Title**: `{% block title %}CoachPrash — STEM Tutoring & Practice{% endblock %}`
- **Meta Description**: `{% block meta_description %}Expert STEM tutoring...{% endblock %}`
- **Open Graph Tags**: og:title, og:description, og:type, og:url
- **Canonical URL**: Set automatically from `request.url`

### robots.txt

Served at `/robots.txt`. Current configuration:
- **Allows** all crawlers on all public pages
- **Disallows**: `/admin/`, `/api/`, `/progress/`, `/auth/`
- Points to sitemap at `/sitemap.xml`

### sitemap.xml

Dynamically generated at `/sitemap.xml`. Includes:
- Static pages: home, about, contact, testimonials, resources
- All active subjects and their topics
- All **free-tier** concepts (premium concepts are excluded)
- All published blog posts

The sitemap updates automatically as you add or modify content.

### Favicon

The site uses a data-URI SVG favicon — a navy rounded rectangle with gold "CP" text. No external file needed.

---

## 18. Security & Rate Limiting

### Rate Limiting

The following endpoints are rate-limited (per IP address):

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /auth/login` | 5/minute | Prevent brute-force login |
| `POST /auth/register` | 3/minute | Prevent mass registration |
| `POST /contact` | 2/minute | Prevent contact spam |
| `/api/*` (all API routes) | 60/minute | Prevent API abuse |

Rate limits are stored in process memory (`memory://`). When a limit is exceeded, the server returns HTTP 429 (Too Many Requests).

### Security Headers

Every response includes these security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `SAMEORIGIN` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS protection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer info |
| `Content-Security-Policy` | See below | Restrict content sources |

### Content Security Policy (CSP)

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data: https://*.railway.app;
connect-src 'self';
frame-src 'self' https://docs.google.com;
```

### CSRF Protection

All forms and API endpoints are protected with CSRF tokens via Flask-WTF. The CSRF token is included in:
- A `<meta name="csrf-token">` tag in the page header
- JavaScript reads this for AJAX requests via `X-CSRFToken` header

### HTML Sanitization

All admin-submitted HTML content (concepts, blog posts) is sanitized with `nh3` before storage. This prevents XSS attacks even if an admin account is compromised.

### Passwords

- Hashed with Werkzeug's `generate_password_hash` (PBKDF2)
- Minimum 8 characters enforced during registration
- Never stored or transmitted in plain text

### Email Handling

- Emails are stored lowercase to prevent duplicate accounts
- Email matching uses case-insensitive comparison (`ilike()`)

---

## 19. Seeding & Demo Data

### Running the Seed Script

The seed script populates the database with initial data. Run it via:

**Railway CLI:**
```bash
flask seed
```

**HTTP endpoint (for Railway deployments):**
```
GET /run-seed/<admin_password>
```

The admin password in the URL must match the `ADMIN_PASSWORD` environment variable.

### What Gets Seeded

In order:

1. **Admin user** — from `ADMIN_EMAIL` and `ADMIN_PASSWORD` env vars
2. **5 Subjects** with **26 Topics** — the complete course catalog structure
3. **5 Content JSON files** — demo content with concepts and problems:
   - Mathematics / Algebra 1: Linear Equations
   - Physics / Honors Physics: Newton's Laws
   - Chemistry / Honors Chemistry: The Mole Concept
   - Computer Science / AP CS A: Arrays & ArrayLists
   - Test Prep / SAT Math: Heart of Algebra
4. **8 Testimonials** — realistic student testimonials
5. **4 Blog Posts** — educational articles with LaTeX
6. **2 Demo Students** — for testing (see [Section 12](#12-managing-students))
7. **3 Access Codes** — for testing (see [Section 13](#13-access-codes))

### Idempotency

The seed script is safe to run multiple times:
- Admin user: skipped if email already exists
- Subjects/Topics: skipped if slug already exists
- Content JSON: skipped if topic already has concepts
- Testimonials: skipped if table is not empty
- Blog posts: skipped if table is not empty
- Demo students: skipped if email already exists
- Access codes: skipped if table is not empty

**Important**: The seed script never auto-runs on deployment. You must trigger it manually.

---

## 20. Deployment & Environment Variables

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret (random string) | `a1b2c3d4e5f6...` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@host:5432/db` |
| `ADMIN_EMAIL` | Admin account email | `admin@coachprash.com` |
| `ADMIN_PASSWORD` | Admin account password | `secure-password-here` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `development` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | — |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | — |
| `AWS_ENDPOINT_URL` | Railway Storage Bucket endpoint | — |
| `AWS_ACCESS_KEY_ID` | Bucket access key | — |
| `AWS_SECRET_ACCESS_KEY` | Bucket secret key | — |
| `AWS_DEFAULT_REGION` | Bucket region | `us-east-1` |
| `AWS_S3_BUCKET_NAME` | Bucket name | — |
| `ASSET_VERSION` | Cache-busting version for CSS/JS | `3.0` |

### Railway Deployment

The app deploys to Railway with this start command (in `railway.toml`):
```
flask db upgrade && gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2
```

This runs database migrations automatically before starting the server.

### Cache Busting

Static assets (CSS, JS) are served with `?v=3.0` query parameters for cache busting. When you update CSS or JS:
1. Change the `ASSET_VERSION` environment variable (e.g., to `3.1`)
2. Redeploy — the new version number invalidates browser caches

Static files are cached for 1 year (`Cache-Control: public, max-age=31536000`).

---

## 21. Troubleshooting

### LaTeX Not Rendering

**Symptom**: Raw `\(` and `\)` text visible instead of rendered math.

**Causes and fixes**:
- KaTeX CDN not loading — check browser devtools Network tab for blocked requests
- CSP blocking KaTeX scripts — ensure `script-src` includes `https://cdn.jsdelivr.net`
- Content inserted after page load (AJAX) — the practice quiz JS calls `renderMathInElement()` after inserting content; if you see raw LaTeX in concept pages, check that `main.js` fires the KaTeX auto-render on DOMContentLoaded

### Images Not Loading

**Symptom**: Broken image icons or "Image unavailable" alt text.

**Causes and fixes**:
- Bucket not configured — verify all `AWS_*` environment variables are set
- Wrong bucket key — the `data-bucket-key` in the HTML must exactly match the key shown after upload
- Presigned URL expired — URLs expire after 1 hour; refresh the page to get new ones

### Bulk Import Fails

**Symptom**: "Subject not found" or "Topic not found" error.

**Fix**: Create the subject and topic via `/admin/content` first, then import. The slugs in your JSON must exactly match the database records.

**Symptom**: "Invalid JSON" error.

**Fix**: Validate your JSON syntax. Common issues:
- Trailing commas after the last item in arrays/objects
- Unescaped quotes in strings
- Missing closing brackets

### Student Can't Access Premium Content

**Symptom**: Student sees "Upgrade to Premium" even though they should have access.

**Check**:
1. Go to `/admin/students` and verify their tier is `premium`
2. Verify their account is active (`is_active = true`)
3. If they used an access code, verify the code's tier is `premium`

### Rate Limiting Triggered

**Symptom**: HTTP 429 "Too Many Requests" response.

**Fix**: Rate limits reset automatically after the time window. In development, you can restart the Flask server to clear the in-memory rate limit store.

### Database Errors

**Symptom**: 500 error pages.

**Common causes**:
- Database not migrated — run `flask db upgrade`
- Missing seed data — run `flask seed`
- Connection issues — check `DATABASE_URL` environment variable

---

## 22. Quick Reference

### URL Structure

| URL | Page |
|-----|------|
| `/` | Home page |
| `/subjects/` | Subject catalog |
| `/subjects/<subject>` | Topic list for a subject |
| `/subjects/<subject>/<topic>` | Topic overview with concepts |
| `/subjects/<subject>/<topic>/<concept>` | Concept explainer |
| `/subjects/<subject>/<topic>/<concept>/practice/` | Practice quiz |
| `/resources/` | Blog/resources listing |
| `/resources/<slug>` | Individual blog post |
| `/about` | About page |
| `/contact` | Contact form |
| `/testimonials` | Testimonials page |
| `/auth/login` | Login |
| `/auth/register` | Registration |
| `/progress/` | Student progress dashboard |
| `/admin/` | Admin dashboard |
| `/robots.txt` | Search engine directives |
| `/sitemap.xml` | Sitemap for search engines |

### Content Hierarchy at a Glance

```
Subject → Topic → Concept → Problem Set → Problem
                                            ├── Choices (MCQ)
                                            ├── Hints (progressive)
                                            └── Solution (steps)
```

### Creating Content: Quick Checklist

1. [ ] Subject exists (or create at `/admin/content`)
2. [ ] Topic exists under the subject (or create)
3. [ ] Generate qhsJSON using Claude AI prompt template
4. [ ] Verify math accuracy in the generated content
5. [ ] Validate JSON at `/admin/content/import`
6. [ ] Import the validated JSON
7. [ ] Set first concept to `free`, rest to `premium`
8. [ ] Upload any images via `/admin/images`
9. [ ] Test the content on the live site as both free and premium users
10. [ ] Check LaTeX renders correctly
11. [ ] Verify hints and solutions work

### Problem Type Quick Reference

| Type | Student Input | Grading | `correct_answer` |
|------|--------------|---------|-------------------|
| `mcq` | Click a choice card | Auto (matches `is_correct`) | Not used |
| `fill_in_blank` | Type in text field | Auto (case-insensitive) | Required (`\|\|` for alternatives) |
| `frq` | Type in textarea | Self-graded by student | Model answer shown after submit |

### LaTeX Quick Reference

```
Inline:   \( x^2 + 3x - 7 \)
Display:  \[ \frac{-b \pm \sqrt{b^2 - 4ac}}{2a} \]

Fractions:   \frac{a}{b}
Exponents:   x^2, x^{n+1}
Subscripts:  x_1, a_{ij}
Roots:       \sqrt{x}, \sqrt[n]{x}
Greek:       \alpha, \beta, \theta, \pi, \Delta
Vectors:     \vec{F}, \vec{v}
Sums:        \sum_{i=1}^{n}
Integrals:   \int_a^b f(x)\,dx
Comparison:  \leq, \geq, \neq, \approx
Text:        \text{net}, \text{avg}
Units:       \,\text{m/s}^2
```

### Callout Box Quick Reference

```html
<div class="callout-key"><strong>Key Takeaway:</strong> ...</div>
<div class="callout-warning"><strong>Common Mistake:</strong> ...</div>
<div class="callout-tip"><strong>Tip:</strong> ...</div>
```

### Image Quick Reference

```html
<!-- Upload image at /admin/images first, then reference: -->
<img data-bucket-key="images/{subject}/{topic}/{filename}" alt="description" />
```
