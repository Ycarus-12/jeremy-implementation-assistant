# knowledge_base.py
# All mock context injected into API calls.
# Grounded in real Posit Cloud documentation (docs.posit.co/cloud).
# v2: Per-role scoping — each role receives only relevant knowledge slices.

PROJECT_PLAN = """
## CUSTOMER: State University Research Computing (SURC)
## IMPLEMENTATION: Posit Cloud — Research Deployment
## CONTRACT START: March 3, 2026 | CONTRACT END: June 27, 2026
## PS LEAD: Meredith Callahan | ACCOUNT EXECUTIVE: Jordan Webb

---
### PHASE 1: ENVIRONMENT SETUP & PILOT (Weeks 1–4)
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Organization account provisioning (up to 200 seats) | PS Lead + IT Admin | Mar 13, 2026 | COMPLETE |
| SAML/SSO configuration with university IdP (Shibboleth) | IT Admin (Derek Huang) | Mar 20, 2026 | COMPLETE |
| Define researcher space structure (Dept spaces x4) | IT Admin + PS Lead | Mar 25, 2026 | COMPLETE |
| Set default resource limits per researcher role | IT Admin (Derek Huang) | Mar 27, 2026 | IN PROGRESS |
| Pilot group onboarding — 15 early adopters (Stats dept) | Derek Huang + Dr. Kim Osei | Apr 3, 2026 | NOT STARTED |
| Pilot UAT sign-off | Derek Huang | Apr 10, 2026 | NOT STARTED |

### PHASE 2: FULL RESEARCHER ROLLOUT (Weeks 5–8)
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Provision remaining researcher accounts (up to 185) | IT Admin | Apr 17, 2026 | NOT STARTED |
| Deliver researcher onboarding guide (final version) | Derek Huang + PS Lead | Apr 17, 2026 | NOT STARTED |
| Conduct live onboarding sessions (3 sessions by department) | Dr. Kim Osei + PS Lead | Apr 24, 2026 | NOT STARTED |
| Full-population go-live | Derek Huang | May 1, 2026 | NOT STARTED |

### PHASE 3: TRAINING & ADOPTION (Weeks 9–12)
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Admin training — ongoing space/user management | Derek Huang | May 15, 2026 | NOT STARTED |
| Researcher self-service documentation published in portal | Dr. Kim Osei | May 22, 2026 | NOT STARTED |
| 30-day adoption review with PS Lead | Derek Huang | Jun 6, 2026 | NOT STARTED |
| Implementation close-out & handoff to CS | PS Lead | Jun 27, 2026 | NOT STARTED |

---
### KEY CONTACTS
- Derek Huang — IT Admin / Technical Lead (primary day-to-day contact)
- Dr. Kim Osei — Research Computing Director / Executive Sponsor
- Meredith Callahan — Posit PS Lead
- Jordan Webb — Posit Account Executive (commercial questions only)

### ACTIVE TASKS THIS WEEK (as of session context)
1. Set default resource limits per researcher role (Derek Huang, due Mar 27 — IN PROGRESS)
2. Prepare onboarding guide draft (Derek Huang, due Apr 17 — early start recommended)
3. Identify 15 pilot researchers in Statistics department (Dr. Kim Osei, due Mar 31)
4. Document SSO attribute mapping for eduPersonEntitlement (Derek Huang, due Mar 25 — OVERDUE)
5. Create 4 departmental spaces: Statistics, Bioinformatics, Economics, Public Health (Derek Huang, due Mar 27)
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

### Overview
Posit Cloud uses an organization account model. The IT Admin invites users to the
organization account and to individual shared spaces. With SSO enabled, first-time
login automatically creates and links the user account.

### Method A: Invite via Email (small batches)
1. Navigate to your organization account (click your icon > select SURC org name)
2. Click "Members" in the left sidebar
3. Click "Invite Members"
4. Enter email addresses (comma-separated, up to 20 at a time)
5. Assign role: set to "Contributor" for researchers
6. Click Send Invitations
7. Users receive an email and are prompted to log in via SSO

### Method B: SSO Auto-Provisioning (recommended for bulk rollout)
With Shibboleth SSO configured, users are automatically added to the organization
account as "Participants" when they first access a shared space URL.
- Participants cannot create their own spaces; they only access invited spaces
- To grant Contributor access, promote them from the Members list
- Recommended: send researchers the direct space URL so auto-provisioning triggers on first login

### Role Assignments for SURC
| User Type | Org Role | Space Role |
|-----------|----------|------------|
| IT Admin (Derek) | Owner | Admin |
| Dept Coordinator | Admin | Moderator |
| Researcher | Contributor | Contributor |
| Read-only observer | Participant | Viewer |

### Bulk Verification
After provisioning:
1. Go to org account > Members tab
2. Filter by "Pending" to see who has not yet accepted/logged in
3. Follow up with pending users before pilot UAT (Apr 10)

### Common Issues
- No invitation email received: Check spam; re-send from Members list
- Cannot log in via SSO: Verify NetID is in the allowed attribute list in Shibboleth config
- User appears as "Participant" but needs to create projects: Promote to Contributor from Members list
"""

TASK_SSO_CONFIG = """
## TASK GUIDE: Configuring SAML/SSO with University Shibboleth IdP
### Section: SSO Configuration | Phase 1 | Owner: Derek Huang | Due: Mar 20 (COMPLETE) | Attribute mapping due: Mar 25 (OVERDUE)

### Overview
Posit Cloud supports SAML 2.0 SSO on Standard and above organization plans.
SURC uses Shibboleth as its Identity Provider (IdP).

### Step 1: Gather SP Values from Posit Cloud
1. Navigate to org account > Account Settings > Security / SSO
2. Note the Service Provider values Posit Cloud provides:
   - Entity ID (SP Metadata URL)
   - ACS URL: format is https://sso.posit.cloud/[org-slug]
   - Choose your org login URL slug (e.g., "surc" → https://sso.posit.cloud/surc)

### Step 2: Configure Your Shibboleth IdP
Provide your university IdP team with:
- Posit Cloud SP Entity ID and ACS URL
- Request: signed SAML responses (Posit Cloud requires signed responses)
- Attribute to release: eduPersonEntitlement (for access restriction)
  or eduPersonPrincipalName (for user identification)

### Step 3: Configure SSO in Posit Cloud
1. In Account Settings > Security, enter:
   - IdP Metadata URL from Shibboleth OR upload IdP metadata XML
   - Org login URL slug
   - Optional: attribute-based access restriction
2. Save and test with a single non-admin test account before broad rollout

### Step 4: Communicate Login URL to Researchers
- All researcher access: https://sso.posit.cloud/surc (or your chosen slug)
- Include this URL in all invitations and onboarding documentation

### Key Constraints
- Posit Cloud requires SIGNED SAML responses — configure this in the IdP
- SSO does not replace space invitations; users still need to be added to spaces
- Misconfigured attribute restriction can lock users out — test before rollout

### SURC Status Note
SSO configuration completed March 20. The eduPersonEntitlement attribute mapping
was due Mar 25 and is currently OVERDUE. Derek should confirm with the IdP team
that this attribute is correctly released before pilot onboarding begins Apr 3.
"""

TASK_RESOURCE_LIMITS = """
## TASK GUIDE: Setting Space and Compute Resource Limits by User Group
### Section: Resource Configuration | Phase 1 | Owner: Derek Huang | Due: Mar 27 (IN PROGRESS)

### Compute Hours Formula
(RAM in GB + CPUs) / 2 × hours active
Example: 2 GB RAM + 1 CPU active for 1 hour = 1.5 compute hours
Sessions idle for 15+ minutes are suspended and do not accrue compute hours.

### Recommended Resource Defaults for SURC
| User Type | RAM | CPU | Background Exec Limit |
|-----------|-----|-----|----------------------|
| Standard researcher | 2 GB | 1 | 1 hour |
| Bioinformatics researcher | 4–8 GB | 2 | 4 hours |
| Stats/Econ researcher | 2 GB | 1 | 1 hour |
| Admin/IT | 2 GB | 1 | 1 hour |

Note: Max RAM is 8 GB per project on Standard plan; 16 GB on Premium/Instructor plans.

### Setting Defaults via a Project Template
1. Create a project in the target space with your desired resource settings
2. Open the project, click the gear icon (Settings) in the header
3. Go to Resources tab; set RAM, CPU, and Background Execution Limit
4. Click Apply Changes
5. Return to the space, open the project menu, save as Template
6. Instruct researchers to always start from this template

### Restricting Contributors from Changing Resources
1. Go to your space > Members (or Space Settings)
2. In Permissions, locate "Can change resources for their content"
3. Disable for the Contributor role to enforce default limits

### Monitoring Usage
- Account-level: Org account > Account Overview > Usage tab
- Space-level: Navigate to space > Usage button in header

### SURC Immediate Action (due Mar 27 — today, IN PROGRESS)
1. Create one project template per departmental space with appropriate resource defaults
2. Disable "Can change resources" for Contributor role in all 4 spaces
3. Document the template name in the researcher onboarding guide
"""

TASK_ONBOARDING_GUIDE = """
## TASK GUIDE: Preparing and Delivering the Researcher Onboarding Guide
### Section: Onboarding Documentation | Phase 2 | Owner: Derek Huang + Dr. Kim Osei | Due: Apr 17

### Recommended Guide Structure
1. Introduction: What is Posit Cloud and why SURC is using it
2. First Login: Access via SSO at https://sso.posit.cloud/surc
3. Navigating Your Space: Finding your departmental space
4. Creating a Project: Starting from the SURC template
5. Uploading Data: File upload (max 500 MB per file, 20 GB per project on disk)
6. Installing Packages: How renv or manual install.packages() works
7. Saving Your Work: Auto-save behavior, project persistence, exporting files
8. Getting Help: Who to contact
9. Compute Limits: Brief explanation of compute hours

### Key Facts to Include
- Projects persist on disk even when not active (session suspends after 15 min idle)
- Compute hours are charged to SURC, not the researcher personally
- Maximum file upload size: 500 MB; maximum project disk: 20 GB
- Default RAM is 2 GB and 1 CPU (researchers cannot change this)
- GitHub integration available but credentials must be re-entered per project

### Delivery Plan
- Draft due: Early April (start no later than Apr 3)
- Final version due: Apr 17 alongside full researcher provisioning
- Live sessions: 3 onboarding sessions Apr 17–24, facilitated by Dr. Kim Osei
"""

TASK_UAT = """
## TASK GUIDE: UAT Process for IT Admins Before Researcher Rollout
### Section: User Acceptance Testing | Phase 1 | Owner: Derek Huang | Due: Apr 10

### What to Test

**1. SSO Login Flow**
- Each pilot researcher logs in via https://sso.posit.cloud/surc
- Correct role assigned (Contributor, not just Participant)
- Users land in the Statistics departmental space after login

**2. Project Creation from Template**
- Researcher creates a new project using the SURC Statistics template
- Project opens with correct defaults (2 GB RAM, 1 CPU)

**3. File Upload**
- Researcher uploads a test dataset (<10 MB CSV)
- File appears in the Files pane

**4. Basic R Execution**
- Researcher runs a simple R script without errors or crashes

**5. Resource Lock Verification**
- Researcher cannot change RAM/CPU settings
- Settings gear > Resources tab shows values but is not editable

### UAT Sign-Off Criteria (all must pass)
- [ ] 100% of pilot users can log in via SSO
- [ ] All pilot users can create a project from the SURC template
- [ ] File upload and basic R execution work in 90%+ of sessions
- [ ] No researcher can modify their own resource limits
- [ ] Derek Huang can view all pilot projects from space admin view

### Sign-Off Process
1. Derek Huang completes the UAT checklist
2. Sends sign-off confirmation to Meredith Callahan by April 10
3. If issues remain open: PS Lead and Derek agree on go/no-go for Phase 2
"""

PRODUCT_KNOWLEDGE = """
## POSIT CLOUD PRODUCT KNOWLEDGE BASE
## Source: Posit official documentation (docs.posit.co/cloud)

### WHAT IS POSIT CLOUD?
Posit Cloud is a cloud-hosted data science platform running RStudio IDE and Jupyter
notebooks in a web browser. Users work in isolated containerized projects without
installing anything locally. Hosted on AWS.

Distinct from:
- Posit Workbench: server software you deploy on your own infrastructure
- Posit Connect: publishing platform for Shiny apps and reports
- Posit Package Manager: internal CRAN mirror management tool

### ACCOUNT TYPES AND ROLES

Organization Account Roles:
- Owner: full control (plan, billing, members, spaces, content, usage)
- Admin: manage members, spaces, content, view usage (cannot manage billing)
- Moderator: manage spaces and content, view usage
- Contributor: create and manage their own spaces within the org
- Participant: auto-assigned when joining a space; no org-level capabilities

Space Roles:
- Admin: full space management
- Moderator: manage content and view usage
- Contributor: create and manage their own projects
- Viewer: read-only access

### SPACES
- Each space has its own member list, content, and usage tracking
- All compute in a space is billed to the organization account that owns it
- Spaces can be archived (content preserved) or deleted (content gone permanently)

Configurable space permissions:
- "Can see the members list"
- "Can change access to their content"
- "Can change resources for their content"

### PROJECTS
- Default allocation: 1 GB RAM, 1 CPU
- Maximum allocation: up to 16 GB RAM (Premium/Instructor); 8 GB (Standard)
- Disk per project: 20 GB maximum
- Max file upload size: 500 MB per file
- Idle suspension: after 15 minutes of inactivity, sessions suspend
- Maximum consecutive runtime: 24 hours hard limit

Compute hours formula: (RAM in GB + CPUs) / 2 × hours active

### SINGLE SIGN-ON (SSO)
Available on Standard and above plans. Protocol: SAML 2.0.
- Each org gets a dedicated login URL: https://sso.posit.cloud/[org-slug]
- Posit Cloud requires SIGNED SAML responses from the IdP
- First SSO login auto-creates the user account as Participant
- Admins must upgrade Participants to Contributors to allow project creation

### SECURITY & INFRASTRUCTURE
- All traffic encrypted via SSL; all data encrypted at rest
- Projects isolated in individual containers
- Hosted on AWS (NOT HIPAA-compliant infrastructure)
- GitHub credentials NOT persisted across projects

### KNOWN LIMITATIONS RELEVANT TO SURC
- Not HIPAA-compliant
- No custom package mirrors
- No HPC or hybrid on-premises integration
- Background execution limit: jobs longer than 24 hours not supported

### ADMIN QUICK REFERENCE
| Task | Where in UI |
|------|-------------|
| Invite members to org | Org account > Members > Invite Members |
| Change member role | Org account > Members > role dropdown |
| Create a space | Navigation sidebar > New Space |
| Invite members to space | Space > Members > Invite |
| Set space permissions | Space > Settings > Permissions |
| View compute usage | Org account > Usage tab |
| Configure SSO | Org account > Account Settings > Security |
| Set project resources | Inside project > gear icon > Resources tab |
| Create project template | Space > project menu > Save as Template |
"""

# ---------------------------------------------------------------------------
# Topic tags for PS Summary auto-categorization
# ---------------------------------------------------------------------------
TOPIC_TAGS = [
    "SSO", "Provisioning", "Resource Limits", "UAT", "Onboarding",
    "Scope Question", "Project Status", "Product Question", "Escalation",
    "Access / Roles", "Compute / Usage", "Security", "General"
]

# ---------------------------------------------------------------------------
# Per-role knowledge base scoping
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
    "PROJECT_PLAN": ("=== PROJECT PLAN ===", PROJECT_PLAN),
    "SOW_SUMMARY": ("=== STATEMENT OF WORK SUMMARY ===", SOW_SUMMARY),
    "TASK_PROVISIONING": ("=== TASK GUIDE: ACCOUNT PROVISIONING — Section: Account Setup | Phase 1 ===", TASK_PROVISIONING),
    "TASK_SSO_CONFIG": ("=== TASK GUIDE: SSO CONFIGURATION — Section: SSO Configuration | Phase 1 ===", TASK_SSO_CONFIG),
    "TASK_RESOURCE_LIMITS": ("=== TASK GUIDE: RESOURCE LIMITS — Section: Resource Configuration | Phase 1 ===", TASK_RESOURCE_LIMITS),
    "TASK_ONBOARDING_GUIDE": ("=== TASK GUIDE: RESEARCHER ONBOARDING GUIDE — Section: Onboarding Documentation | Phase 2 ===", TASK_ONBOARDING_GUIDE),
    "TASK_UAT": ("=== TASK GUIDE: UAT PROCESS — Section: User Acceptance Testing | Phase 1 ===", TASK_UAT),
    "PRODUCT_KNOWLEDGE": ("=== POSIT CLOUD PRODUCT KNOWLEDGE BASE ===", PRODUCT_KNOWLEDGE),
}


def get_context_for_role(role: str) -> str:
    """Return only the knowledge base sections relevant to the given role."""
    keys = ROLE_KNOWLEDGE_MAP.get(role, list(KNOWLEDGE_SECTIONS.keys()))
    parts = []
    for key in keys:
        header, content = KNOWLEDGE_SECTIONS[key]
        parts.append(f"{header}\n{content}")
    return "\n\n".join(parts)


def get_full_context() -> str:
    """Return the complete knowledge base (used when role is unknown)."""
    parts = []
    for header, content in KNOWLEDGE_SECTIONS.values():
        parts.append(f"{header}\n{content}")
    return "\n\n".join(parts)
