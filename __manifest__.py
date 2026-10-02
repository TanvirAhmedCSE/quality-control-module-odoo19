{
    'name': "Quality Control",

    'summary': "QC Section Checking for product",

    'description': """
    Long description of module's purpose
    """,

    'author': "Tanvir",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Ntech/',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    # always loaded
    'data': [
        'security/quality_security.xml',
        'security/ir.model.access.csv',
        'security/record_rules.xml',
        'views/quality_check_views.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    # JS/XML for the Show/Hide Remarks button
    'assets': {
        'web.assets_backend': [
            'quality_control/static/src/js/remarks_toggle_field.js',
            'quality_control/static/src/xml/remarks_toggle_field.xml',
        ],
    },
}