# Parent Portal — End-to-End Test Guide

Complete walkthrough for testing the Parent Portal feature from start to finish.

---

## Prerequisites

- Flask server running locally (`flask run --debug`)
- Database seeded with demo data (`flask seed` or `/run-seed/<ADMIN_PASSWORD>`)
- Admin credentials: `admin@coachprash.com` / your `ADMIN_PASSWORD` from `.env`

### Existing Test Accounts

| Username | Email | Tier | Has Password |
|----------|-------|------|-------------|
| DemoStudent | demo.student@example.com | Premium | Yes |
| DemoFree | demo.free@example.com | Free | Yes |

---

## Part A: Generate Practice Data as a Student

**Goal:** Ensure the student has quiz attempts so the parent portal has data to display.

1. Open `http://127.0.0.1:5000` in your browser.

2. Log in as DemoStudent:
   - Go to `http://127.0.0.1:5000/auth/login`
   - Email: `demo.student@example.com`
   - Password: (from seed.py)

3. Do some practice to generate progress data:
   - Click **Subjects** in the sidebar
   - Pick any subject (e.g., Mathematics)
   - Click a topic (e.g., Algebra 1)
   - Click a concept (e.g., "Solving Linear Equations")
   - Click **Start Practice**
   - Answer 3-5 questions (get some right, some wrong — this creates `AttemptLog` records)
   - Complete the quiz (this creates a `StudentProgress` record with a mastery score)

4. Check **My Progress** (chart icon in sidebar):
   - Stats grid: Concepts Completed, In Progress, Problems Attempted, Accuracy, Day Streak
   - Subject progress bars
   - Recent activity timeline
   - This is exactly what the parent will see later in read-only mode.

5. Log out.

---

## Part B: Generate a Parent Link Code (as Admin)

**Goal:** Admin creates a link code tied to the student's account.

1. Log in as Admin:
   - Email: `admin@coachprash.com`
   - Password: your `ADMIN_PASSWORD`

2. Navigate to the student:
   - Click **Admin** (gear icon) in sidebar
   - Click **Manage Students** (or go to `http://127.0.0.1:5000/admin/students`)
   - Find **DemoStudent** in the list
   - Click **Edit**

3. Generate the Parent Link Code:
   - Scroll down to the **"Parent Access"** section at the bottom
   - Click **"Generate Parent Link Code"**
   - A green flash message appears: `Parent link code generated: XXXXXXXX (expires in 7 days)`
   - The code also appears in the **Link Codes** table, showing status "Active"
   - **Copy this 8-character code** (e.g., `A3B7XK9M`)

### How Link Codes Work

| Property | Value |
|----------|-------|
| Format | 8 uppercase alphanumeric characters (e.g., `A3B7XK9M`) |
| Tied to | One specific student |
| Expiry | 7 days from generation |
| Usage | Single-use — marked "Used" after one parent links with it |
| Multiple codes | You can generate multiple codes for the same student (e.g., for two parents) |

### How you would share the code in real life

- In person during a parent-teacher meeting
- Via email to the parent
- On a printed handout
- The parent does NOT need the student's login credentials — only the code

4. Log out of the admin account.

---

## Part C: Register as a Parent and Link the Code

**Goal:** Create a parent account and use the code to link to the student.

1. Register a new account (the parent's account):
   - Go to `http://127.0.0.1:5000/auth/register`
   - Username: `TestParent`
   - Email: `testparent@example.com`
   - Password: `parent1234` (min 8 chars)
   - Confirm Password: `parent1234`
   - Leave **Access Code blank** (that field is for student tier upgrades, not parent linking)
   - Click **Register**
   - You are now logged in as a regular student (role = `student`)

2. Navigate to the Link page:
   - Go to `http://127.0.0.1:5000/parent/link`
   - You see a form titled **"Link Your Child's Account"**
   - Instructions: "Enter the 8-character parent link code provided by your child's teacher or administrator."

3. Enter the code:
   - Type the 8-character code from Part B (e.g., `A3B7XK9M`)
   - The input auto-uppercases and has letter-spacing for readability
   - Click **"Link My Child"**

4. What happens behind the scenes:
   - System validates the code (exists, not expired, not already used)
   - Creates a `ParentStudentLink` record connecting your account to DemoStudent
   - Marks the code as "Used" so nobody else can reuse it
   - Upgrades your role from `student` to `parent`
   - Flashes success: `Successfully linked to DemoStudent!`
   - Redirects to the Parent Dashboard

### Error Scenarios to Test

| Action | Expected Message |
|--------|-----------------|
| Enter a wrong code | "Invalid link code. Please check and try again." |
| Enter the same code again (already used) | "This link code has already been used." |
| Enter an expired code (wait 7 days or modify DB) | "This link code has expired. Please ask your admin for a new one." |
| Link to your own account | "You cannot link to your own account." |
| Already linked to this student | "You are already linked to this student." |

---

## Part D: View Your Child's Progress (as Parent)

**Goal:** See the parent dashboard and detailed progress view.

### Parent Dashboard (`/parent/`)

After linking, you are redirected here. You see a card for DemoStudent showing:

- Username and tier badge (Premium)
- **Concepts Completed** count
- **Problems Attempted** count
- **Accuracy** percentage
- **Last Active** date
- A **"View Details"** button

A **"Link Another Child"** button appears at the bottom.

### Student Progress View

Click **"View Details"** on DemoStudent's card. This takes you to `/parent/student/<student_id>`.

This is a read-only version of the student's My Progress page:

- **Breadcrumb**: `Parent Dashboard >> DemoStudent`
- **Stats grid**: Concepts Completed, In Progress, Problems Attempted, Accuracy %, Day Streak
- **Subject Progress**: bars showing completion per subject (e.g., "Mathematics 1/4 (25%)")
- **Recent Activity**: timeline of the student's last 20 quiz attempts with checkmarks (correct) and X marks (incorrect), concept name, and timestamps

### Freemium Behavior

| Student Tier | Parent Sees |
|-------------|-------------|
| Premium | Full data — all stats, mastery scores, detailed activity |
| Free | Yellow banner: "Limited View — [name] is on the Free tier. Upgrade to Premium for full progress tracking..." with basic stats |

To test freemium: generate a code for DemoFree (free tier) and link a second parent account.

### Sidebar Navigation

The sidebar now shows **"My Children"** (person icon) instead of "My Progress". This link is highlighted when on any parent page.

### Linking Multiple Children

1. Click **"Link Another Child"** at bottom of dashboard (or go to `/parent/link`)
2. Enter a new code (generated from admin for a different student)
3. Both children appear as cards on the parent dashboard

---

## Part E: Verify in Admin (as Admin)

**Goal:** Confirm admin can see and manage parent-student relationships.

1. Log out of the parent account.

2. Log in as Admin.

3. Check the Admin Dashboard:
   - A new stat card shows **"Parent Accounts: 1"**
   - A **"Parents"** quick link appears in the Quick Links grid

4. Click **"Parents"** (or go to `/admin/parents`):
   - Table shows: Parent username, email, linked students (as badges), joined date
   - Action column: **"Unlink [StudentName]"** button for each link

5. Go to **Manage Students** and **Edit** DemoStudent:
   - Scroll to **Parent Access** section
   - Link code now shows status **"Used"**
   - **Linked Parents** table shows `TestParent` with email and link date

6. Test removing a link:
   - On the Manage Parents page, click **"Unlink DemoStudent"** next to TestParent
   - Confirm the dialog
   - Link is deleted
   - If the parent has no remaining links, their role reverts from `parent` to `student`

---

## Quick Test Checklist

| # | Test | Expected Result | Pass? |
|---|------|----------------|-------|
| 1 | Student logs in, completes a quiz | AttemptLog + StudentProgress records created | |
| 2 | Student views My Progress | Stats, subject bars, activity timeline display | |
| 3 | Admin generates code for student | 8-char code shown in flash + table, status "Active" | |
| 4 | Parent registers normally | Account created with role=student, tier=free | |
| 5 | Parent enters valid code at /parent/link | Role upgrades to parent, linked to student, redirected to dashboard | |
| 6 | Parent dashboard shows child card | Username, tier badge, stats, last active, View Details button | |
| 7 | Parent clicks View Details | Full read-only progress page (stats, subjects, activity) | |
| 8 | Parent tries another student's ID in URL | 403 Forbidden | |
| 9 | Wrong code entered | "Invalid link code" error | |
| 10 | Used code entered again | "Already been used" error | |
| 11 | Self-linking attempted | "Cannot link to your own account" error | |
| 12 | Already-linked student code | "Already linked to this student" info | |
| 13 | Admin dashboard shows parent count | "Parent Accounts: 1" stat card | |
| 14 | Admin manage parents page | Parent listed with linked student badges | |
| 15 | Admin removes parent-student link | Link deleted, role reverts if no links remain | |
| 16 | Sidebar shows "My Children" for parent | Person icon, highlighted on parent pages | |
| 17 | Sidebar shows "My Progress" for student | Chart icon (not "My Children") | |
| 18 | Free-tier student linked | Parent sees limited view + upgrade banner | |
| 19 | Premium-tier student linked | Parent sees full stats and activity | |
| 20 | Mobile responsive | Parent cards and progress page render on narrow screens | |

---

## Cleanup After Testing

To remove test data, log in as admin and:

1. Go to `/admin/parents` and unlink any test parent-student links
2. Go to `/admin/students` and deactivate or note the test parent account
3. Or reset the DB entirely: `/run-drop-all/<ADMIN_PASSWORD>` then redeploy + re-seed
