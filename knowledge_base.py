# knowledge_base.py
# All mock context injected into every API call.
# Grounded in real Posit Cloud documentation (docs.posit.co/cloud).

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
1. Set default resource limits per researcher role (Derek Huang, due Mar 27)
2. Prepare onboarding guide draft (Derek Huang, due Apr 17 — early start recommended)
3. Identify 15 pilot researchers in Statistics department (Dr. Kim Osei, due Mar 31)
4. Document SSO attribute mapping for eduPersonEntitlement (Derek Huang, due Mar 25 — slightly overdue)
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
- Cannot log in via SSO: Verify NetID is in the allowed attribute list in Shibboleth IdP config
- User appears as "Participant" but needs to create projects: Promote to Contributor from Members list
"""

TASK_SSO_CONFIG = """
## TASK GUIDE: Configuring SAML/SSO with University Shibboleth IdP

### Overview
Posit Cloud supports SAML 2.0 SSO on Standard and above organization plans.
SURC uses Shibboleth as its Identity Provider (IdP).
SSO must be configured before pilot user onboarding (due Apr 3).

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
   - Optional: attribute-based access restriction (specify attribute name and expected value)
2. Save and test with a single non-admin test account before broad rollout

### Step 4: Communicate Login URL to Researchers
- All researcher access: https://sso.posit.cloud/surc (or your chosen slug)
- Include this URL in all invitations and onboarding documentation
- SSO URL ensures auth flows through Shibboleth

### Key Constraints
- SSO available on Standard plan and above (confirmed in SURC SOW)
- Posit Cloud requires signed SAML responses — configure this in the IdP
- SSO does not replace space invitations; users still need to be added to spaces
- Misconfigured attribute restriction can lock users out — test before rollout

### SURC Status Note
SSO configuration was completed March 20. The eduPersonEntitlement attribute mapping
was due Mar 25 and is slightly overdue. Derek should confirm with the IdP team that
this attribute is correctly released before pilot onboarding begins Apr 3.
"""

TASK_RESOURCE_LIMITS = """
## TASK GUIDE: Setting Space and Compute Resource Limits by User Group

### Overview
Posit Cloud controls compute via:
1. Project-level resource settings (RAM, CPU, background execution limit) — set per project
2. Space-level permissions — control whether Contributors can change their own resource settings

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
4. Note: Admins and Moderators can always change resource settings

### Monitoring Usage
- Account-level: Org account > Account Overview > Usage tab
- Space-level: Navigate to space > Usage button in header
- No automated per-space alerts; email alerts fire at 80% of monthly compute limit

### SURC Immediate Action (due Mar 27 — today)
1. Create one project template per departmental space with appropriate resource defaults
2. Disable "Can change resources" for Contributor role in all 4 spaces
3. Document the template name in the researcher onboarding guide
"""

TASK_ONBOARDING_GUIDE = """
## TASK GUIDE: Preparing and Delivering the Researcher Onboarding Guide

### Overview
The researcher onboarding guide is SURC-owned documentation. PS assists with structure;
Derek Huang and Dr. Kim Osei own final content and publication. Due Apr 17.

### Recommended Guide Structure
1. Introduction: What is Posit Cloud and why SURC is using it
2. First Login: Access via SSO at https://sso.posit.cloud/surc
3. Navigating Your Space: Finding your departmental space, understanding the interface
4. Creating a Project: Starting from the SURC template (step-by-step with screenshots)
5. Uploading Data: File upload (max 500 MB per file, 20 GB per project on disk)
6. Installing Packages: How renv or manual install.packages() works in the cloud context
7. Saving Your Work: Auto-save behavior, project persistence, exporting files
8. Getting Help: Who to contact (Derek for IT issues, dept coordinator for access)
9. Compute Limits: Brief explanation of compute hours and why they matter

### Key Facts to Include
- Each researcher works in their own projects within the departmental space
- Projects persist on disk even when not active (session suspends after 15 min idle)
- Compute hours are charged to SURC, not the researcher personally
- Maximum file upload size: 500 MB; maximum project disk: 20 GB
- Default RAM is 2 GB and 1 CPU (researchers cannot change this — controls are locked)
- Researchers must not share login credentials; each person uses their own NetID
- GitHub integration available but credentials must be re-entered per project

### Delivery Plan
- Draft due: Early April (start no later than Apr 3)
- Final version due: Apr 17 alongside full researcher provisioning
- Publication: SURC internal IT portal, linked from space descriptions
- Live sessions: 3 onboarding sessions Apr 17–24, facilitated by Dr. Kim Osei
"""

TASK_UAT = """
## TASK GUIDE: UAT Process for IT Admins Before Researcher Rollout

### Overview
UAT runs Apr 3–10 with 15 Statistics department researchers as pilot users.
Derek Huang leads UAT. Sign-off required before Phase 2 full rollout.

### What to Test

**1. SSO Login Flow**
- Each pilot researcher logs in via https://sso.posit.cloud/surc
- Correct role assigned (Contributor, not just Participant)
- Users land in the Statistics departmental space after login

**2. Project Creation from Template**
- Researcher creates a new project using the SURC Statistics template
- Project opens with correct defaults (2 GB RAM, 1 CPU)
- R and relevant packages available as expected

**3. File Upload**
- Researcher uploads a test dataset (recommend a <10 MB CSV)
- File appears in the Files pane within the project

**4. Basic R Execution**
- Researcher runs a simple R script (load data, summarize, produce output)
- No memory errors or unexpected session crashes

**5. Resource Lock Verification**
- Researcher cannot change RAM/CPU settings (permissions locked)
- Settings gear > Resources tab shows values but is not editable

### UAT Sign-Off Criteria
All must pass:
- [ ] 100% of pilot users can log in via SSO
- [ ] All pilot users can create a project from the SURC template
- [ ] File upload and basic R execution work in 90%+ of sessions
- [ ] No researcher can modify their own resource limits
- [ ] Derek Huang can view all pilot projects from space admin view

### Escalation to PS Lead
Escalate to Meredith Callahan for:
- SSO failures affecting more than 2 users
- Platform errors that appear to be Posit Cloud bugs (not config issues)
- Any behavior contradicting what is documented in the onboarding guide

### Sign-Off Process
1. Derek Huang completes the UAT checklist
2. Documents any open issues and resolution status
3. Sends sign-off confirmation to Meredith Callahan by April 10
4. If issues remain open: PS Lead and Derek agree on go/no-go for Phase 2
"""

PRODUCT_KNOWLEDGE = """
## POSIT CLOUD PRODUCT KNOWLEDGE BASE
## Source: Posit official documentation (docs.posit.co/cloud)

---
### WHAT IS POSIT CLOUD?
Posit Cloud is a cloud-hosted data science platform running RStudio IDE and Jupyter
notebooks in a web browser. Users work in isolated containerized projects without
installing anything locally. Hosted by Posit (formerly RStudio, Inc.) on AWS.

Distinct from:
- Posit Workbench: server software you deploy on your own infrastructure
- Posit Connect: publishing platform for Shiny apps and reports
- Posit Package Manager: internal CRAN mirror management tool

---
### ACCOUNT TYPES AND ROLES

**Account Types:**
- Personal account: individual workspace, no sharing by default
- Organization account: shared environment for teams; required for SSO, multi-space management

**Organization Account Roles:**
- Owner: full control (plan, billing, members, spaces, content, usage)
- Admin: manage members, spaces, content, view usage (cannot manage billing)
- Moderator: manage spaces and content, view usage
- Contributor: create and manage their own spaces within the org
- Participant: auto-assigned when joining a space; no org-level capabilities

**Space Roles (within a shared space):**
- Admin: full space management
- Moderator: manage content and view usage; cannot manage members
- Contributor: create and manage their own projects
- Viewer: read-only access

---
### SPACES
A space is a shared collaborative environment within an organization account.
- Each space has its own member list, content, and usage tracking
- All compute in a space is billed to the organization account that owns it
- Spaces can be organized with project lists (like folders)
- Admins and Moderators can create/delete lists and manage all content
- Spaces can be archived (content preserved) or deleted (content gone permanently)

**Configurable space permissions:**
- "Can see the members list" — show/hide member roster for Contributors/Viewers
- "Can change access to their content" — allow Contributors to share projects
- "Can change resources for their content" — allow Contributors to adjust RAM/CPU

---
### PROJECTS
Each project is a containerized R or Python development environment.
- Default allocation: 1 GB RAM, 1 CPU
- Maximum allocation: up to 16 GB RAM (Premium/Instructor); 8 GB (Standard)
- Disk per project: 20 GB maximum
- Max file upload size: 500 MB per file
- Idle suspension: after 15 minutes of inactivity, sessions suspend
- Background execution limit: minimum 1 hour; maximum depends on plan
- Maximum consecutive runtime: 24 hours hard limit

**Compute hours formula:**
(RAM in GB + CPUs) / 2 × hours active
Example: 2 GB RAM + 1 CPU × 1 hour = 1.5 compute hours
Idle sessions do not accrue compute hours.

**Project settings (gear icon in project header):**
- Resources: RAM, CPU, Background Execution Limit
- System: OS version
- Packages: R/Python version and package options

**Project templates:**
- Any project can be saved as a template within a space
- New projects from a template inherit files, packages, and resource settings

---
### SINGLE SIGN-ON (SSO)
Available on Standard and above organization plans. Protocol: SAML 2.0.

**Key concepts:**
- Posit Cloud = SAML Service Provider (SP)
- University IdP (Shibboleth) = Identity Provider
- Each org gets a dedicated login URL: https://sso.posit.cloud/[org-slug]
- Posit Cloud requires SIGNED SAML responses from the IdP
- Optional attribute-based access restriction (e.g., by eduPersonEntitlement value)

**SSO user behavior:**
- First SSO login auto-creates the user account
- User added to org as Participant on first space access
- Admins must upgrade Participants to Contributors to allow project creation

**Common university SSO attributes:**
- eduPersonPrincipalName (eppn): unique user identifier
- eduPersonEntitlement: group/role membership strings
- displayName, mail: display name and email

---
### COMPUTE & USAGE MONITORING
- Account-level usage: org account > Account Overview > Usage tab
- Space-level usage: space > Usage button in header
- Usage broken down by space and by individual user
- Email alerts when approaching monthly compute limits
- No automated per-space or per-user budget alerts (monitoring is manual)
- rscloud R package enables programmatic space member management via API

---
### SECURITY & INFRASTRUCTURE
- All traffic encrypted via SSL; all data encrypted at rest
- Projects isolated in individual containers; no cross-container network access
- Hosted on AWS (NOT HIPAA-compliant infrastructure)
- GitHub Copilot integration available in RStudio projects (per-project, requires GitHub account)
- GitHub credentials NOT persisted across projects; must be re-entered per project

---
### KNOWN LIMITATIONS RELEVANT TO SURC
- Not HIPAA-compliant
- No custom package mirrors (would require separate Posit Package Manager)
- No HPC or hybrid on-premises integration
- GitHub credentials do not persist across projects
- Publishing Shiny apps/R Markdown to Posit Cloud deprecated end of 2024; use Posit Connect Cloud
- Background execution limit: jobs longer than 24 hours not supported

---
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


def get_full_context():
    return "\n\n".join([
        "=== PROJECT PLAN ===\n" + PROJECT_PLAN,
        "=== STATEMENT OF WORK SUMMARY ===\n" + SOW_SUMMARY,
        "=== TASK GUIDE: ACCOUNT PROVISIONING ===\n" + TASK_PROVISIONING,
        "=== TASK GUIDE: SSO CONFIGURATION ===\n" + TASK_SSO_CONFIG,
        "=== TASK GUIDE: RESOURCE LIMITS ===\n" + TASK_RESOURCE_LIMITS,
        "=== TASK GUIDE: RESEARCHER ONBOARDING GUIDE ===\n" + TASK_ONBOARDING_GUIDE,
        "=== TASK GUIDE: UAT PROCESS ===\n" + TASK_UAT,
        "=== POSIT CLOUD PRODUCT KNOWLEDGE BASE ===\n" + PRODUCT_KNOWLEDGE,
    ])
