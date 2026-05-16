# CoachPrash Launch Checklist

## Pre-Launch Verification

### Database
- [ ] Run `flask db upgrade` to apply all migrations (including performance indexes)
- [ ] Run seed via `/run-seed` endpoint or `flask seed` CLI to load content, testimonials, blog posts, demo students
- [ ] Verify 5 subjects with topics are visible on `/subjects`
- [ ] Verify demo content loads: check each subject has concepts with problems

### Authentication
- [ ] Register a new free account
- [ ] Login with email/password
- [ ] Login with Google OAuth
- [ ] Apply access code PREM2026 to upgrade to premium
- [ ] Verify case-insensitive email login works

### Content & Study Engine
- [ ] Visit a free concept (e.g., /mathematics/algebra-1/what-is-a-linear-equation) — content renders with LaTeX
- [ ] Start a practice quiz — MCQ, fill-in-blank, and FRQ types work
- [ ] Use hints (check cost_points deduction)
- [ ] View step-by-step solutions (premium only)
- [ ] Complete a quiz — results screen shows score, accuracy, and time
- [ ] Verify freemium gating: free user sees first concept free, rest locked
- [ ] Verify premium user sees all concepts and all problems

### Security
- [ ] Hit `/login` POST 6 times rapidly — verify 429 rate limit response
- [ ] Check response headers in devtools: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- [ ] Try submitting `<script>alert(1)</script>` in admin content fields — verify nh3 strips it
- [ ] Visit `/nonexistent-page` — styled 404 error page
- [ ] Verify 500 error page works (test by temporarily breaking a route)

### SEO
- [ ] Visit `/robots.txt` — correct disallow rules and sitemap reference
- [ ] Visit `/sitemap.xml` — valid XML with subjects, topics, free concepts, blog posts
- [ ] View source on home page — meta description, OG tags, canonical URL present
- [ ] Verify favicon (CP monogram) appears in browser tab

### UI
- [ ] Callout boxes render correctly on concept pages (green key, red warning, blue tip)
- [ ] Loading spinners appear on quiz submit/hint/solution buttons during AJAX
- [ ] Card hover animations work (subtle lift on hover)
- [ ] Empty progress dashboard shows friendly message for new users
- [ ] Blog pagination works (if >20 posts)
- [ ] Sidebar navigation works on desktop (collapse/expand) and mobile (overlay drawer)

### Performance
- [ ] Static file responses have `Cache-Control: public, max-age=31536000` header
- [ ] CSS and JS URLs include `?v=3.0` cache-busting parameter
- [ ] Pages load reasonably fast (<2s)

## Environment Variables (Railway)

Required:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — Flask secret key
- `ADMIN_EMAIL` — Admin account email
- `ADMIN_PASSWORD` — Admin account password

Optional:
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — for Google OAuth
- `RAILWAY_BUCKET_ENDPOINT` / `RAILWAY_BUCKET_KEY_ID` / `RAILWAY_BUCKET_SECRET` / `RAILWAY_BUCKET_NAME` — for image hosting
- `ASSET_VERSION` — cache-busting version (default: 3.0)
- `RATELIMIT_STORAGE_URI` — rate limiter backend (default: memory://)

## Post-Launch Monitoring

- [ ] Check Railway logs for any 500 errors
- [ ] Monitor rate limiting — no false positives blocking real users
- [ ] Verify Google OAuth callback works on production domain
- [ ] Check presigned URLs for bucket images are resolving correctly

## Content Expansion Roadmap

Current demo content covers 5 topics (1 per subject). Next priorities:
1. Add more topics to Mathematics (Geometry, Algebra 2, Precalculus)
2. Add AP Physics 1 content
3. Add AP Chemistry content
4. Expand SAT Math (Problem Solving & Data Analysis, Passport to Advanced Math)
5. Add ACT Math and ACT Science content
