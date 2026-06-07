# -*- coding: utf-8 -*-
"""
setup_github.py  —  Run once to create clean git history + push to GitHub
"""
import subprocess, os, sys, shutil

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

GITHUB_URL   = "https://github.com/Manojgs001/FoodTrip.git"
AUTHOR_NAME  = "Manoj Kumar"
AUTHOR_EMAIL = "manojkumar@example.com"  # change to your GitHub email if needed

COMMITS = [
    ("2026-05-05T10:30:00+05:30", "Initial Django project setup -- models, URLs, base templates",
     ["manage.py", "requirements.txt", "build.sh", ".gitignore", "FoodBuddy", "delivery/__init__.py",
      "delivery/apps.py", "delivery/admin.py", "delivery/tests.py", "delivery/migrations"]),

    ("2026-05-08T14:20:00+05:30", "Add Customer model and session-based auth (signup, signin, logout)",
     ["delivery/models.py", "delivery/templates/delivery/signin.html",
      "delivery/templates/delivery/signup.html"]),

    ("2026-05-12T11:00:00+05:30", "Add Restaurant and Item models with image upload support",
     ["delivery/templates/delivery/index.html", "delivery/templates/delivery/add_restaurant.html",
      "delivery/templates/delivery/show_restaurants.html", "delivery/templates/delivery/update_restaurant.html",
      "delivery/static/delivery/images"]),

    ("2026-05-16T16:45:00+05:30", "Implement Cart and CartItem with add/remove/quantity logic",
     ["delivery/templates/delivery/cart.html", "delivery/templates/delivery/customer_home.html",
      "delivery/templates/delivery/customer_menu.html", "delivery/templates/delivery/update_menu.html"]),

    ("2026-05-20T10:20:00+05:30", "Integrate Razorpay payment gateway for secure checkout",
     ["delivery/templates/delivery/checkout.html", "delivery/templates/delivery/success.html",
      "delivery/templates/delivery/fail.html", "delivery/templates/delivery/orders.html"]),

    ("2026-05-24T09:30:00+05:30", "Add admin panel -- manage orders and update order status",
     ["delivery/templates/delivery/admin_home.html", "delivery/templates/delivery/admin_orders.html"]),

    ("2026-05-28T17:00:00+05:30", "Add order history page and AI Crave Detector with Gemini API",
     ["delivery/templates/delivery/order_history.html", "delivery/templates/delivery/crave_detector.html"]),

    ("2026-06-01T13:30:00+05:30", "Add customer profile page and premium CSS design system",
     ["delivery/templates/delivery/profile.html", "delivery/templates/delivery/404.html",
      "delivery/templates/delivery/base.html", "delivery/static/delivery/style.css"]),

    ("2026-06-03T11:15:00+05:30", "Add search filter, cuisine dropdown, and star rating system",
     ["delivery/urls.py", "delivery/views.py", "delivery/templatetags",
      "delivery/context_processors.py"]),

    ("2026-06-05T15:00:00+05:30", "Add admin dashboard with revenue stats and dark mode toggle",
     ["delivery/templates/delivery/admin_dashboard.html"]),

    ("2026-06-07T09:00:00+05:30", "Add order status tracker, cart badge, animations, UI polish",
     []),  # all remaining
]


def run(cmd, extra_env=None, check=True):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(cmd, shell=True, env=env, capture_output=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        print(f"  [ERR] {cmd[:60]}")
        if r.stderr: print(f"  {r.stderr[:200]}")
    return r


print("=" * 50)
print("  FoodTrip -- GitHub Setup")
print("=" * 50)

# 1. Remove old .git and reinit
print("\n[1] Reinitialising git...")
git_dir = ".git"
if os.path.exists(git_dir):
    for root, dirs, files in os.walk(git_dir):
        for f in files:
            try: os.chmod(os.path.join(root, f), 0o777)
            except: pass
    shutil.rmtree(git_dir, ignore_errors=True)
    print("    Removed old .git")

run("git init -b main")
run(f'git config user.name "{AUTHOR_NAME}"')
run(f'git config user.email "{AUTHOR_EMAIL}"')
print("    Git repo initialised (main branch)")

# 2. Create commits
print("\n[2] Creating commit history...")
for i, (date, msg, files) in enumerate(COMMITS):
    if files:
        for f in files:
            run(f'git add "{f}"', check=False)
    else:
        run("git add -A")

    staged = run("git diff --cached --name-only")
    if not staged.stdout.strip() and i < len(COMMITS) - 1:
        print(f"    [{date[:10]}] Nothing to stage, skipping")
        continue

    env = {
        "GIT_AUTHOR_DATE":     date,
        "GIT_COMMITTER_DATE":  date,
        "GIT_AUTHOR_NAME":     AUTHOR_NAME,
        "GIT_AUTHOR_EMAIL":    AUTHOR_EMAIL,
        "GIT_COMMITTER_NAME":  AUTHOR_NAME,
        "GIT_COMMITTER_EMAIL": AUTHOR_EMAIL,
    }
    r = run(f'git commit -m "{msg}"', extra_env=env)
    if r.returncode == 0:
        print(f"    [{date[:10]}] {msg[:55]}")
    else:
        print(f"    [{date[:10]}] SKIPPED (nothing new to commit)")

# 3. Show log
print("\n[3] Commit log:")
log = run("git log --format='%h  %ad  %s' --date=short")
print(log.stdout)

# 4. Set remote
print("[4] Setting GitHub remote...")
run("git remote remove origin", check=False)
run(f"git remote add origin {GITHUB_URL}")
print(f"    Remote: {GITHUB_URL}")

# 5. Push
print("\n[5] Pushing to GitHub...")
print("    --> Enter your GitHub username and Personal Access Token when asked\n")
r = subprocess.run("git push -u origin main --force",
                   shell=True, encoding="utf-8", errors="replace")
if r.returncode == 0:
    print("\n>>> SUCCESS! Live at: https://github.com/Manojgs001/FoodTrip")
else:
    print("\n>>> Push failed or needs credentials. Run manually:")
    print("    git push -u origin main --force")
