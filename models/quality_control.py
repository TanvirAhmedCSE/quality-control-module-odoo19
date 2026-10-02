from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

MANAGER = 'quality_control.group_quality_check_manager'
SUPERVISOR = 'quality_control.group_quality_check_supervisor'

# Each role works on one stage: User -> draft, Supervisor -> supervisor, Manager -> manager
STAGES = [('draft', 'Draft'), ('supervisor', 'Supervisor'), ('manager', 'Manager')]
ROLES = {'draft': 'User', 'supervisor': 'Supervisor', 'manager': 'Manager'}


class QualityCheck(models.Model):
    _name = "quality.check"
    _description = "Quality Control Check"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    # Fields a Manager may write (approve/fail/cancel via state, remarks).
    MANAGER_WRITABLE = {'state', 'my_remarks', 'message_main_attachment_id'}

    # FIELDS

    name = fields.Char(string="Reference", copy=False, default="New")
    inspector_id = fields.Many2one("res.users", "Main Checker", required=True, readonly=True,
                                   default=lambda self: self.env.user)
    additional_inspector_ids = fields.Many2many("res.users", string="Additional Inspectors")
    check_date = fields.Date(string="Check Date", default=fields.Date.today)
    quantity_lines = fields.One2many("quality.check.line", "line_id", string="Product Lines")
    result = fields.Selection([("pass", "Pass"), ("fail", "Fail")], string="Result", tracking=True)
    state = fields.Selection(
        STAGES + [('approved', 'Approved'), ('failed', 'Failed'), ('cancel', 'Cancelled')],
        string="Status", default=lambda self: self._get_my_stage(), tracking=True)
    # Stage the check started in (never changes afterwards)
    origin_state = fields.Selection(STAGES, string="Started At", readonly=True, copy=False,
                                    default=lambda self: self._get_my_stage())

    # Per-user remarks
    remark_ids = fields.One2many("quality.check.remark", "check_id", string="Remarks")
    remarks_html = fields.Html(string="Remarks", compute="_compute_remarks", sanitize=False)
    my_remarks = fields.Text(string="My Remarks", compute="_compute_remarks",
                             inverse="_inverse_my_remarks")

    # UI-control fields, all filled by _compute_ui_flags
    my_stage = fields.Char(compute="_compute_ui_flags")
    is_additional_inspector = fields.Boolean(compute="_compute_ui_flags")
    can_edit = fields.Boolean(compute="_compute_ui_flags")
    can_add_remark = fields.Boolean(compute="_compute_ui_flags")
    my_remarks_label = fields.Char(compute="_compute_ui_flags")
    # Carrier field for the remarks_toggle widget. Holds no data.
    show_remarks = fields.Boolean(compute="_compute_ui_flags")

    # Users that can be picked as Additional Inspectors (depends on origin_state)
    allowed_inspector_ids = fields.Many2many(
        "res.users", string="Allowed Additional Inspectors",
        compute="_compute_allowed_inspector_ids")

    # COMPUTES / CONSTRAINTS

    @api.model
    def _get_my_stage(self):
        """The stage the current user works on, decided by the user's group."""
        if self.env.user.has_group(MANAGER):
            return 'manager'
        if self.env.user.has_group(SUPERVISOR):
            return 'supervisor'
        return 'draft'

    @api.depends('inspector_id', 'additional_inspector_ids', 'state')
    @api.depends_context('uid')
    def _compute_ui_flags(self):
        """A person can edit / write remarks only while the check is in their own stage.
        - Edit: must be the Main or an Additional Inspector (so never a Manager).
        - Remarks: Draft needs to be an inspector, Supervisor/Manager stage = any Supervisor/Manager."""
        user = self.env.user
        my_stage = self._get_my_stage()
        for rec in self:
            is_additional = user in rec.additional_inspector_ids
            is_inspector = is_additional or user == rec.inspector_id
            my_turn = rec.state == my_stage
            rec.my_stage = my_stage
            rec.is_additional_inspector = is_additional
            rec.can_edit = my_turn and is_inspector
            rec.can_add_remark = my_turn and (rec.state != 'draft' or is_inspector)
            rec.my_remarks_label = "%s Remarks (%s):" % (ROLES.get(rec.state, ''), user.name)
            rec.show_remarks = True

    @api.depends('origin_state')
    def _compute_allowed_inspector_ids(self):
        """Managers are never allowed. Started in Draft: any internal non-Manager user.
        Started in Supervisor stage: Supervisors only."""
        users = self.env['res.users'].search([('share', '=', False)])
        managers = users.filtered(lambda u: u.has_group(MANAGER))
        supervisors = users.filtered(lambda u: u.has_group(SUPERVISOR))
        for rec in self:
            rec.allowed_inspector_ids = supervisors if rec.origin_state == 'supervisor' else users - managers

    @api.constrains('additional_inspector_ids')
    def _check_additional_inspectors(self):
        for rec in self:
            if rec.additional_inspector_ids - rec.allowed_inspector_ids:
                raise ValidationError(
                    _("Additional Inspectors must be Supervisors (not Managers).")
                    if rec.origin_state == 'supervisor'
                    else _("Managers cannot be Additional Inspectors."))

    @api.depends('remark_ids.remarks', 'remark_ids.user_id', 'remark_ids.stage', 'state')
    @api.depends_context('uid')
    def _compute_remarks(self):
        """my_remarks: text of the current user's own remark for this stage.
        remarks_html: read-only stack of the other remarks (label + author + text)."""
        for rec in self:
            mine = rec.remark_ids.filtered(lambda r: r.user_id == self.env.user and r.stage == rec.state)
            rec.my_remarks = mine.remarks or False
            others = (rec.remark_ids - mine) if rec.can_add_remark else rec.remark_ids
            rec.remarks_html = Markup('').join(
                Markup('<div class="mb-3"><div class="fw-bold">%s Remarks (%s):</div>'
                       '<div style="white-space: pre-wrap">%s</div></div>')
                % (ROLES[r.stage], r.user_id.name, r.remarks)
                for r in others
            ) or False

    def _inverse_my_remarks(self):
        """Creates, updates, or (if emptied) deletes the current user's remark for the
        current stage. Permissions are enforced by quality.check.remark."""
        user = self.env.user
        for rec in self:
            mine = rec.remark_ids.filtered(lambda r: r.user_id == user and r.stage == rec.state)
            text = (rec.my_remarks or '').strip()
            if not text:
                mine.unlink()
            elif mine:
                mine.remarks = rec.my_remarks
                rec.message_post(body=_("%s remarks updated by %s") % (ROLES[rec.state], user.name))
            else:
                self.env['quality.check.remark'].create({'check_id': rec.id, 'remarks': rec.my_remarks})
                rec.message_post(body=_("%s remarks added by %s") % (ROLES[rec.state], user.name))

    # ORM OVERRIDES

    @api.model_create_multi
    def create(self, vals_list):
        """The starting stage is forced from the creator's role.
        (Managers have no create access, see ir.model.access.csv.)"""
        for vals in vals_list:
            vals['state'] = vals['origin_state'] = self._get_my_stage()
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su and self.env.user.has_group(MANAGER) and set(vals) - self.MANAGER_WRITABLE:
            raise ValidationError(
                _("Managers can only add remarks and approve, fail or cancel a check."))
        res = super().write(vals)
        if 'quantity_lines' in vals:
            for rec in self:
                rec.message_post(body=_("Product Line updated by %s") % self.env.user.name)
        return res

    @api.ondelete(at_uninstall=False)
    def _ondelete_check(self):
        """Only draft checks can be deleted. Only Managers have delete access
        (see ir.model.access.csv)."""
        if any(rec.state != "draft" for rec in self):
            raise ValidationError(_("You can only delete a QC when it is in draft state."))

    # BUSINESS ACTIONS (button names are used by the form view)

    def action_send_to_supervisor(self):
        if self.state == 'draft':
            self.state = 'supervisor'

    def action_reset_to_draft(self):
        """Recall / send back. Only for checks that started in Draft."""
        if self.state == 'supervisor' and self.origin_state == 'draft':
            self.state = 'draft'

    def action_send_to_manager(self):
        if self.state == 'supervisor':
            self.state = 'manager'

    def action_cancel(self):
        if self.state == 'manager':
            self.state = 'cancel'

    def action_approved(self):
        """Button is shown only when result is 'pass' (enforced in the view)."""
        if self.state == 'manager':
            self.state = 'approved'

    def action_failed(self):
        """Button is shown only when result is 'fail' (enforced in the view)."""
        if self.state == 'manager':
            self.state = 'failed'