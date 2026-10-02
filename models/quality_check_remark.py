from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .quality_control import ROLES


class QualityCheckRemark(models.Model):
    _name = "quality.check.remark"
    _description = "Quality Check Remark"

    check_id = fields.Many2one("quality.check", required=True, ondelete="cascade", index=True)
    user_id = fields.Many2one("res.users", string="By", required=True,
                              default=lambda self: self.env.user)
    stage = fields.Selection(list(ROLES.items()), string="Role")
    remarks = fields.Text(required=True)

    _check_user_stage_uniq = models.Constraint(
        'UNIQUE(check_id, user_id, stage)',
        'Each user can add only one remark per stage.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            check = self.env['quality.check'].browse(vals['check_id'])
            if not check.can_add_remark:
                raise ValidationError(_("You cannot add remarks at this stage."))
            vals['user_id'] = self.env.user.id
            vals['stage'] = check.state
        return super().create(vals_list)

    def _check_own(self):
        for rec in self:
            if rec.user_id != self.env.user or rec.stage != rec.check_id.state:
                raise ValidationError(
                    _("You can only edit or delete your own remarks during your stage."))

    def write(self, vals):
        self._check_own()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ondelete_check_own(self):
        self._check_own()