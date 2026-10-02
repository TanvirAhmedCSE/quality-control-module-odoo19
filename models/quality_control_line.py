from odoo import api, fields, models
from odoo.exceptions import ValidationError


class QualityCheckLine(models.Model):
    _name = "quality.check.line"
    _description = "Quality Control Check Line"

    product_id = fields.Many2one('product.product', 'Product', required=True)

    rec_qty = fields.Float('Receive Qty', required=True)

    damage_qty = fields.Float('Damage Qty', required=True)

    remain_qty = fields.Float('Remain Qty', required=False, compute="_compute_remain_qty", store=True)
    
    line_id = fields.Many2one('quality.check', 'Line', required=True, ondelete='cascade')

    @api.depends("rec_qty", "damage_qty")
    def _compute_remain_qty(self):
        for line in self:
            line.remain_qty = line.rec_qty - line.damage_qty

    @api.constrains("damage_qty", "rec_qty")
    def _check_passed_quantity(self):
        """Validates that damage quantity does not exceed receive quantity."""
        for line in self:
            if line.damage_qty > line.rec_qty:
                raise ValidationError(
                    "Damage Qty can not be greater than receive qty"
                )
