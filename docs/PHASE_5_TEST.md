# Phase 5 Testing Manual

**Features:** Coach Dashboard, Messaging Center, Monthly Reports
**Date:** 2026-05-18
**Prerequisites:** Admin account, at least 1 student account with some quiz attempts

---

## 1. Coach Dashboard

### 1.1 Access & Permissions

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 1 | Admin can access | Log in as admin, go to `/admin/coach` | Dashboard loads with stats grid and student table |
| 2 | Student blocked | Log in as student, go to `/admin/coach` | Redirect to home or 403 |
| 3 | Parent blocked | Log in as parent, go to `/admin/coach` | Redirect to home or 403 |
| 4 | Quick link works | Log in as admin, go to `/admin/` (main dashboard), click "Coach Dashboard" | Navigates to `/admin/coach` |

### 1.2 Stats Grid (Top Cards)

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 5 | Total Students | Check the first card | Shows count of all non-admin users |
| 6 | Active (30d) | Check the second card | Shows count of students with at least 1 attempt in last 30 days |
| 7 | Avg Accuracy | Check the third card | Shows average accuracy % across all students (or 0% if no attempts) |
| 8 | At-Risk | Check the fourth card | Shows count of students who are inactive >7 days OR accuracy <50% with 10+ attempts |

### 1.3 At-Risk Alerts

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 9 | Inactive alert | Have a student with attempts but none in last 7+ days | Alert card shows "Inactive for X days" |
| 10 | Low accuracy alert | Have a student with 10+ attempts and <50% accuracy | Alert card shows "Low accuracy: X%" |
| 11 | Alert actions | Click "View Progress" on alert card | Goes to `/admin/coach/student/<id>` |
| 12 | Message from alert | Click "Send Message" on alert card | Goes to `/messages/compose?to=<student_id>` |
| 13 | No alerts | All students active and accuracy >= 50% | "No at-risk students" or section hidden |

### 1.4 Student Table - Sorting

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 14 | Default sort | Load `/admin/coach` | Sorted by last_active descending |
| 15 | Sort by name | Click "Name" column header | Students sorted alphabetically; click again reverses |
| 16 | Sort by tier | Click "Tier" column header | Sorted by free/premium |
| 17 | Sort by accuracy | Click "Accuracy" column header | Sorted by accuracy %; click again reverses |
| 18 | Sort by streak | Click "Streak" column header | Sorted by streak count |
| 19 | Sort by concepts | Click "Concepts" column header | Sorted by completed concept count |
| 20 | Sort indicator | Click any column header | Active column shows arrow (up or down) |

### 1.5 Student Table - Search

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 21 | Search by name | Type part of a student's name, click Search | Table filtered to matching students |
| 22 | Search by email | Type part of a student's email, click Search | Table filtered to matching students |
| 23 | No results | Search for "xyznonexistent" | Empty state message shown |
| 24 | Clear search | Click "Clear" button | All students shown again |

### 1.6 Student Table - Data Display

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 25 | Name links | Click student name in table | Goes to `/admin/coach/student/<id>` |
| 26 | Tier badge | Check tier column | Shows "Free" or "Premium" badge with different colors |
| 27 | Last Active | Check column for student with attempts | Shows date (YYYY-MM-DD format) |
| 28 | Never active | Check column for student with 0 attempts | Shows "Never" |
| 29 | Accuracy color | Student with <50% accuracy | Number shown in red |
| 30 | Accuracy color | Student with >= 80% accuracy | Number shown in green |
| 31 | Streak display | Student with active streak | Shows "X days" or "X day" |
| 32 | Actions column | Check action buttons | "View" and "Msg" buttons present for each student |

### 1.7 Student Detail Page

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 33 | Page loads | Click "View" for a student with attempts | Detail page loads with stats, subject progress, recent activity |
| 34 | Stats grid | Check the 5 stat cards | Shows: Concepts Completed, In Progress, Total Attempts, Accuracy%, Day Streak |
| 35 | Subject progress | Check subject section | Shows each subject with X/Y completed, percentage, progress bar |
| 36 | Recent activity | Check activity timeline | Shows up to 20 most recent attempts with correct/incorrect labels |
| 37 | Correct attempt | Check a correct attempt in timeline | Shown in green with "Correct" label |
| 38 | Incorrect attempt | Check an incorrect attempt | Shown in red with "Incorrect" label |
| 39 | Send Message | Click "Send Message" button | Goes to `/messages/compose?to=<student_id>` |
| 40 | Back button | Click "Back to Coach Dashboard" | Returns to `/admin/coach` |
| 41 | Empty student | View detail for student with 0 attempts | Shows 0s for stats, empty states for progress/activity |
| 42 | Invalid student | Go to `/admin/coach/student/fake-uuid` | 404 page |

---

## 2. Messaging Center

### 2.1 Sidebar Integration

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 43 | Admin sees link | Log in as admin | "Messages" link visible in sidebar with speech bubble icon |
| 44 | Student sees link | Log in as student | "Messages" link visible in sidebar |
| 45 | Parent sees link | Log in as parent | "Messages" link visible in sidebar |
| 46 | Not logged in | View sidebar while logged out | No "Messages" link |
| 47 | Unread badge | Have unread messages for user | Badge with count appears next to "Messages" |
| 48 | No unread | All messages read | No badge shown |
| 49 | Active highlight | Navigate to `/messages/` | "Messages" link has active/highlighted style |

### 2.2 Inbox

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 50 | Empty inbox | Log in as user with no messages | "No messages yet." with "Send your first message" button |
| 51 | Thread list | Log in as user with messages | Threads listed, sorted by most recently updated first |
| 52 | Thread card info | Check a thread card | Shows: participant names, date, subject, message preview (max 100 chars) |
| 53 | Unread thread | Thread has unread messages | Thread card highlighted, unread badge with count shown |
| 54 | Read thread | All messages read in thread | No highlight, no badge |
| 55 | Click thread | Click on a thread card | Goes to `/messages/thread/<id>` |
| 56 | New Message button | Click "New Message" | Goes to `/messages/compose` |

### 2.3 Compose Message - Admin

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 57 | Recipient list | Log in as admin, go to `/messages/compose` | Dropdown shows ALL active non-admin users with format "username (role)" |
| 58 | Admin not in list | Check recipient dropdown | Admin's own account not listed |
| 59 | Pre-select recipient | Go to `/messages/compose?to=<student_id>` | That student is pre-selected in dropdown |
| 60 | Send message | Fill all fields, click Send | Thread created, redirected to thread view, success flash |
| 61 | Empty subject | Submit with empty subject | Validation error |
| 62 | Empty body | Submit with empty body | Validation error |
| 63 | Empty recipient | Submit without selecting recipient | Validation error |

### 2.4 Compose Message - Student

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 64 | Recipient list | Log in as student, go to `/messages/compose` | Dropdown shows only admin(s) with label "username (Coach)" |
| 65 | Send to coach | Fill fields, click Send | Thread created with admin as participant |

### 2.5 Compose Message - Parent

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 66 | Recipient list | Log in as parent, go to `/messages/compose` | Dropdown shows only admin(s) with label "username (Coach)" |
| 67 | Send to coach | Fill fields, click Send | Thread created with admin as participant |

### 2.6 Thread View & Replies

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 68 | View conversation | Open a thread | Messages shown in chronological order |
| 69 | Sent messages | Messages from current user | Displayed as right-aligned bubbles (sent style) |
| 70 | Received messages | Messages from other user | Displayed as left-aligned bubbles (received style) |
| 71 | Message metadata | Check each message bubble | Shows sender name (bold) and timestamp |
| 72 | Newlines preserved | Send message with multiple lines | Newlines rendered as line breaks (nl2br filter) |
| 73 | Mark as read | Open thread with unread messages | Unread messages marked as read; sidebar badge count decreases |
| 74 | Reply | Type in reply box, click "Send Reply" | New message appears at bottom of conversation |
| 75 | Empty reply | Submit reply with empty body | Validation error, flash message |
| 76 | Back to inbox | Click "Back to Inbox" | Returns to `/messages/` |

### 2.7 Security & Access Control

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 77 | Non-participant blocked | Log in as user NOT in thread, go to `/messages/thread/<id>` | 403 Forbidden |
| 78 | Non-participant reply | POST to `/messages/thread/<id>/reply` as non-participant | 403 Forbidden |
| 79 | Logged out access | Go to `/messages/` while logged out | Redirect to login |
| 80 | Rate limit compose | Send 11+ new messages in 1 minute | Rate limit error after 10 |
| 81 | Rate limit reply | Send 21+ replies in 1 minute | Rate limit error after 20 |

### 2.8 Multi-Message Flow

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 82 | Full conversation | Admin sends to student, student replies, admin replies | All 3 messages visible in thread for both users |
| 83 | Inbox updates | After reply in step 82 | Thread moves to top of inbox for both users |
| 84 | Unread tracking | Admin sends message | Student sees unread badge in sidebar and inbox |

---

## 3. Monthly Reports

### 3.1 Access & Navigation

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 85 | Admin access | Log in as admin, go to `/admin/reports` | Reports page loads with generate form and reports table |
| 86 | Quick link | From `/admin/`, click "Monthly Reports" | Navigates to `/admin/reports` |
| 87 | Student blocked | Log in as student, go to `/admin/reports` | Redirect or 403 |
| 88 | Parent blocked | Log in as parent, go to `/admin/reports` | Redirect or 403 |

### 3.2 Generate Report Form

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 89 | Form elements | Check the generate form | Student dropdown, month select, year input, Generate button |
| 90 | Default month | Check month dropdown | Current month pre-selected |
| 91 | Default year | Check year input | Current year pre-filled |
| 92 | Student list | Check student dropdown | All non-admin users listed |

### 3.3 Report Generation

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 93 | Generate report | Select student with attempts, current month/year, click Generate | Report created, redirected to report view |
| 94 | Duplicate prevention | Generate same student/month/year again | Error flash: report already exists |
| 95 | Student with no attempts | Generate report for student with 0 attempts | Report created with 0% accuracy, 0 attempts, appropriate messaging |
| 96 | Invalid student | Submit form with no student selected | Validation error |

### 3.4 Report Content (HTML View)

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 97 | View report | Click "View" on a generated report | Report page loads at `/admin/reports/<id>` |
| 98 | Student info | Check report header | Shows student name and report period (e.g., "May 2026") |
| 99 | Stats grid | Check stats section | Shows: Accuracy%, Total Attempts, Concepts Started, Concepts Completed |
| 100 | Accuracy trend | Check trend section | Shows current month vs previous month accuracy with up/down indicator |
| 101 | Strongest topics | Check strengths table | Top 3 topics by accuracy with attempt counts |
| 102 | Weakest topics | Check weaknesses table | Bottom 3 topics by accuracy with attempt counts |
| 103 | Recommendations | Check recommendations section | Auto-generated tips based on performance data |
| 104 | Download PDF btn | Check for PDF button | "Download PDF" button present |
| 105 | Back to reports | Click back button | Returns to `/admin/reports` |

### 3.5 Reports Table

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 106 | Table columns | Check reports table | Student, Period, Accuracy%, Attempts, Generated date, Actions |
| 107 | View action | Click "View" button | Goes to report HTML view |
| 108 | PDF action | Click "PDF" button | Downloads PDF file |
| 109 | Empty table | No reports generated yet | Empty state message |
| 110 | Multiple reports | Generate reports for different students/months | All shown in table |

### 3.6 PDF Download

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 111 | PDF downloads | Click "PDF" on a report | Browser downloads a PDF file |
| 112 | PDF filename | Check downloaded filename | Format: `report_studentname_month_year.pdf` |
| 113 | PDF content | Open the PDF | Contains: CoachPrash branding, student name, period, all stats, topics, recommendations |
| 114 | PDF layout | Check formatting | Clean layout, no sidebar, no broken styles, navy/gold branding |
| 115 | PDF from view | Click "Download PDF" from report view page | Same PDF downloads |

---

## 4. Shared Progress Utility

### 4.1 Consistency Across Views

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 116 | Student dashboard | Log in as student, go to `/progress/` | Shows stats (accuracy, streak, subject progress, recent activity) |
| 117 | Parent view | Log in as parent, view linked student | Shows same stats as student sees in their own dashboard |
| 118 | Coach detail | Log in as admin, view student in coach dashboard | Shows same stats as student/parent views |
| 119 | Numbers match | Compare accuracy/streak/concepts across all 3 views for same student | All values identical |

---

## 5. Empty States & Edge Cases

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 120 | Zero students | Remove all non-admin users, visit `/admin/coach` | Stats show 0, empty table with message |
| 121 | Zero attempts | Student with account but no quiz attempts | Coach dashboard shows "Never" for last active, 0% accuracy, 0 streak |
| 122 | Zero messages | Fresh account, visit `/messages/` | "No messages yet" with CTA button |
| 123 | Zero reports | Visit `/admin/reports` with none generated | Empty state in reports table |
| 124 | Invalid thread ID | Go to `/messages/thread/fake-uuid` | 404 page |
| 125 | Invalid report ID | Go to `/admin/reports/fake-uuid` | 404 page |

---

## 6. Mobile / Responsive

| # | Test | Steps | Expected |
|---|------|-------|----------|
| 126 | Coach dashboard | View `/admin/coach` on mobile width | Stats cards stack, table scrolls horizontally |
| 127 | Student detail | View coach student detail on mobile | Stats cards stack, timeline readable |
| 128 | Inbox | View `/messages/` on mobile | Thread cards full width, readable |
| 129 | Thread view | View message thread on mobile | Bubbles fit screen, reply form usable |
| 130 | Compose | View compose form on mobile | Form fields full width |
| 131 | Reports | View `/admin/reports` on mobile | Form and table responsive |

---

## Quick Test Checklist

For a fast smoke test, run through these key scenarios:

- [ ] **Admin**: `/admin/coach` loads with student data
- [ ] **Admin**: Click a student name to see detail page
- [ ] **Admin**: Click "Send Message" from student detail
- [ ] **Admin**: Send a message to a student
- [ ] **Student**: Log in, see unread badge in sidebar
- [ ] **Student**: Open inbox, see the message thread
- [ ] **Student**: Reply to the message
- [ ] **Admin**: See the reply in inbox
- [ ] **Admin**: Go to `/admin/reports`, generate a report
- [ ] **Admin**: View the report in HTML
- [ ] **Admin**: Download the report as PDF
- [ ] **Parent**: Log in, send message to coach, see reply
- [ ] **Parent**: Verify cannot access `/admin/coach` or `/admin/reports`
