"""User roles, permissions, and group constants."""
from __future__ import annotations


# Bookkeeper user group name
BOOKKEEPER_GROUP_NAME = "Bookkeeper Group"
ASSISTANT_GROUP_NAME = "Assistant Group"
MANAGER_GROUP_NAME = "Manager Group"
READONLY_NEW_STAFF_MEMBER_GROUP_NAME = "New Staff Readonly Group"

# User types
CON_BOOKKEEPER = "bookkeeper"
CON_ASSISTANT = "assistant"
CON_MANAGER = "manager"
CON_CFO = "cfo"
CON_DEVELOPER = "developer"
CON_USER = "user"

# Permission names
ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME = (
    "assistant.assistant_has_full_manager_permissions"
)
ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME = "assistant_has_full_manager_permissions"

BOOKKEEPER_PERMISSION = "bookkeeper_user"
ASSISTANT_PERMISSION = "assistant_user"
MANAGER_PERMISSION = "manager_user"

# Read-only permissions for new staff member / read-only groups
DEFAULT_READONLY_PERMISSIONS_NEW_STAFF_MEMBER = [
    {
        "app_label": "special_assignment",
        "model_label": "specialassignment",
        "permissions_codename_labels": [
            "can_view_list",
            "view_specialassignment",
        ],
    },
    {
        "app_label": "task",
        "model_label": "task",
        "permissions_codename_labels": [
            "can_view_list",
            "view_task",
        ],
    },
    {
        "app_label": "job",
        "model_label": "job",
        "permissions_codename_labels": [
            "can_view_list",
            "view_job",
        ],
    },
    {
        "app_label": "discussion",
        "model_label": "discussion",
        "permissions_codename_labels": [
            "can_view_list",
            "view_discussion",
        ],
    },
    {
        "app_label": "note",
        "model_label": "note",
        "permissions_codename_labels": [
            "can_view_list",
            "view_note",
        ],
    },
    {
        "app_label": "document",
        "model_label": "document",
        "permissions_codename_labels": [
            "can_view_list",
            "view_document",
        ],
    },
    {
        "app_label": "important_contact",
        "model_label": "importantcontact",
        "permissions_codename_labels": [
            "can_view_list",
            "view_importantcontact",
        ],
    },
    {
        "app_label": "client_account",
        "model_label": "clientaccount",
        "permissions_codename_labels": [
            "can_view_list",
            "view_clientaccount",
        ],
    },
    {
        "app_label": "client",
        "model_label": "client",
        "permissions_codename_labels": [
            "can_view_list",
            "view_client",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffbriefcase",
        "permissions_codename_labels": [
            "view_staffbriefcase",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffaccounts",
        "permissions_codename_labels": [
            "view_staffaccounts",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffdocuments",
        "permissions_codename_labels": [
            "view_staffdocuments",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffnotes",
        "permissions_codename_labels": [
            "view_staffnotes",
        ],
        "extra_permissions": {"codename_labels": []},
    },
]

DEFAULT_READONLY_PERMISSIONS_NEW_STAFF_MEMBER = sorted(
    DEFAULT_READONLY_PERMISSIONS_NEW_STAFF_MEMBER, key=lambda x: x.get("app_label")
)

# Full operational permissions for active operational staff members
DEFAULT_PERMISSIONS_NEW_STAFF_MEMBER = [
    {
        "app_label": "special_assignment",
        "model_label": "specialassignment",
        "permissions_codename_labels": [
            "can_view_list",
            "view_specialassignment",
            "add_specialassignment",
            "change_specialassignment",
            "delete_specialassignment",
        ],
    },
    {
        "app_label": "task",
        "model_label": "task",
        "permissions_codename_labels": [
            "can_view_list",
            "add_task",
            "view_task",
            "change_task",
            "delete_task",
        ],
    },
    {
        "app_label": "job",
        "model_label": "job",
        "permissions_codename_labels": [
            "can_view_list",
            "add_job",
            "view_job",
            "change_job",
            "delete_job",
        ],
    },
    {
        "app_label": "discussion",
        "model_label": "discussion",
        "permissions_codename_labels": [
            "can_view_list",
            "view_discussion",
            "add_discussion",
            "change_discussion",
            "delete_discussion",
        ],
    },
    {
        "app_label": "note",
        "model_label": "note",
        "permissions_codename_labels": [
            "can_view_list",
            "view_note",
            "add_note",
            "delete_note",
            "change_note",
        ],
    },
    {
        "app_label": "document",
        "model_label": "document",
        "permissions_codename_labels": [
            "can_view_list",
            "view_document",
            "add_document",
            "delete_document",
            "change_document",
        ],
    },
    {
        "app_label": "important_contact",
        "model_label": "importantcontact",
        "permissions_codename_labels": [
            "can_view_list",
            "view_importantcontact",
            "add_importantcontact",
            "change_importantcontact",
            "delete_importantcontact",
        ],
    },
    {
        "app_label": "client_account",
        "model_label": "clientaccount",
        "permissions_codename_labels": [
            "can_view_list",
            "view_clientaccount",
            "add_clientaccount",
            "change_clientaccount",
            "delete_clientaccount",
        ],
    },
    {
        "app_label": "client",
        "model_label": "client",
        "permissions_codename_labels": [
            "can_view_list",
            "view_client",
            "add_client",
            "change_client",
            "delete_client",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffbriefcase",
        "permissions_codename_labels": [
            "view_staffbriefcase",
            "add_staffbriefcase",
            "change_staffbriefcase",
            "delete_staffbriefcase",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffaccounts",
        "permissions_codename_labels": [
            "view_staffaccounts",
            "add_staffaccounts",
            "change_staffaccounts",
            "delete_staffaccounts",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffdocuments",
        "permissions_codename_labels": [
            "view_staffdocuments",
            "add_staffdocuments",
            "change_staffdocuments",
            "delete_staffdocuments",
        ],
        "extra_permissions": {"codename_labels": []},
    },
    {
        "app_label": "staff_briefcase",
        "model_label": "staffnotes",
        "permissions_codename_labels": [
            "view_staffnotes",
            "add_staffnotes",
            "change_staffnotes",
            "delete_staffnotes",
        ],
        "extra_permissions": {"codename_labels": []},
    },
]
DEFAULT_PERMISSIONS_NEW_STAFF_MEMBER = sorted(
    DEFAULT_PERMISSIONS_NEW_STAFF_MEMBER, key=lambda x: x.get("app_label")
)

