import { Component, onMounted, onPatched, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// "Hide Remarks" / "Show Remarks" button
export class RemarksToggleField extends Component {
    static template = "quality_control.RemarksToggleField";
    static props = { ...standardFieldProps };

    setup() {
        this.rootRef = useRef("root");
        this.state = useState({ shown: true });
        onMounted(() => this.applyVisibility());
        onPatched(() => this.applyVisibility());
    }

    get target() {
        const form = this.rootRef.el && this.rootRef.el.closest(".o_form_sheet, .o_form_renderer");
        return form && form.querySelector(".o_quality_remarks");
    }

    applyVisibility() {
        const el = this.target;
        if (el) {
            if (this.state.shown) {
                el.style.removeProperty("display");
            } else {
                el.style.setProperty("display", "none", "important");
            }
        }
    }

    onClick() {
        this.state.shown = !this.state.shown;
        this.applyVisibility();
    }
}

registry.category("fields").add("remarks_toggle", {
    component: RemarksToggleField,
    supportedTypes: ["boolean"],
});