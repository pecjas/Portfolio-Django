# Deploying to PythonAnywhere

Written for the modernization release (Phases 1–5), but the shape holds for
every later deploy. Paths are the real ones for the `stagingportfolio` account,
confirmed against the server on 2026-09-17; for a different account, swap the
username and the project directory, which the Web tab shows as **Source code**
and **Working directory**.

This release is unusual in two ways, and both can stop the deploy dead. Check
them *before* you touch anything, in **Step 0**.

---

## Step 0 — Two blockers, checked first

Open a **Bash console** on PythonAnywhere. The staging server's real values,
confirmed on 2026-09-17:

| Thing | Value |
|---|---|
| Username | `stagingportfolio` |
| Project root | `~/Portfolio-Django` (where `manage.py` lives) |
| Current virtualenv | `myvirtualenv` — Python 3.8.10, Django 3.0.2 |
| Branch checked out | `master` |

### 0a. Python version — CONFIRMED A BLOCKER (checked 2026-09-17)

The staging server runs virtualenv `myvirtualenv` on **Python 3.8.10 with
Django 3.0.2**:

```
/home/stagingportfolio/.virtualenvs/myvirtualenv/lib/python3.8/site-packages/django
```

Django 5.2 requires **Python 3.10 or newer**, so that virtualenv cannot be
upgraded in place — `pip install -r requirements.txt` will refuse. You need a
new one. **Appendix A** has the steps; do it as part of Step 5.

Python 3.8 reached end of life in October 2024 and Django 3.0 in April 2021, so
this is worth doing regardless of the redesign.

To re-check at any point:

```bash
workon myvirtualenv
python --version
python -c "import django; print(django.get_version())"
```

### 0b. Migration bookkeeping

`main/migrations/` used to be in `.gitignore`, so the migration files on the
server were generated there and were never in git. This release tracks them.
Two consequences, and you need to know which situation you are in.

```bash
cd ~/Portfolio-Django
ls main/migrations/
python manage.py showmigrations main
```

Read the `showmigrations` output:

| What you see | What it means | What to do |
|---|---|---|
| `[X] 0001_initial` | Django has recorded the initial migration | Nothing special. Plain `migrate` in Step 5. |
| `[ ] 0001_initial` | Tables exist but Django has no record of them | You must fake it. See **Step 5, variant B**. |
| `(no migrations)` | The app has no migration files here at all | Same as the row above — **variant B**. |

The site works today, so the tables definitely exist. The only question is
whether `django_migrations` knows about them. Running a plain `migrate` in the
`[ ]` case fails with *"table main_project already exists"* — which is loud and
harmless, but variant B avoids it.

---

## Step 1 — Local: commit everything

You have work that is staged but not committed, and one file that is not
tracked at all.

```bash
git status --short
```

The untracked `main/static/main/files/jason-peck-resume.pdf` is your CV. **If
you do not add it, the Download CV button will not appear in production** — the
template only renders the link when the file exists.

```bash
git add main/static/main/files/jason-peck-resume.pdf
git add -A
git status --short
```

Decide on `source-images/` before committing. It holds the full-resolution
original photo (469 KB) that `tools/images/make_portrait.py` and `make_og.py`
read from. Commit it and the generators work on any clone; ignore it and you
must keep the original somewhere yourself.

Then commit and push:

```bash
git commit -m "Modernization: responsive images, share card, error pages, tooling"
git push origin modernization
```

## Step 2 — Local: merge to the deployed branch

Find out which branch the web app actually serves — do this on the server, do
not assume:

```bash
cd ~/Portfolio-Django && git branch --show-current
```

Then locally, merging into `staging` as the example:

```bash
git checkout staging
git merge modernization
git push origin staging
```

Run the tests once more on the merged branch before you go near the server:

```bash
.venv/Scripts/python.exe manage.py test
```

36 tests should pass.

## Step 3 — Server: back up

SQLite, so the database is one file. Do this every time; it is the only thing
here that cannot be rebuilt.

```bash
cd ~/Portfolio-Django
cp db.sqlite3 ~/db.sqlite3.$(date +%Y%m%d-%H%M)
cp -r main/migrations ~/migrations-backup-$(date +%Y%m%d-%H%M)
git rev-parse --short HEAD > ~/last-deployed-commit.txt
cat ~/last-deployed-commit.txt
```

That last file is your rollback target. Write it down.

Your `env.py` and `media/` are untracked and git will not touch them. **No
`env.py` changes are needed for this release** — I compared the settings keys
against what production already has and they are identical.

## Step 4 — Server: switch branch and pull

PythonAnywhere has no concept of a branch. The **Source code** path on the Web
tab points at a directory, and the app runs whatever is checked out there. So
"pointing the site at staging" just means checking out `staging` in
`~/Portfolio-Django` — there is no setting to change and no need to touch the
WSGI file.

The old server-side migration files sit exactly where the incoming tracked ones
need to go. Move them aside first, or the checkout is unpredictable — git's
behaviour when a file being written already exists as an ignored file has
changed between versions.

```bash
cd ~/Portfolio-Django
mv main/migrations/0*.py ~/migrations-backup-*/ 2>/dev/null
ls main/migrations/          # should show only __init__.py
```

Then switch:

```bash
git status                   # must be clean; stash or discard anything listed
git fetch origin
git checkout staging         # creates a local branch tracking origin/staging
git pull origin staging
git log --oneline -1
ls main/migrations/          # should now show 0001, 0002, 0003
```

`git branch --show-current` should now say `staging`, and the prompt's `(master)`
will change to `(staging)`.

If `git checkout staging` complains that the branch is unknown, you have not
pushed it yet — go back to Step 2. If it complains about local changes, see what
they are first (`git status`); `env.py`, `db.sqlite3`, `media/` and `static/` are
all ignored and will not be listed.

Do **not** delete `main/migrations/__init__.py`. Without it the directory stops
being a Python package and Django stops seeing the migrations.

## Step 5 — Server: dependencies and migrations

The current virtualenv is on Python 3.8 and cannot take Django 5.2, so build the
new one now — **Appendix A**, which ends with `pip install -r requirements.txt`.
Come back here once `django.get_version()` reports `5.2.17`.

```bash
workon portfolio-py310
cd ~/Portfolio-Django
python --version
python -c "import django; print(django.get_version())"   # expect 5.2.17
```

### Variant A — `showmigrations` showed `[X] 0001_initial`

```bash
python manage.py migrate
```

Expect `0002_project_slug` and `0003_project_is_personal` to apply.

### Variant B — `showmigrations` showed `[ ]` or nothing

Tell Django the initial migration is already in the database, then apply the
rest:

```bash
python manage.py migrate main 0001 --fake
python manage.py migrate
```

`--fake` records `0001_initial` as applied without running it, which is exactly
right when the tables are already there.

### Either way, verify

```bash
python manage.py showmigrations main
```

All three should show `[X]`. Then confirm the data survived:

```bash
python manage.py shell -c "from main.models import Project; print(Project.objects.count(), 'projects'); print([p.slug for p in Project.objects.all()][:5])"
```

Every project must have a non-empty slug — `0002` backfills them, and the
project pages 404 without them.

## Step 6 — Server: static files

This release deletes eight old banner images and adds several new ones, so
clear rather than overlay. `--clear` empties `STATIC_ROOT` first, which drops
the ~1 MB of orphaned files that would otherwise linger.

```bash
python manage.py collectstatic --clear --noinput
```

There is a few-second window during the clear where static files 404. On a
portfolio site that is fine; if it bothers you, use plain `collectstatic
--noinput` and accept the orphans.

Confirm the Web tab's **Static files** mapping still points at the right place:

| URL | Directory |
|---|---|
| `/static/` | `/home/stagingportfolio/Portfolio-Django/static` |
| `/media/` | whatever `media_root` is set to in your `env.py` |

## Step 7 — Server: deployment check, then reload

Now that `DEBUG` is genuinely `False`, this is the honest place to run it:

```bash
python manage.py check --deploy
```

Expect exactly three warnings, all known:

- **W005** and **W021** — HSTS subdomains and preload. Deliberate; `SECURE_HSTS_SECONDS` starts at one hour on purpose and should stay there until HTTPS has been stable for a while.
- **W009** — `SECRET_KEY` under 50 characters. Real. Fix it when you rotate keys; it is not a release blocker.

Anything else is new and worth stopping for.

Then hit the big green **Reload** button on the **Web** tab. Nothing you have
done so far is live until you do.

## Step 8 — Verify the live site

Work through these in a browser:

- [ ] Home page loads, hero banner crossfades between the name and "Solution Architect"
- [ ] Profile photo is sharp and the three text segments are spaced
- [ ] **Download CV** button appears and the PDF downloads
- [ ] Portfolio filters work, and the URL updates as you filter
- [ ] A project page opens at `/projects/<slug>/`
- [ ] An old-style link `/project/?id=<title>` still redirects
- [ ] Contact form sends (check reCAPTCHA is not blocking it)
- [ ] Visit a nonsense URL — you should get the **styled** 404, not Django's yellow debug page. If you see the debug page, `DEBUG` is `True` in your server `env.py` and must be fixed immediately.
- [ ] Dark mode toggle persists across a reload
- [ ] Check the browser console for errors

Then check the share card, which needs the site to be publicly reachable:

- **LinkedIn Post Inspector** — `linkedin.com/post-inspector/`. Paste the site URL. This also force-refreshes LinkedIn's cache, which otherwise holds about 7 days.
- **Facebook Sharing Debugger** — `developers.facebook.com/tools/debug/`
- Paste the link into Slack and watch it unfurl

## Step 9 — Content tasks that need the production admin

These are data, not code, so they can only be done after deploy:

1. **Fix the dual "Present."** Admin → Jobs → *Interoperability Engineer / Developer* (Epic Systems) → set **End date**. It is currently null, so the site claims you work at Epic and Esker simultaneously. Your Esker history starts 24 Aug 2020.
2. **Update the "Portfolio Website" project description.** It still says Materialize was used for the base CSS. Materialize is gone; add the AI / Claude Code callout you wanted.
3. **Set `is_personal` on any project that needs it.** The migration seeded it from whether a GitHub link existed, which is a guess. It is editable straight from the project list.

---

## Step 10 — After this deploy: dropping the JobDetail table

Migration `0012` moved every job bullet out of the `JobDetail` table and onto
`Job.responsibilities`, one bullet per line. **It does not drop the table.** The
36 rows are still sitting there untouched, deliberately, so that this deploy has
something to roll back to.

Once the live Experience section reads correctly — six jobs, bullets in the
right order, nothing missing — the table can go:

1. Open the Experience accordion on the live site and check every job against
   what you remember. Order matters: the old table had no ordering declared, so
   the backfill froze the order by primary key, which is the order the rows were
   created in.
2. Ask Claude for the follow-up migration that deletes the model, or write a
   `migrations.DeleteModel(name="JobDetail")` migration yourself, and remove the
   `JobDetail` class from `main/models.py`.
3. Deploy that on its own.

Until then, editing bullets happens in **one** place: Admin → Jobs → the job →
**Responsibilities**, one bullet per line. The Job details admin page is gone.
Anything still in the `JobDetail` table is dead data and is not rendered.

---

## Rollback

If the site is broken and you cannot see why, get back to known-good first and
debug afterwards.

```bash
cd ~/Portfolio-Django
git reset --hard $(cat ~/last-deployed-commit.txt)
cp ~/db.sqlite3.<timestamp> db.sqlite3
workon myvirtualenv          # the old Python 3.8 / Django 3.0.2 environment
python manage.py collectstatic --clear --noinput
```

Then **Reload** on the Web tab.

Restoring the database matters: `0003_project_is_personal` drops the
`html_project` column, and old code expects it. Code alone is not enough.

If you built a new virtualenv in Appendix A, the old one is untouched — point
the Web tab back at it and reload.

### Reading the error

PythonAnywhere writes three logs, linked from the Web tab. The **error log** is
the one with the traceback:

```
/var/log/stagingportfolio.pythonanywhere.com.error.log
```

```bash
tail -50 /var/log/stagingportfolio.pythonanywhere.com.error.log
```

---

## Appendix A — Building a new virtualenv for Python 3.10+

Only needed if Step 0a found Python 3.9 or older. The old virtualenv is left
alone, so this is reversible.

Needed on this server: it is on Python 3.8.10. The existing `myvirtualenv` is
left completely untouched, which is what makes this reversible.

**Switch to the staging branch first** (Step 4) — `requirements.txt` does not
exist on `master`, so there is nothing to install from until you do.

First see what your account offers, and take the newest:

```bash
ls /usr/bin/python3.*
```

```bash
mkvirtualenv --python=/usr/bin/python3.10 portfolio-py310
```

That creates it and activates it. Then:

```bash
cd ~/Portfolio-Django
pip install -r requirements.txt
python --version
python -c "import django; print(django.get_version())"   # expect 5.2.17
```

Now point the web app at it: **Web** tab → **Virtualenv** → replace

```
/home/stagingportfolio/.virtualenvs/myvirtualenv
```

with

```
/home/stagingportfolio/.virtualenvs/portfolio-py310
```

**Check the Python version shown on the Web tab as well.** PythonAnywhere runs
your app under the version configured there, and it needs to agree with the
virtualenv's. If the tab offers a selector, set it to match. If it does not,
you may need to create a new web app on the newer Python and move the domain
across — more involved, so find this out before you start.

To roll back: put the old path back in that field and reload. `myvirtualenv`
still has Django 3.0.2 in it, untouched.
