# knowledge_base.py v3
# Posit Cloud Implementation Assistant
# v3: adds get_sidebar_tasks() with Monday.com stub

from datetime import datetime, date

PROJECT_PLAN = """
## CUSTOMER: State University Research Computing (SURC)
## IMPLEMENTATION: Posit Cloud — Research Deployment
## CONTRACT START: May 3, 2026 | CONTRACT END: Sep 4, 2026
## PS LEAD: Meredith Callahan | ACCOUNT EXECUTIVE: Jordan Webb

---
### PHASE 1: ENVIRONMENT SETUP & PILOT (Weeks 1–4)
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Organization account provisioning (up to 200 seats) | PS Lead + IT Admin | May 13, 2026 | COMPLETE |
| SAML/SSO configuration with university IdP (Shibboleth) | IT Admin (Derek Huang) | May 20, 2026 | COMPLETE |
| Define researcher space structure (Dept spaces x4) | IT Admin + PS Lead | May 25, 2026 | COMPLETE |
| Set default resource limits per researcher role | IT Admin (Derek Huang) | Jun 3, 2026 | IN PROGRESS |
| Pilot group onboarding — 15 early adopters (Stats dept) | Derek Huang + Dr. Kim Osei | Jun 10, 2026 | NOT STARTED |
| Pilot UAT sign-off | Derek Huang | Jun 17, 2026 | NOT STARTED |

### PHASE 2: FULL RESEARCHER ROLLOUT (Weeks 5–8)
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Provision remaining researcher accounts (up to 185) | IT Admin | Jun 24, 2026 | NOT STARTED |
| Deliver researcher onboarding guide (final version) | Derek Huang + PS Lead | Jun 24, 2026 | NOT STARTED |
| Conduct live onboarding sessions (3 sessions by department) | Dr. Kim Osei + PS Lead | Jul 1, 2026 | NOT STARTED |
| Full-population go-live | Derek Huang | Jul 8, 2026 | NOT STARTED |

### PHASE 3: TRAINING & ADOPTION (Weeks 9–12)
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Admin training — ongoing space/user management | Derek Huang | Jul 22, 2026 | NOT STARTED |
| Researcher self-service documentation published in portal | Dr. Kim Osei | Jul 29, 2026 | NOT STARTED |
| 30-day adoption review with PS Lead | Derek Huang | Aug 13, 2026 | NOT STARTED |
| Implementation close-out & handoff to CS | PS Lead | Sep 4, 2026 | NOT STARTED |

---
### KEY CONTACTS
- Derek Huang — IT Admin / Technical Lead (primary day-to-day contact)
- Dr. Kim Osei — Research Computing Director / Executive Sponsor
- Meredith Callahan — Posit PS Lead
- Jordan Webb — Posit Account Executive (commercial questions only)
"""

SOW_SUMMARY = """
## STATEMENT OF WORK SUMMARY — State University Research Computing / Posit Cloud

### IN SCOPE
- Posit Cloud organization account provisioning (up to 200 named researcher accounts)
- Single Sign-On (SSO) configuration via SAML 2.0 with university Shibboleth IdP
- Space structure design: up to 6 departmental shared spaces
- Default compute resource limit configuration per user group (researcher, admin)
- Researcher onboarding documentation (1 guide, PS-assisted, SURC-owned)
- Up to 3 live onboarding sessions (virtual, PS-led)
- Admin training (1 session, covering ongoing user and space management)
- 30-day post-go-live adoption check-in

### OUT OF SCOPE
- Custom or private CRAN/Bioconductor package mirror setup
- HPC cluster integration or hybrid on-premises/cloud architecture
- Posit Workbench or Posit Connect deployment (separate products, not included)
- Data pipeline or ETL configuration
- Custom R environment pre-configuration per researcher
- Ongoing content or package support beyond the implementation period
- HIPAA-compliant infrastructure (Posit Cloud is not on HIPAA stack)
- Integration with university data warehouse or institutional databases

### FINAL ACCEPTANCE CRITERIA
1. Successful SSO login by >90% of provisioned accounts
2. All 4 departmental spaces active with appropriate member assignments
3. Researcher onboarding guide published
4. IT admin trained and able to manage users/spaces independently
"""

TASK_PROVISIONING = """
## TASK GUIDE: Provisioning Researcher Accounts in Posit Cloud
### Section: Account Setup | Phase 1

### Method A: Invite via Email (small batches)
1. Navigate to your organization account (click your icon > select SURC org name)
2. Click "Members" in the left sidebar
3. Click "Invite Members"
4. Enter email addresses (comma-separated, up to 20 at a time)
5. Assign role: set to "Contributor" for researchers
6. Click Send Invitations

### Method B: Space Invitations via SSO (recommended for bulk rollout)
With SSO configured, invite researchers to their departmental space —
invitations sent by Posit Cloud direct users to the dedicated SURC login page
(https://sso.posit.cloud/surc). Users who join a space are automatically added
to the organization account as Participants, and are removed from the account
automatically when they leave their last space.
- To let a researcher create projects, set their SPACE role to Contributor
- Manage researchers at the space level — account-level membership is handled
  for you (only admins and space creators need account-level management)

### Role Assignments for SURC
| User Type | Org Role | Space Role |
|-----------|----------|------------|
| IT Admin (Derek) | Owner | Admin |
| Dept Coordinator | Admin | Moderator |
| Researcher | Contributor | Contributor |
| Read-only observer | Participant | Viewer |

### Common Issues
- No invitation email: Check spam; re-send from Members list
- Cannot log in via SSO: Verify NetID is in the allowed Shibboleth attribute list
- User is "Participant" but needs to create projects: Promote to Contributor from Members list
"""

TASK_SSO_CONFIG = """
## TASK GUIDE: SAML/SSO Setup with University Shibboleth IdP
### Section: SSO Configuration | Phase 1 | Owner: Derek Huang | Due: May 20 (COMPLETE) | Attribute mapping documentation: Jun 1 (OVERDUE)

### How SSO Configuration Works for Posit Cloud
SSO setup is NOT self-service — there is no SSO settings page in the product.
Posit configures SAML SSO on their side through a manual process. Meredith
Callahan (PS Lead) coordinates the configuration request with Posit's team.
SURC's job is to gather the required information from the university IdP team
and provide it through PS.

### Step 1: Gather What Posit Needs (IT Admin + university IdP team)
Posit requests the following to configure the integration:
1. IdP software in use (SURC: Shibboleth)
2. IdP metadata XML — provided as an attachment or a URL Posit can fetch
3. Attribute names that will be released to Posit:
   - Stable and unique identifier (typically eduPersonTargetedId or eduPersonPrincipalName)
   - First name (typically givenName)
   - Last name (typically sn)
   - Email
4. The organization-name for the dedicated login URL, which takes the form
   https://sso.posit.cloud/[organization-name] (SURC chose: surc)
5. Optional: attribute-based access restriction — which attribute to inspect
   and the expected value (typically eduPersonEntitlement)

### Step 2: Submit Through PS
Provide the above to Meredith Callahan, who submits the configuration request
to Posit. Posit performs the configuration and confirms when the dedicated
login page is live.

### Step 3: Validate
1. Test login at https://sso.posit.cloud/surc with a single non-admin NetID
2. Confirm the account is created and the user lands in the correct space
3. If using attribute restriction, verify an out-of-scope NetID is denied access

### Key Constraints
- Posit's SP implementation requires SIGNED SAML responses — the IdP team may
  need to enable this in Shibboleth
- Invitations sent by Posit Cloud direct users to the dedicated login page
- SSO login does not by itself grant project-creation rights — admins set
  space roles (Contributor) as needed
- Misconfigured attribute restriction can lock users out — test before rollout

### SURC Status
SSO configured by Posit and live as of May 20. Internal documentation of the
attribute mapping (the identifier attribute and the eduPersonEntitlement
restriction value agreed with the IdP team) was due Jun 1 — currently OVERDUE.
Complete before pilot onboarding so login issues can be diagnosed quickly.
"""

TASK_RESOURCE_LIMITS = """
## TASK GUIDE: Setting Space and Compute Resource Limits by User Group
### Section: Resource Configuration | Phase 1 | Owner: Derek Huang | Due: Jun 3 (IN PROGRESS)

### Compute Hours Formula
(RAM in GB + CPUs) / 2 × hours active
Example: 2 GB RAM + 1 CPU × 1 hour = 1.5 compute hours

### Recommended Defaults for SURC
| User Type | RAM | CPU | Background Exec Limit |
|-----------|-----|-----|----------------------|
| Standard researcher | 2 GB | 1 | 1 hour |
| Bioinformatics researcher | 4–8 GB | 2 | 4 hours |
| Stats/Econ researcher | 2 GB | 1 | 1 hour |

### Setting Defaults via a Project Template
1. Create a project with your desired resource settings
2. Inside project > gear icon > Resources tab
3. Set RAM, CPU, Background Execution Limit > Apply Changes
4. Space > project menu > Save as Template

### Restricting Contributors from Changing Resources
1. Space > Members / Settings > Permissions
2. Disable "Can change resources for their content" for Contributor role

### Monitoring Usage
- Account-level: Org account > Account Overview > Usage tab
- Space-level: Space > Usage button in header
"""

TASK_ONBOARDING_GUIDE = """
## TASK GUIDE: Preparing and Delivering the Researcher Onboarding Guide
### Section: Onboarding Documentation | Phase 2 | Owner: Derek Huang + Dr. Kim Osei | Due: Jun 17

### Recommended Guide Structure
1. Introduction: What is Posit Cloud and why SURC is using it
2. First Login: https://sso.posit.cloud/surc
3. Navigating Your Space: Finding your departmental space
4. Creating a Project: Starting from the SURC template
5. Uploading Data: Max 500 MB per file, 20 GB per project
6. Installing Packages: renv or install.packages()
7. Saving Your Work: Auto-save, project persistence, export
8. Getting Help: Derek for IT issues, dept coordinator for access
9. Compute Limits: Compute hours explanation

### Key Facts
- Projects persist on disk even when not active
- Compute charged to SURC, not the researcher
- RAM is 2 GB / 1 CPU — researchers cannot change this
- GitHub credentials must be re-entered per project

### Delivery Plan
- Draft: no later than Jun 10
- Final: Jun 17
- Live sessions: Jun 17–24, facilitated by Dr. Kim Osei
"""

TASK_UAT = """
## TASK GUIDE: UAT Process for IT Admins Before Researcher Rollout
### Section: User Acceptance Testing | Phase 1 | Owner: Derek Huang | Due: Jun 10

### What to Test
1. SSO Login Flow — login via https://sso.posit.cloud/surc, Contributor role, correct space
2. Project Creation from Template — SURC template, 2 GB RAM / 1 CPU defaults
3. File Upload — test CSV, appears in Files pane
4. Basic R Execution — simple script, no crashes
5. Resource Lock — researcher cannot change RAM/CPU

### Sign-Off Criteria (all must pass)
- [ ] 100% of pilot users log in via SSO
- [ ] All create a project from SURC template
- [ ] File upload + R execution work in 90%+ of sessions
- [ ] No researcher can modify resource limits
- [ ] Derek can view all pilot projects from admin view

### Sign-Off Process
1. Complete checklist
2. Send confirmation to Meredith Callahan by June 10
3. If issues remain: PS Lead + Derek agree on go/no-go
"""

PRODUCT_KNOWLEDGE = """
## POSIT CLOUD PRODUCT KNOWLEDGE BASE
## Source: Posit official documentation (docs.posit.co/cloud)

### WHAT IS POSIT CLOUD?
Cloud-hosted RStudio IDE and Jupyter notebooks in a browser. Each user works in
isolated containerized projects. Hosted on AWS by Posit (formerly RStudio, Inc.).

Not the same as:
- Posit Workbench: self-hosted server software
- Posit Connect: publishing platform for Shiny apps
- Posit Package Manager: internal CRAN mirror tool

### ACCOUNT ROLES
Organization: Owner > Admin > Moderator > Contributor > Participant
Space: Admin > Moderator > Contributor > Viewer

### PROJECTS
- Default: 1 GB RAM, 1 CPU
- Max: 8 GB RAM (Standard plan); 16 GB (Premium/Instructor)
- Disk: 20 GB per project
- Max file upload: 500 MB
- Idle suspension: 15 minutes
- Max runtime: 24 hours

Compute formula: (RAM GB + CPUs) / 2 × hours active

### SSO
SAML 2.0, available for organization accounts on Standard or Instructor plans.
- Configuration is a manual process handled by Posit — coordinated through
  your Posit contact. There is no self-service SSO settings page.
- Dedicated login URL: https://sso.posit.cloud/[organization-name]
- Posit's SP implementation requires SIGNED SAML responses from the IdP
- Attributes requested: stable unique identifier (typically eduPersonTargetedId
  or eduPersonPrincipalName), givenName, sn, email
- Optional access restriction by attribute (typically eduPersonEntitlement)
- Invitations sent by Cloud direct users to the dedicated login page
- Users who join spaces are added to the org account as Participants
  automatically; admins set space roles (e.g., Contributor) as needed

### SECURITY
- SSL encrypted; data encrypted at rest
- AWS hosted — NOT HIPAA-compliant
- GitHub credentials do not persist across projects

### KNOWN LIMITATIONS FOR SURC
- Not HIPAA-compliant
- No custom package mirrors
- No HPC or on-premises integration
- Max job runtime: 24 hours

### ADMIN QUICK REFERENCE
| Task | Where |
|------|-------|
| Invite to org | Org account > Members > Invite Members |
| Change member role | Org account > Members > role dropdown |
| Create space | Sidebar > New Space |
| Invite to space | Space > Members > Invite |
| Set permissions | Space > Settings > Permissions |
| View usage | Org account > Usage tab |
| Configure SSO | Manual process via Posit — coordinate through PS Lead |
| Set project resources | Inside project > gear icon > Resources tab |
| Create template | Space > project menu > Save as Template |
"""

# ---------------------------------------------------------------------------
# Topic tags
# ---------------------------------------------------------------------------
TOPIC_TAGS = [
    "SSO", "Provisioning", "Resource Limits", "UAT", "Onboarding",
    "Scope Question", "Project Status", "Product Question", "Escalation",
    "Access / Roles", "Compute / Usage", "Security", "General"
]

# ---------------------------------------------------------------------------
# Per-role knowledge scoping
# ---------------------------------------------------------------------------
ROLE_KNOWLEDGE_MAP = {
    "IT Admin / Technical Lead": [
        "PROJECT_PLAN", "SOW_SUMMARY", "TASK_PROVISIONING",
        "TASK_SSO_CONFIG", "TASK_RESOURCE_LIMITS", "TASK_UAT",
        "PRODUCT_KNOWLEDGE"
    ],
    "Project Lead / Project Manager": [
        "PROJECT_PLAN", "SOW_SUMMARY", "TASK_PROVISIONING",
        "TASK_ONBOARDING_GUIDE", "TASK_UAT", "PRODUCT_KNOWLEDGE"
    ],
    "Executive Sponsor / Research Director": [
        "PROJECT_PLAN", "SOW_SUMMARY", "PRODUCT_KNOWLEDGE"
    ],
    "Researcher / End User": [
        "TASK_ONBOARDING_GUIDE", "PRODUCT_KNOWLEDGE"
    ],
    "UAT Tester": [
        "TASK_UAT", "TASK_PROVISIONING", "PRODUCT_KNOWLEDGE", "PROJECT_PLAN"
    ],
}

KNOWLEDGE_SECTIONS = {
    "PROJECT_PLAN":          ("=== PROJECT PLAN ===", PROJECT_PLAN),
    "SOW_SUMMARY":           ("=== STATEMENT OF WORK SUMMARY ===", SOW_SUMMARY),
    "TASK_PROVISIONING":     ("=== TASK GUIDE: ACCOUNT PROVISIONING — Section: Account Setup | Phase 1 ===", TASK_PROVISIONING),
    "TASK_SSO_CONFIG":       ("=== TASK GUIDE: SSO CONFIGURATION — Section: SSO Configuration | Phase 1 ===", TASK_SSO_CONFIG),
    "TASK_RESOURCE_LIMITS":  ("=== TASK GUIDE: RESOURCE LIMITS — Section: Resource Configuration | Phase 1 ===", TASK_RESOURCE_LIMITS),
    "TASK_ONBOARDING_GUIDE": ("=== TASK GUIDE: RESEARCHER ONBOARDING GUIDE — Section: Onboarding Documentation | Phase 2 ===", TASK_ONBOARDING_GUIDE),
    "TASK_UAT":              ("=== TASK GUIDE: UAT PROCESS — Section: User Acceptance Testing | Phase 1 ===", TASK_UAT),
    "PRODUCT_KNOWLEDGE":     ("=== POSIT CLOUD PRODUCT KNOWLEDGE BASE ===", PRODUCT_KNOWLEDGE),
}


def get_context_for_role(role: str) -> str:
    keys = ROLE_KNOWLEDGE_MAP.get(role, list(KNOWLEDGE_SECTIONS.keys()))
    return "\n\n".join(
        f"{header}\n{content}"
        for key in keys
        for header, content in [KNOWLEDGE_SECTIONS[key]]
    )


def get_full_context() -> str:
    return "\n\n".join(
        f"{header}\n{content}"
        for header, content in KNOWLEDGE_SECTIONS.values()
    )


# ---------------------------------------------------------------------------
# Sidebar task data
# ---------------------------------------------------------------------------
# Hardcoded task list — replace get_sidebar_tasks() body with Monday API
# call when the board is stood up. The return format must stay identical:
# a dict with keys "overdue" and "upcoming", each a list of
# {"name": str, "due": str} dicts.
#
# TODO (Monday.com integration):
#   import monday_client
#   tasks = monday_client.get_tasks(board_id=MONDAY_BOARD_ID)
#   return monday_client.format_for_sidebar(tasks, today=today)

_HARDCODED_TASKS = [
    {"name": "Document SSO attribute mapping",     "due": date(2026, 6, 1),  "status": "OVERDUE"},
    {"name": "Set default resource limits",         "due": date(2026, 6, 3),  "status": "IN PROGRESS"},
    {"name": "Create 4 departmental spaces",        "due": date(2026, 6, 3),  "status": "IN PROGRESS"},
    {"name": "Identify 15 pilot researchers",       "due": date(2026, 6, 7),  "status": "NOT STARTED"},
    {"name": "Pilot group onboarding",              "due": date(2026, 6, 10), "status": "NOT STARTED"},
    {"name": "Pilot UAT sign-off",                  "due": date(2026, 6, 17), "status": "NOT STARTED"},
    {"name": "Provision remaining accounts (185)",  "due": date(2026, 6, 24), "status": "NOT STARTED"},
    {"name": "Deliver researcher onboarding guide", "due": date(2026, 6, 24), "status": "NOT STARTED"},
]


def get_date_context(today: date = None) -> str:
    """
    Build a date-aware project status block for the system prompt.
    Computed from _HARDCODED_TASKS at session time so the prompt, the
    sidebar, and reality never drift apart. No hardcoded 'due today'
    language anywhere else — this is the single source of truth.
    """
    if today is None:
        today = date.today()

    overdue, due_today, upcoming = [], [], []
    for t in _HARDCODED_TASKS:
        if t["status"] == "COMPLETE":
            continue
        d = t["due"]
        line = f"- {t['name']} (due {d.strftime('%b %-d')}, status: {t['status']})"
        if d < today:
            overdue.append(line)
        elif d == today:
            due_today.append(line)
        elif (d - today).days <= 14:
            upcoming.append(line)

    parts = [f"TODAY'S DATE: {today.strftime('%B %-d, %Y')}", ""]
    parts.append("OVERDUE TASKS:" if overdue else "OVERDUE TASKS: None")
    parts.extend(overdue)
    if due_today:
        parts.append("DUE TODAY:")
        parts.extend(due_today)
    parts.append("UPCOMING (next 14 days):" if upcoming else "UPCOMING (next 14 days): None")
    parts.extend(upcoming)
    return "\n".join(parts)


def get_sidebar_tasks(today: date = None) -> dict:
    """
    Return overdue and upcoming (within 14 days) tasks for the sidebar.

    Returns:
        {
            "overdue":  [{"name": str, "due": str}, ...],
            "upcoming": [{"name": str, "due": str}, ...],
        }

    TODO: Replace body with Monday.com API call when board is ready.
          Keep return format identical so sidebar rendering requires no changes.
    """
    if today is None:
        today = date.today()

    overdue  = []
    upcoming = []

    for task in _HARDCODED_TASKS:
        if task["status"] == "COMPLETE":
            continue
        due_date = task["due"]
        due_str  = due_date.strftime("%b %-d")

        if due_date < today:
            overdue.append({"name": task["name"], "due": due_str})
        elif (due_date - today).days <= 14:
            upcoming.append({"name": task["name"], "due": due_str})

    # Sort both lists by due date
    overdue.sort(key=lambda t: t["due"])
    upcoming.sort(key=lambda t: t["due"])

    return {"overdue": overdue, "upcoming": upcoming}
