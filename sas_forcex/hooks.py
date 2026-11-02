app_name = "sas_forcex"
app_title = "ForceX"
app_publisher = "SAS Infosystem Pvt Ltd"
app_description = "ForceX platform layer: Desk theme, rebranding and the shared forcex.ui component kit"
app_email = "subhapriyo.banerjee@sasinfosystem.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "sas_forcex",
# 		"logo": "/assets/sas_forcex/logo.png",
# 		"title": "SAS ForceX",
# 		"route": "/sas_forcex",
# 		"has_permission": "sas_forcex.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sas_forcex/css/sas_forcex.css"
# app_include_js = "/assets/sas_forcex/js/sas_forcex.js"

# include js, css files in header of web template
# web_include_css = "/assets/sas_forcex/css/sas_forcex.css"
# web_include_js = "/assets/sas_forcex/js/sas_forcex.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sas_forcex/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sas_forcex/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sas_forcex.utils.jinja_methods",
# 	"filters": "sas_forcex.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sas_forcex.install.before_install"
# after_install = "sas_forcex.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sas_forcex.uninstall.before_uninstall"
# after_uninstall = "sas_forcex.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sas_forcex.utils.before_app_install"
# after_app_install = "sas_forcex.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sas_forcex.utils.before_app_uninstall"
# after_app_uninstall = "sas_forcex.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "sas_forcex.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sas_forcex.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sas_forcex.tasks.all"
# 	],
# 	"daily": [
# 		"sas_forcex.tasks.daily"
# 	],
# 	"hourly": [
# 		"sas_forcex.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sas_forcex.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sas_forcex.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sas_forcex.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "sas_forcex.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sas_forcex.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sas_forcex.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sas_forcex.utils.before_request"]
# after_request = ["sas_forcex.utils.after_request"]

# Job Events
# ----------
# before_job = ["sas_forcex.utils.before_job"]
# after_job = ["sas_forcex.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sas_forcex.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# ---- ForceX platform assets ---------------------------------------------------
# This app holds ONLY what every ForceX tenant shares: the Desk palette, the
# shared component styles, the rebrand layer and the forcex.ui JS kit.
# Product features live in their own apps (FLEETO → sas_forcex_fleeto).
#   forcex_harbour         ForceX Harbour light/dark theme (re-tints v16 Espresso tokens)
#   (forcex_desk_theme.bundle.css kept in public/css but no longer loaded)
#   forcex_components      .fx-* design system used by forcex.ui helpers
app_include_css = ["forcex_harbour.bundle.css", "forcex_components.bundle.css"]
# Harbour also styles the login / portal pages.
web_include_css = ["forcex_harbour.bundle.css"]
# forcex_rebrand loads first so upstream names (Frappe, ERPNext, HRMS, ...) are
# replaced with ForceX names before other ForceX code renders anything.
app_include_js = ["forcex_harbour.bundle.js", "forcex_rebrand.bundle.js", "forcex_ui.bundle.js"]
# Same rebranding on website pages (login, portal).
web_include_js = ["forcex_rebrand.bundle.js"]

# ---- ForceX theme (ForceX Theme Settings single) --------------------------------
# Logic: sas_forcex/theme_engine.py (pure, unit-tested) · Frappe glue: sas_forcex/theme.py
# Desk gets the theme in frappe.boot.forcex_theme (also switches search off per role);
# website/login pages get an inline <style> + <script> in <head>.
extend_bootinfo = ["sas_forcex.theme.extend_bootinfo"]
update_website_context = ["sas_forcex.theme.update_website_context"]
# Fresh sites start with the ForceX palette prefilled (existing sites: patch v16_0).
after_install = "sas_forcex.theme.after_install"
