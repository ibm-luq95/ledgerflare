# -*- coding: utf-8 -*-#
import inflection
from django.contrib.sites.models import Site

from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.general import IS_SHOW_CREATED_AT, IS_SHOW_LABELS_IN_FILTER_FORM
from core.forms.per_page_form import PerPageForm
from site_settings.models import SectionDescription


class BWSectionDescriptionHelperMixin:
    """
    Mixin class that adds section description data to the context of a view.
    """

    def get_context_data(self, **kwargs):
        """
        Retrieves the context data for the view, including the section description data.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The context data for the view, including the section description data.

        """
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Get the current domain from the request
        domain = self.request.get_host()

        # Get the site object with the matching domain
        site_object = Site.objects.filter(domain=domain).first()

        if site_object:
            # Get the section description objects for the site
            bw_section_description = SectionDescription.objects.filter(site=site_object)

            # Create a dictionary with the section title as the key and the description as the value
            bw_section_description_data = {
                item.section_title: item.description for item in bw_section_description
            }

            # Add the section description data to the context
            context.setdefault("bw_section_description", bw_section_description_data)

        return context


class BWBaseListViewMixin:
    """
    Mixin class that provides common functionality for list views.

    Attributes:
        paginate_by (int): The number of items to display per page.
        is_show_labels_in_filter_form (bool): Whether to show labels in the filter form.

    Methods:
        get_context_data(**kwargs) -> dict: Retrieves the context data for the view.
        get_paginate_by(queryset) -> int: Paginate by specified value in querystring, or use default class property value.

    """

    paginate_by = LIST_VIEW_PAGINATE_BY
    is_show_labels_in_filter_form = IS_SHOW_LABELS_IN_FILTER_FORM
    page_title: str = ""

    def get_context_data(self, **kwargs):
        """
        Retrieves the context data for the view.

        This method adds additional data to the context, such as the value of `is_show_created_at`,
        the `per_page_filter_form`, and the `total_records` if applicable.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The context data for the view.

        """
        # Call the base implementation first to get a context
        context: dict = super().get_context_data(**kwargs)
        context.setdefault("is_show_created_at", IS_SHOW_CREATED_AT)
        per_page_number = self.request.GET.get("per_page", LIST_VIEW_PAGINATE_BY)
        per_page_form = PerPageForm(initial={"per_page": per_page_number})
        context.setdefault("per_page_filter_form", per_page_form)
        if "paginator" in context and context["paginator"] is not None:
            context.setdefault("total_records", context["paginator"].count)
        elif "page_obj" in context and context["page_obj"] is not None:
            context.setdefault("total_records", context["page_obj"].paginator.count)
        elif "object_list" in context and context["object_list"] is not None:
            if isinstance(context["object_list"], list):
                context.setdefault("total_records", len(context["object_list"]))
            else:
                context.setdefault(
                    "total_records",
                    getattr(context["object_list"], "count", lambda: 0)(),
                )
        elif hasattr(self, "object_list"):
            context.setdefault(
                "total_records",
                getattr(self.object_list, "count", lambda: 0)(),
            )
        if hasattr(self, "modal"):
            if hasattr(self.model, "_meta"):
                context.setdefault("app_label", self.model._meta.app_label)
            if hasattr(self, "model"):
                excluded_fields = [
                    "id",
                    "updated_at",
                    "metadata",
                    "deleted_at",
                    "is_deleted",
                ]
                names_list = [field.name for field in getattr(self.model, "_meta").fields]
                new_list = [
                    inflection.humanize(name)
                    for name in names_list
                    if name not in excluded_fields
                ]
                context.setdefault("fields", new_list)
        context.setdefault("title", self.page_title)
        if hasattr(self, "list_type"):
            context.setdefault("list_type", self.list_type)
        if hasattr(self, "page_header"):
            context.setdefault("page_header", self.page_header)
        if hasattr(self, "component_path"):
            context.setdefault("component_path", self.component_path)

        if hasattr(self, "is_show_create_btn"):
            context.setdefault("is_show_create_btn", self.is_show_create_btn)
        if hasattr(self, "actions_base_url"):
            context.setdefault("actions_base_url", self.actions_base_url)
        if hasattr(self, "filter_cancel_url"):
            context.setdefault("filter_cancel_url", self.filter_cancel_url)
        if hasattr(self, "pagination_list_url_name"):
            context.setdefault("pagination_list_url_name", self.pagination_list_url_name)


        if hasattr(self, "is_header_enabled"):
            context.setdefault("is_header_enabled", self.is_header_enabled)

        if hasattr(self, "subtitle"):
            context.setdefault("subtitle", self.subtitle)

        if hasattr(self, "table_header_subtitle"):
            context.setdefault("table_header_subtitle", self.table_header_subtitle)

        if hasattr(self, "actions_items"):
            context.setdefault("actions_items", self.actions_items)

        if hasattr(self, "show_info_icon"):
            context.setdefault("show_info_icon", self.show_info_icon)

        if hasattr(self, "base_url_name"):
            context.setdefault("base_url_name", self.base_url_name)

        if hasattr(self, "empty_label"):
            context.setdefault("empty_label", self.empty_label)

        if hasattr(self, "is_filters_enabled"):
            context.setdefault("is_filters_enabled", self.is_filters_enabled)

        if hasattr(self, "is_footer_enabled"):
            context.setdefault("is_footer_enabled", self.is_footer_enabled)

        if hasattr(self, "is_actions_menu_enabled"):
            context.setdefault("is_actions_menu_enabled", self.is_actions_menu_enabled)

        if hasattr(self, "filterset"):
            if hasattr(self.filterset, "form"):
                context.setdefault("filter_form", getattr(self.filterset, "form"))

        # context.update()
        return context

    def get_paginate_by(self, queryset):
        """
        Paginate by specified value in querystring, or use default class property value.

        Args:
            queryset: The queryset to paginate.

        Returns:
            int: The number of items to display per page.

        """
        per_page_num = self.request.GET.get("per_page", LIST_VIEW_PAGINATE_BY)
        return per_page_num
