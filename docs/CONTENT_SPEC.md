# CoachPrash Content Spec (qhsJSON)

> **Purpose:** Single reference for Claude Code agents generating course content.
> Agents: READ THIS FILE instead of receiving inline instructions.

---

## File Structure

```
content/{subject_slug}_{course_slug}.json
```

### Top-level wrapper

```json
{
  "subject_slug": "mathematics",
  "course_slug": "ap-statistics",
  "topics": [ ... ]
}
```

### Topic (= one unit/chapter/module of the course)

```json
{
  "name": "Unit 1: Exploring One-Variable Data and Collecting Data",
  "slug": "unit-1-exploring-one-variable-data-and-collecting-data",
  "description": "2-3 sentence summary of the unit.",
  "display_order": 0,
  "concepts": [ ... ]
}
```

### Concept (= one lesson/section within a topic)

```json
{
  "title": "Introducing Statistics: What Can We Learn from Data?",
  "slug": "introducing-statistics",
  "subject_area": "statistics",
  "difficulty": "easy|medium|hard",
  "tags": ["ap-statistics", "unit-1", "topic-1-1"],
  "content_html": "<h2>Title</h2><p>Rich HTML lesson content...</p>",
  "content_raw": "Plain text title only",
  "estimated_minutes": 8,
  "access_tier": "free",
  "display_order": 0,
  "problem_sets": [ ... ]
}
```

---

## content_html Guidelines

- **Length:** 500-1500 words of rich HTML
- **LaTeX math:** `\( inline \)` and `\[ display \]`
- **LaTeX escaping in JSON:** Double-escape backslashes: `\\( \\mu \\)`, `\\[ x^2 \\]`
- **Callout blocks:**
  - `<div class="callout-key"><strong>Key Idea:</strong> ...</div>`
  - `<div class="callout-warning"><strong>Common Mistake:</strong> ...</div>` (or `<strong>AP Exam Tip:</strong>` for AP courses)
- **Include:** definitions, formulas, worked examples, common mistakes
- **Never use raw Unicode math symbols** (no `≠`, `≤`, `≥`). Always use LaTeX: `\(\neq\)`, `\(\leq\)`, `\(\geq\)`

---

## Diagrams

Diagrams are stored as data fields in the content JSON, not as inline HTML. The seed process builds `<figure>` tags at load time.

### Concept-level diagrams

Add a `diagrams` array to the concept object:

```json
{
  "title": "Forces and Free-Body Diagrams",
  "slug": "forces-free-body-diagrams",
  "content_html": "...",
  "diagrams": [
    {
      "bucket_key": "images/physics/ap-physics-1-mechanics/fbd-block-flat-surface.svg",
      "alt_text": "Free-body diagram showing all forces on a block on a flat surface",
      "caption": "Forces acting on a block on a flat surface"
    }
  ],
  "problem_sets": [ ... ]
}
```

Diagrams are appended to `content_html` at seed time.

### Problem-level diagrams

Add a `diagram` object (singular) to the problem:

```json
{
  "question_html": "<p>A box slides down a 30° incline...</p>",
  "problem_type": "mcq",
  "diagram": {
    "bucket_key": "images/physics/ap-physics-1-mechanics/fbd-box-ramp-30deg.svg",
    "alt_text": "Free-body diagram of box on 30° incline",
    "caption": "Forces on a box sliding down a ramp"
  },
  "choices": [ ... ]
}
```

The diagram is prepended to `question_html` at seed time. This means diagrams move with problems — reordering, restructuring, or sharing concepts across courses never breaks diagram associations.

### Diagram fields

| Field | Required | Description |
|-------|----------|-------------|
| `bucket_key` | Yes | S3 object key (e.g., `images/physics/ap-physics-1-mechanics/fbd.svg`) |
| `alt_text` | Yes | Accessible description for screen readers |
| `caption` | No | Figcaption text displayed below the image |

### Diagram generation pipeline

SVG files are generated from manifest files (`scripts/manifests/*.json`) which contain rendering parameters only. The manifests do NOT reference problems — they are purely build tools for SVG generation.

```
manifest → generate_diagrams.py → upload_diagrams.py → bucket
content JSON (diagram field) → flask seed → <figure> tags in DB
```

---

## Problem Set Structure

Each concept gets exactly **1 problem_set** with **10 problems** in this exact order:

| Index | Type | Access   | Description         |
|-------|------|----------|---------------------|
| 0     | mcq  | free     | Easy-medium MCQ     |
| 1     | mcq  | free     | Easy-medium MCQ     |
| 2     | ftb  | free     | Fill-in-the-blank   |
| 3     | ftb  | free     | Fill-in-the-blank   |
| 4     | mcq  | premium  | Medium-hard MCQ     |
| 5     | mcq  | premium  | Medium-hard MCQ     |
| 6     | ftb  | premium  | Medium-hard FTB     |
| 7     | ftb  | premium  | Medium-hard FTB     |
| 8     | frq  | premium  | Free-response       |
| 9     | frq  | premium  | Free-response       |

### Problem Set wrapper

```json
{
  "title": "Practice: Concept Title Here",
  "access_tier": "free",
  "display_order": 0,
  "problems": [ ... ]
}
```

---

## Problem Types

### MCQ (Multiple Choice)

```json
{
  "question_html": "<p>Question text with \\( LaTeX \\) if needed.</p>",
  "problem_type": "mcq",
  "difficulty": "easy",
  "points": 1,
  "choices": [
    { "text": "Wrong answer", "is_correct": false },
    { "text": "Wrong answer", "is_correct": false },
    { "text": "Correct answer", "is_correct": true },
    { "text": "Wrong answer", "is_correct": false }
  ],
  "hints": [
    { "text": "Free hint — nudge toward the concept.", "cost_points": 0 },
    { "text": "Paid hint — nearly gives the answer.", "cost_points": 1 }
  ],
  "solution_steps": [
    { "text": "Step 1 explanation." },
    { "text": "Step 2 explanation with \\( math \\)." }
  ],
  "access_tier": "free"
}
```

- Exactly **4 choices**, exactly **1 correct**
- Randomize correct answer position (don't always put it in slot C)

### FTB (Fill-in-the-Blank)

```json
{
  "question_html": "<p>What is the value of \\( 2 + 3 \\)?</p>",
  "problem_type": "ftb",
  "difficulty": "medium",
  "points": 1,
  "correct_answer": "5",
  "hints": [ ... ],
  "solution_steps": [ ... ],
  "access_tier": "free"
}
```

- **Multiple accepted answers:** Use `||` separator: `"right skewed||skewed right||skewed to the right"`
- Keep answers short (1-3 words or a number)
- Case-insensitive matching

### FRQ (Free Response)

```json
{
  "question_html": "<p>Multi-part question with (a), (b), (c)...</p>",
  "problem_type": "frq",
  "difficulty": "hard",
  "points": 3,
  "correct_answer": "(a) Model answer...\n(b) Model answer...\n(c) Model answer...",
  "hints": [ ... ],
  "solution_steps": [ ... ],
  "access_tier": "premium"
}
```

- FRQs are always `"access_tier": "premium"`
- Create original, real-world context FRQs with multi-part structure
- **AP courses only:** Use released College Board FRQs verbatim (public domain). Never copy from third-party sites.
- **AP Statistics inference:** Use State/Plan/Do/Conclude framework

---

## Hints

Every problem gets exactly **2 hints:**

1. **Free hint** (`cost_points: 0`) — conceptual nudge, doesn't give the answer
2. **Paid hint** (`cost_points: 1`) — nearly reveals the answer

---

## Solution Steps

Every problem gets **2-4 solution steps.** Each step is `{ "text": "..." }`.

- Use LaTeX for math: `\\( expression \\)` or `\\[ display \\]`
- Reference the specific numbers/context from the problem
- Never use raw Unicode math symbols in solution text

---

## Complete Example (1 MCQ + 1 FTB + 1 FRQ)

<details>
<summary>Click to expand full example concept JSON</summary>

```json
{
  "title": "Introducing Statistics: What Can We Learn from Data?",
  "slug": "introducing-statistics",
  "subject_area": "statistics",
  "difficulty": "easy",
  "tags": ["ap-statistics", "unit-1", "topic-1-1"],
  "content_html": "<h2>Introducing Statistics</h2><p><strong>Statistics</strong> is the science of collecting, organizing, analyzing, and interpreting data.</p><h3>Population vs. Sample</h3><p>A <strong>population</strong> is the entire group (size \\( N \\)). A <strong>sample</strong> is a subset (size \\( n \\)).</p><div class=\"callout-key\"><strong>Key Idea:</strong> Always answer in context.</div><div class=\"callout-warning\"><strong>AP Exam Tip:</strong> Vague answers lose credit.</div>",
  "content_raw": "Introducing Statistics: What Can We Learn from Data?",
  "estimated_minutes": 8,
  "access_tier": "free",
  "display_order": 0,
  "problem_sets": [
    {
      "title": "Practice: Introducing Statistics",
      "access_tier": "free",
      "display_order": 0,
      "problems": [
        {
          "question_html": "<p>A researcher surveys 200 students from 10 high schools in California to estimate average social media use. What is the <strong>population</strong>?</p>",
          "problem_type": "mcq",
          "difficulty": "easy",
          "points": 1,
          "choices": [
            { "text": "The 200 students surveyed", "is_correct": false },
            { "text": "The 10 high schools", "is_correct": false },
            { "text": "All high school students in California", "is_correct": true },
            { "text": "All students who use social media", "is_correct": false }
          ],
          "hints": [
            { "text": "The population is the entire group the researcher wants to learn about.", "cost_points": 0 },
            { "text": "The researcher wants to learn about all CA high school students. The 200 surveyed are the sample.", "cost_points": 1 }
          ],
          "solution_steps": [
            { "text": "The population is the entire group of interest: all high school students in California." },
            { "text": "The 200 surveyed students are the sample drawn from that population." }
          ],
          "access_tier": "free"
        },
        {
          "question_html": "<p>A biologist tags 45 deer to estimate the total deer population. The number 45 represents which value? (Enter the letter used in statistics.)</p>",
          "problem_type": "ftb",
          "difficulty": "easy",
          "points": 1,
          "correct_answer": "n||sample size",
          "hints": [
            { "text": "The 45 deer are a subset. What letter denotes subset size?", "cost_points": 0 },
            { "text": "Sample size is \\( n \\) (lowercase). Population size is \\( N \\) (uppercase).", "cost_points": 1 }
          ],
          "solution_steps": [
            { "text": "The 45 tagged deer are a sample of all deer in the forest." },
            { "text": "Sample size is denoted \\( n \\). So 45 = \\( n \\)." }
          ],
          "access_tier": "free"
        },
        {
          "question_html": "<p>A city council surveys 800 of 25,000 households about a new park.</p><p>(a) Identify the population and sample.</p><p>(b) Rewrite \"68% support the park\" in proper statistical context.</p><p>(c) Why is sampling practical here?</p>",
          "problem_type": "frq",
          "difficulty": "easy",
          "points": 3,
          "correct_answer": "(a) Population: all 25,000 households. Sample: the 800 surveyed.\n(b) Based on 800 randomly selected households, approximately 68% of responding city residents support the new park.\n(c) Surveying all 25,000 households would be costly and slow. A random sample provides a reliable estimate at a fraction of the effort.",
          "hints": [
            { "text": "For (a): who does the council want to learn about vs. who did they actually survey?", "cost_points": 0 },
            { "text": "For (b): mention who, what, and the basis (sample). For (c): think cost/time.", "cost_points": 1 }
          ],
          "solution_steps": [
            { "text": "(a) Population = all 25,000 city households. Sample = 800 surveyed households." },
            { "text": "(b) \"Based on 800 randomly selected city households, about 68% support building a new community park.\"" },
            { "text": "(c) Surveying the entire population would cost significantly more time and money. A well-chosen random sample gives a reliable estimate." }
          ],
          "access_tier": "premium"
        }
      ]
    }
  ]
}
```

</details>

---

## Agent Workflow (Token-Efficient)

When generating content for a full course:

1. **Agent prompt should be minimal:** "Read `docs/CONTENT_SPEC.md` for format. Generate concepts for [topics list]. Write to `temp_unitN.json`."
2. **Do NOT repeat this spec inline** in agent prompts
3. **Use 1 agent per unit** (not 3), each handling all topics for that unit
4. **Each agent writes a temp file** — merge into the main file afterward with a Python script
5. **Validate with Python scripts** via Bash — never read the full JSON back into conversation
