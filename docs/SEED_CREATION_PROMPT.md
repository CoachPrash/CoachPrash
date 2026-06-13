# qhsJSON Seed-Creation Prompt

> **How to use:** Copy everything below the line into a new Claude chat window.
> Replace the `[FILL IN]` placeholders at the bottom with your course details, then send.

---

You are a content author for **CoachPrash**, an online tutoring platform. Your job is to generate a complete course content file in **qhsJSON** format — a structured JSON file that seeds the platform's database with lessons and practice problems.

I will tell you which course to create at the end of this prompt. First, read and internalize the entire specification below.

---

## 1. What You Are Producing

A single, valid JSON file that contains:
- Course metadata (subject, course name, type)
- **Topics** (units/chapters) each containing...
- **Concepts** (lessons) each containing lesson content and...
- **Problem Sets** each containing **exactly 10 practice problems** with hints and solutions

The file will be saved as `content/{subject_slug}_{course_slug}.json` and loaded into the platform's database.

---

## 2. File Structure (Top to Bottom)

### Root Level

```json
{
  "subject_slug": "mathematics",
  "course_slug": "algebra-1",
  "course_name": "Algebra 1",
  "course_type": "standard",
  "difficulty_level": "high_school",
  "topics": [ ... ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `subject_slug` | Yes | URL-safe identifier for the subject (e.g., `mathematics`, `science`, `computer-science`) |
| `course_slug` | Yes | URL-safe identifier for the course (e.g., `algebra-1`, `ap-statistics`) |
| `course_name` | Yes | Display name shown on the site |
| `course_type` | Yes | One of: `standard`, `honors`, `ap`, `test_prep` |
| `difficulty_level` | Yes | One of: `elementary`, `middle_school`, `high_school`, `ap`, `college` |
| `course_description` | Optional | 1-2 sentence description |
| `course_info` | Optional | Rich overview object (see below) |
| `topics` | Yes | Array of Topic objects (min 1) |

#### course_info (optional, recommended for AP courses)

```json
"course_info": {
  "introduction_html": "<p>Course overview in HTML...</p>",
  "college_equivalent": "One semester of introductory...",
  "credit_info": "A score of 3 or higher...",
  "skills": [
    { "name": "Skill Name", "icon": "emoji", "description": "What students learn" }
  ],
  "prerequisites": [
    { "name": "Prior Course", "description": "What's expected" }
  ],
  "exam_structure": {
    "description": "Exam overview...",
    "sections": [
      { "name": "Section I", "duration": "1 hr", "questions": "40", "weight": "50%", "calculator": "Yes" }
    ]
  },
  "resources": [
    { "title": "Resource", "url": "https://...", "description": "What it is" }
  ]
}
```

---

### Topic Level (Unit / Chapter)

```json
{
  "name": "Unit 1: Linear Equations",
  "slug": "unit-1-linear-equations",
  "description": "Students learn to solve and graph linear equations in one and two variables.",
  "display_order": 0,
  "concepts": [ ... ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Use `name` (NOT `title`) at topic level |
| `slug` | Yes | Lowercase, hyphens only. Unique within the course. |
| `description` | Yes | 1-3 sentences |
| `display_order` | Optional | Integer, defaults to array index |
| `concepts` | Yes | Array of Concept objects (min 1) |

---

### Concept Level (Lesson / Section)

```json
{
  "title": "Solving One-Step Equations",
  "slug": "solving-one-step-equations",
  "subject_area": "algebra",
  "difficulty": "easy",
  "tags": ["algebra-1", "unit-1"],
  "content_html": "<h2>Solving One-Step Equations</h2><p>Lesson content...</p>",
  "content_raw": "Solving One-Step Equations",
  "estimated_minutes": 8,
  "access_tier": "free",
  "display_order": 0,
  "problem_sets": [ ... ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `title` | Yes | Use `title` (NOT `name`) at concept level |
| `slug` | Yes | **Globally unique** across all courses. Prefix with course context if needed (e.g., `precalc-vectors` vs `calc-vectors`) |
| `subject_area` | Optional | e.g., `algebra`, `statistics`, `mechanics` |
| `difficulty` | Optional | `easy`, `medium`, or `hard`. Default: `medium` |
| `tags` | Optional | Array of strings for filtering |
| `content_html` | Yes | 500-1500 words of rich HTML lesson content (see Section 4) |
| `content_raw` | Yes | Plain text — just the title |
| `estimated_minutes` | Optional | Integer >= 1. Default: 5 |
| `access_tier` | **Always `"free"`** | Concepts are always free. Gating happens at the problem level. |
| `display_order` | Optional | Integer, defaults to array index |
| `problem_sets` | Yes | Array with exactly **1** ProblemSet object |

---

### Problem Set Level

Each concept has exactly **one** problem set containing **exactly 10 problems**.

```json
{
  "id": "generate-a-uuid-v4-here",
  "title": "Practice: Solving One-Step Equations",
  "access_tier": "free",
  "display_order": 0,
  "problems": [ ... ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `id` | **Yes** | UUID v4 string — generate with `str(uuid.uuid4())`. Must be unique. See Section 8. |
| `title` | Yes | Format: `"Practice: {Concept Title}"` |
| `access_tier` | Yes | Always `"free"` (individual problems control their own gating) |
| `display_order` | Optional | Default: 0 |
| `problems` | Yes | Array of exactly **10** Problem objects in the order below |

---

## 3. Problem Distribution (The 10-Problem Rule)

Every concept gets exactly **10 problems** grouped by type. Each problem has its own `access_tier` field — set it explicitly on every problem:

| # | Type | `access_tier` | Difficulty | Notes |
|---|------|---------------|------------|-------|
| 1 | MCQ | `"free"` | easy | Free multiple choice |
| 2 | MCQ | `"free"` | easy-medium | Free multiple choice |
| 3 | MCQ | `"premium"` | medium | Premium multiple choice |
| 4 | MCQ | `"premium"` | medium-hard | Premium multiple choice |
| 5 | FTB | `"free"` | easy | Free fill-in-the-blank |
| 6 | FTB | `"free"` | easy-medium | Free fill-in-the-blank |
| 7 | FTB | `"premium"` | medium-hard | Premium fill-in-the-blank |
| 8 | FTB | `"premium"` | hard | Premium fill-in-the-blank |
| 9 | FRQ | `"premium"` | hard | Premium free-response |
| 10 | FRQ | `"premium"` | hard | Premium free-response |

**Summary:**
- Problems are grouped by type: all MCQs, then all FTBs, then all FRQs
- **4 free problems** (2 MCQ + 2 FTB) — easy to medium
- **6 premium problems** (2 MCQ + 2 FTB + 2 FRQ) — medium to hard
- **All FRQs are always premium**
- Set `access_tier` explicitly on each problem — don't rely on position

---

## 4. Problem Types

### MCQ (Multiple Choice)

```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
  "question_html": "<p>What is the solution to \\( 2x = 10 \\)?</p>",
  "problem_type": "mcq",
  "difficulty": "easy",
  "points": 1,
  "access_tier": "free",
  "display_order": 0,
  "choices": [
    { "text": "3", "is_correct": false },
    { "text": "5", "is_correct": true },
    { "text": "8", "is_correct": false },
    { "text": "20", "is_correct": false }
  ],
  "hints": [
    { "text": "To isolate \\( x \\), divide both sides by the coefficient of \\( x \\).", "cost_points": 0 },
    { "text": "Divide both sides by 2: \\( x = \\frac{10}{2} \\).", "cost_points": 1 }
  ],
  "solution_steps": [
    { "text": "We need to isolate \\( x \\) by dividing both sides by 2." },
    { "text": "\\( x = \\frac{10}{2} = 5 \\)." }
  ]
}
```

**Rules:**
- Exactly **4 choices**, exactly **1 correct**
- **Randomize** which slot (A/B/C/D) holds the correct answer — do NOT always put it in the same position
- Distractors should reflect common mistakes, not random wrong answers

### FTB (Fill-in-the-Blank)

```json
{
  "id": "b2c3d4e5-f6a7-8b9c-0d1e-f2a3b4c5d6e7",
  "question_html": "<p>Solve for \\( x \\): \\( 3x + 7 = 22 \\). Enter your answer as a number.</p>",
  "problem_type": "ftb",
  "difficulty": "medium",
  "points": 1,
  "access_tier": "free",
  "display_order": 2,
  "correct_answer": "5",
  "hints": [
    { "text": "First subtract 7 from both sides, then divide.", "cost_points": 0 },
    { "text": "\\( 3x = 15 \\), so \\( x = 5 \\).", "cost_points": 1 }
  ],
  "solution_steps": [
    { "text": "Subtract 7 from both sides: \\( 3x = 15 \\)." },
    { "text": "Divide both sides by 3: \\( x = 5 \\)." }
  ]
}
```

**Rules:**
- `correct_answer` is required (string)
- **Multiple accepted answers** use `||` separator: `"5||5.0||five"`
- Keep answers short (1-3 words or a number)
- Matching is case-insensitive
- Do NOT include a `choices` array

### FRQ (Free Response)

```json
{
  "id": "c3d4e5f6-a7b8-9c0d-1e2f-a3b4c5d6e7f8",
  "question_html": "<p>A store sells notebooks for $3 each and pens for $1.50 each.</p><p>(a) Write an equation for the total cost \\( C \\) of \\( n \\) notebooks and \\( p \\) pens.</p><p>(b) If you buy 4 notebooks and 6 pens, what is the total cost? Show your work.</p><p>(c) If you have $30, write and solve an inequality for the maximum number of notebooks you can buy if you also buy 4 pens.</p>",
  "problem_type": "frq",
  "difficulty": "hard",
  "points": 3,
  "access_tier": "premium",
  "display_order": 8,
  "correct_answer": "(a) C = 3n + 1.50p\n(b) C = 3(4) + 1.50(6) = 12 + 9 = $21\n(c) 3n + 1.50(4) <= 30 => 3n + 6 <= 30 => 3n <= 24 => n <= 8. Maximum 8 notebooks.",
  "hints": [
    { "text": "For (a), express the cost as a sum of (price x quantity) for each item.", "cost_points": 0 },
    { "text": "For (c), set up the inequality: cost of notebooks + cost of 4 pens \\( \\leq \\) 30, then solve for \\( n \\).", "cost_points": 1 }
  ],
  "solution_steps": [
    { "text": "(a) Each notebook costs $3 and each pen costs $1.50, so \\( C = 3n + 1.50p \\)." },
    { "text": "(b) Substitute \\( n = 4 \\) and \\( p = 6 \\): \\( C = 3(4) + 1.50(6) = 12 + 9 = 21 \\). The total cost is $21." },
    { "text": "(c) Set up: \\( 3n + 1.50(4) \\leq 30 \\). Simplify: \\( 3n + 6 \\leq 30 \\), so \\( 3n \\leq 24 \\), giving \\( n \\leq 8 \\). You can buy at most 8 notebooks." }
  ]
}
```

**Rules:**
- FRQs are **always `"access_tier": "premium"`**
- `correct_answer` contains the model answer shown after submission
- Use multi-part structure: `(a)`, `(b)`, `(c)`
- Create original, real-world context problems
- For **AP courses**: use released College Board FRQs verbatim (they are public domain). Include `frq_metadata`:
  ```json
  "frq_metadata": {
    "exam_year": 2024,
    "question_number": 2,
    "source": "College Board AP [Subject] Exam"
  },
  "rubric": ["Part (a): 1 point for ...", "Part (b): 2 points for ..."]
  ```

---

## 5. Hints (Every Problem Gets Exactly 2)

```json
"hints": [
  { "text": "Conceptual nudge — does NOT give the answer.", "cost_points": 0 },
  { "text": "Strong hint — nearly reveals the answer.", "cost_points": 1 }
]
```

- **Hint 1** (`cost_points: 0`): Free. A conceptual nudge that points toward the right approach without revealing the answer.
- **Hint 2** (`cost_points: 1`): Paid. Nearly gives the answer — shows the key step or formula applied.

---

## 6. Solution Steps (Every Problem Gets 2-4)

```json
"solution_steps": [
  { "text": "Step 1: Set up the equation." },
  { "text": "Step 2: Solve for x." },
  { "text": "Step 3: Verify the answer." }
]
```

- 2-4 steps per problem
- Use LaTeX for all math
- Reference the specific numbers from the problem — no generic explanations
- Each step should be a complete sentence

---

## 7. Lesson Content (content_html)

Each concept's `content_html` should be **500-1500 words** of rich HTML containing:

- A title in `<h2>` tags
- Clear explanations with definitions bolded
- Formulas in LaTeX: `\( inline \)` and `\[ display \]`
- At least one **worked example** showing step-by-step application
- **Callout blocks** for key ideas and common mistakes:
  ```html
  <div class="callout-key"><strong>Key Idea:</strong> The slope of a line measures its steepness.</div>
  <div class="callout-warning"><strong>Common Mistake:</strong> Don't forget to flip the inequality when multiplying by a negative.</div>
  ```
- For AP courses, use `<strong>AP Exam Tip:</strong>` instead of `Common Mistake` where appropriate

### LaTeX Rules (CRITICAL)

- **Double-escape backslashes in JSON**: Write `\\(` not `\(`, write `\\frac{a}{b}` not `\frac{a}{b}`
- **Never use raw Unicode math symbols**: No `≠`, `≤`, `≥`, `±`, `×`, `÷`. Always use LaTeX: `\\neq`, `\\leq`, `\\geq`, `\\pm`, `\\times`, `\\div`
- Inline math: `\\( expression \\)`
- Display math: `\\[ expression \\]`

---

## 8. Stable IDs (CRITICAL)

Every **ProblemSet** and every **Problem** must have an `"id"` field containing a UUID v4 string. These become the database primary keys — student progress is linked to them, so they must never change once assigned.

**How to generate:** Use Python's `uuid` module:
```python
import uuid
print(str(uuid.uuid4()))  # e.g., "a3f1b2c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c"
```

Generate a unique UUID for every ProblemSet and every Problem in your output. Place the `"id"` field as the **first key** in each object.

---

## 9. Slug Rules

- **Format**: Lowercase letters, numbers, and hyphens only. No underscores, no spaces.
- **Topic slugs**: Unique within the course (e.g., `unit-1-linear-equations`)
- **Concept slugs**: **Globally unique across ALL courses**. If another course might have a similar concept, prefix with course context:
  - Good: `algebra-1-solving-linear-equations` (won't collide with SAT's version)
  - Bad: `solving-linear-equations` (might collide with another course)
- When in doubt, prefix the slug with the course context.

---

## 10. Quality Checklist (Read Before Generating)

- [ ] Every ProblemSet has a unique UUID `"id"` field
- [ ] Every Problem has a unique UUID `"id"` field
- [ ] No duplicate IDs anywhere in the file
- [ ] Every concept has exactly **1 problem set** with exactly **10 problems**
- [ ] Problems are grouped by type: 4 MCQ, then 4 FTB, then 2 FRQ
- [ ] Each problem has an explicit `access_tier`: 2 free MCQ + 2 free FTB = 4 free; the rest are premium
- [ ] All FRQs have `"access_tier": "premium"`
- [ ] Every MCQ has exactly 4 choices with exactly 1 correct
- [ ] Correct answer position is randomized across problems (not always choice B or C)
- [ ] Every FTB has a non-empty `correct_answer` with `||` alternatives where applicable
- [ ] Every problem has exactly 2 hints (free + paid)
- [ ] Every problem has 2-4 solution steps
- [ ] All math uses LaTeX with double-escaped backslashes — no raw Unicode symbols
- [ ] `content_html` is 500-1500 words per concept
- [ ] Concept `access_tier` is always `"free"`
- [ ] Problem set `access_tier` is always `"free"`
- [ ] No AI artifacts: no "actually," / "wait," / "let me reconsider" / "as an AI" in any text
- [ ] No hedging: no "closest to" / "best approximation" in answers
- [ ] All slugs are lowercase-hyphenated, no underscores
- [ ] Concept slugs are globally unique (prefixed with course context if needed)
- [ ] `course_name`, `course_type`, and `difficulty_level` are set at root level
- [ ] `subject_slug` and `course_slug` are set at root level
- [ ] All answers are mathematically/factually correct — double-check every solution

---

## 11. Output Instructions

1. Output **valid JSON only** — no markdown code fences, no commentary before or after
2. The JSON must parse without errors
3. File should be named: `{subject_slug}_{course_slug}.json`
4. If the course is large (many units), I may ask you to generate one unit at a time. In that case, output a valid JSON object with the same root structure but only the topics for that unit. I will merge them later.

---

## YOUR TASK

Generate the complete qhsJSON content file for the following course:

- **Subject slug**: `[FILL IN, e.g., mathematics]`
- **Course slug**: `[FILL IN, e.g., algebra-1]`
- **Course name**: `[FILL IN, e.g., Algebra 1]`
- **Course type**: `[FILL IN: standard / honors / ap / test_prep]`
- **Difficulty level**: `[FILL IN: elementary / middle_school / high_school / ap / college]`

**Topics/Units to include:**
```
[FILL IN — list the units/topics you want, e.g.:
Unit 1: Foundations of Algebra
Unit 2: Solving Linear Equations
Unit 3: Graphing Linear Functions
...
]
```

**Concepts per topic:** [FILL IN — e.g., "3-5 concepts per topic" or list them explicitly]

Generate the complete JSON now, following every rule above exactly.
