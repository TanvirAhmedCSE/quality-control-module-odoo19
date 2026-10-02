<div align="center">

# Quality Control

A role-based **Quality Check** module for Odoo. Inspectors record received and damaged quantities per product, and every check moves through a **User → Supervisor → Manager** approval workflow, with per-user remarks at each stage and a full audit trail in the chatter. [**[See Screenshots]**](#screenshots)

![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67?logo=odoo&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

---

## Features

- **Three-level approval workflow**: Draft → Supervisor → Manager → Approved / Failed / Cancelled.
- **Three independent roles**: User, Supervisor and Manager are separate security groups with no hierarchy (no `implied_ids`). Each user gets exactly one role, and every group has its own access rights and record rules.
- **One stage per role**: User works on Draft, Supervisor on the Supervisor stage, Manager on the Manager stage. A person can edit a check or write a remark only while the check is in their own stage.
- **Role-aware starting stage**: a check starts in the stage matching its creator's role (User → Draft, Supervisor → Supervisor stage). This is enforced server-side and cannot be spoofed from the client.
- **Read-only Manager role**: Managers cannot create or edit checks. They review, add remarks, and make the final decision (Approve / Fail / Cancel).
- **Product lines** with *Receive Qty*, *Damage Qty* and an automatically computed *Remain Qty*, plus validation that damage can never exceed received quantity.
- **Additional Inspectors**: invite more people to a check, with the allowed picker list depending on the stage the check started in. Managers can never be picked.
- **Per-user, per-stage remarks**: every participant writes their own remark. Others' remarks are shown read-only in a stacked view.
- **Show / Hide Remarks** button, a custom OWL field widget that toggles the section in the browser only, so the form is never marked as modified.
- **Record-level security**: Users only see checks they created or were added to as additional inspectors. Supervisors and Managers see all checks.
- **Chatter tracking** on status and result, plus log messages when remarks or product lines change.
- **Color-coded list view**: the whole row is colored based on the check's stage and your role. Red = the check is in your own stage (always wins). Green = you are an additional inspector and the check is not in your own stage.
- **Delete protection**: only Managers can delete checks, and only while they are in Draft. Users and Supervisors do not get a Delete option.

---

## Workflow

```
 User creates          Supervisor creates
      │                        │
      ▼                        │
   [Draft] ──Send To Supervisor──▶ [Supervisor] ──Send To Manager──▶ [Manager]
      ▲                              │                                   │
      └─── Reset / Recall to Draft ──┘                    ┌──────────────┼──────────────┐
      (only if the check started in Draft)                ▼              ▼              ▼
                                                     [Approved]      [Failed]      [Cancelled]
                                                    (result=pass)  (result=fail)
```

Managers do not create checks. They only act on checks that reach the Manager stage.

| Action | Available to | Condition |
|---|---|---|
| **Send To Supervisor** | Main Inspector / additional inspector with the User role | State is Draft |
| **Reset To Draft** | Main Inspector / additional inspector with the User role | State is Supervisor, check started in Draft |
| **Recall To Draft** | Supervisor | State is Supervisor, check started in Draft |
| **Send To Manager** | Supervisor | State is Supervisor |
| **Approve** | Manager | State is Manager and Result = *Pass* |
| **Fail** | Manager | State is Manager and Result = *Fail* |
| **Cancel** | Manager | State is Manager |

---

## Roles and Permissions

The module adds a **Quality Management** category with a **Quality Level1** privilege containing three **independent** groups: `User`, `Supervisor` and `Manager`. There is no hierarchy and no group implies another, so assign **exactly one role per user**.

| Group | Sees | Can do |
|---|---|---|
| **User** | Own checks and checks where they are an additional inspector | Create checks, edit inspection data in Draft, send to Supervisor |
| **Supervisor** | All checks | Create checks, review and forward checks to the Manager, recall to Draft |
| **Manager** | All checks | Read-only review. Add remarks, approve, fail or cancel. Can delete Draft checks. Cannot create or edit checks |

### Access rights

| Group | Quality Check | Check Line | Remark |
|---|---|---|---|
| User | read, write, create | full | full |
| Supervisor | read, write, create | full | full |
| Manager | read, write, delete (no create) | read only | full |

A Manager's `write` access on a check is limited in code to `state` (Approve / Fail / Cancel) and their own remark.

Record rules: **User** is limited to checks where they are the main or an additional inspector (applied to checks, lines and remarks). **Supervisor** and **Manager** have access to all records.

### Manager restrictions

- A Manager **cannot create** a check. The **New** button is hidden for Managers because they have no create access.
- A Manager **cannot edit** any check data (reference, date, additional inspectors, result, product lines). On the server, a Manager can write only `state` (for Approve / Fail / Cancel) and their own remark, and has read-only access to product lines.
- A Manager can add a remark only on a saved check that is in the Manager stage.
- A Manager can never be an Additional Inspector.

### Who can edit what

Editing follows your role's own stage: you can edit only while the check is in that stage, and only if you are the Main Inspector or an Additional Inspector.

| Stage | Can edit result and product lines |
|---|---|
| Draft | Main Inspector, or an Additional Inspector with the User role |
| Supervisor | A Supervisor who is the Main Inspector or an Additional Inspector |
| Manager | Nobody |
| Approved / Failed / Cancelled | Nobody |

`Reference`, `Additional Inspectors` and `Check Date` are editable only while the check is still in the stage it started in, and only by those who can edit inspection data. They are always read-only for Managers.

### Who can delete

| Group | Delete a check |
|---|---|
| User | No |
| Supervisor | No |
| Manager | Yes, only while the check is in Draft |

### Additional Inspector picker

| Check started as | Selectable users |
|---|---|
| User (Draft) | Any internal user except Managers |
| Supervisor | Supervisors only (no Managers, no plain Users) |

The rule is enforced both in the form domain and by a server-side constraint.

---

## List View Colors

In the list view the **whole row** is colored depending on your role and the stage of each check. Your "own stage" is the stage you are responsible for:

| Your role | Your own stage |
|---|---|
| User | Draft |
| Supervisor | Supervisor |
| Manager | Manager |

| Row color | When |
|---|---|
| **Red** | The check is in **your own stage**. This always wins, even if you are also an additional inspector on that check. |
| **Green** | You are an **additional inspector** on the check **and** it is **not** in your own stage. |
| Default | Any other check (not in your own stage and you are not an additional inspector). |

Since Managers can never be additional inspectors, they only see red rows (checks in the Manager stage) and default rows.

---

## Remarks System

Remarks are stored in a dedicated model (`quality.check.remark`) instead of a single text field per role.

- Each user can write **one remark per stage** (a unique `check + user + stage` constraint).
- Only the users responsible for the current stage can add a remark (see the table below).
- A user can **edit or delete only their own remark, and only during its stage**. This is enforced on the server as well as in the form.
- Emptying your remark text deletes it.
- Other participants' remarks appear in a read-only stacked block as `<Role> Remarks (<User>):`, and your own remark appears in an editable box.
- Every add or update is logged in the chatter.

| Stage | Who can add a remark |
|---|---|
| Draft | Main Inspector, or an Additional Inspector with the User role |
| Supervisor | Any Supervisor |
| Manager | Any Manager (on a saved check) |

---

## Screenshots

**Main Checker: Quality Checks List (sees only own records and the records as additional inspector himself)**

<img src="mvvbv/1.png" width="100%"/>

**Main Checker: Draft with Remarks & QC product lines**

<img src="mvvbv/2.png" width="100%"/>

**Additional Inspector: Adds QC product line and Remarks**

<img src="mvvbv/3.png" width="100%"/>

**Sent to Supervisor (status moves to Supervisor, Reset To Draft available)**

<img src="mvvbv/4.png" width="100%"/>

**Supervisor: Quality Checks List (all records visible)**

<img src="mvvbv/5.png" width="100%"/>

**Supervisor: Review and Remarks (remarks added, ready to send to Manager)**

<img src="mvvbv/6.png" width="100%"/>

**Sent to Manager (status moves to Manager)**

<img src="mvvbv/7.png" width="100%"/>

**Manager: Quality Checks List (all records visible)**

<img src="mvvbv/8.png" width="100%"/>

**Manager: Review and Approve (manager remarks added, ready to approve)**

<img src="mvvbv/9.png" width="100%"/>

**Approved: Final Status (full chatter log of the workflow) with using Hide Remarks button**

<img src="mvvbv/10.png" width="100%"/>

**Supervisor: Creates Record, Adds QC Product Lines, Fail Result and a Remark**

<img src="mvvbv/11.png" width="100%"/>

**Sent to Manager (status moves to Manager) and Manager added remark**

<img src="mvvbv/12.png" width="100%"/>

**Failed: Final Status (Manager marks Fail, full chatter log of the workflow)**

<img src="mvvbv/13.png" width="100%"/>

---

## Data Model

### `quality.check`

| Field | Type | Description |
|---|---|---|
| `name` | Char | Reference (default `New`) |
| `inspector_id` | Many2one `res.users` | Main Checker (set automatically, read-only) |
| `additional_inspector_ids` | Many2many `res.users` | Extra inspectors (never Managers) |
| `check_date` | Date | Defaults to today |
| `result` | Selection | `pass` / `fail` (tracked) |
| `state` | Selection | `draft`, `supervisor`, `manager`, `approved`, `failed`, `cancel` (tracked) |
| `origin_state` | Selection | Stage the check started in (never changes) |
| `quantity_lines` | One2many | Product lines |
| `remark_ids` | One2many | Per-user remarks |

### `quality.check.line`

| Field | Type | Description |
|---|---|---|
| `product_id` | Many2one `product.product` | Product |
| `rec_qty` | Float | Received quantity |
| `damage_qty` | Float | Damaged quantity (must be ≤ received) |
| `remain_qty` | Float (computed, stored) | `rec_qty - damage_qty` |

### `quality.check.remark`

| Field | Type | Description |
|---|---|---|
| `check_id` | Many2one `quality.check` | Parent check (cascade delete) |
| `user_id` | Many2one `res.users` | Author |
| `stage` | Selection | Stage in which the remark was written |
| `remarks` | Text | Remark body |

---

## Usage

1. Assign each user one role (**User**, **Supervisor** or **Manager**) under *Quality Management → Quality Level1* on the user form.
2. Open the **Quality Check** menu → **Quality Checks**.
3. As a User or Supervisor, click **New**, add product lines (received and damaged quantities) and choose a **Result**.
4. Optionally add **Additional Inspectors** and write your remarks.
5. Move the check forward with the header buttons. Each role sees only the buttons it is allowed to use.
6. The Manager reviews the check, optionally adds a remark, and makes the final decision: **Approve**, **Fail** or **Cancel**.

---

## Project Structure

```
quality_control/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── quality_control.py          # quality.check (workflow, permissions, remarks logic)
│   ├── quality_control_line.py     # quality.check.line (product lines)
│   └── quality_check_remark.py     # quality.check.remark (per-user remarks)
├── security/
│   ├── quality_security.xml        # category, privilege and 3 independent groups
│   ├── ir.model.access.csv         # access rights per group
│   └── record_rules.xml            # record-level rules per group
├── views/
│   ├── quality_check_views.xml     # list, form and action
│   └── menu.xml
└── static/src/
    ├── js/remarks_toggle_field.js  # OWL widget: Show/Hide Remarks
    └── xml/remarks_toggle_field.xml
```

## Author

**Tanvir**: [@TanvirAhmedCSE](https://github.com/TanvirAhmedCSE)

Contributions, issues and feature requests are welcome.
