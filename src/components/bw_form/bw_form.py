# -*- coding: utf-8 -*-#
# In a file called [project root]/components/calendar/calendar.py
from django.urls import reverse_lazy
from django_components import component


@component.register("bw_form")
class BWForm(component.Component):
    # Templates inside `[your apps]/components` dir and `[project root]/components` dir will be automatically found.
    # To customize which template to use based on context
    # you can override def get_template_name() instead of specifying the below variable.
    template_name = "bw_form/bw_form.html"
    js_file = "bw_form/bw_form.js"
    css_file = "bw_form/bw_form.css"

    class Cache:
        enabled = False

    # This component takes one parameter, a date string to show in the template
    def get_context_data(
        self,
        form,
        form_title="",
        form_subtitle="",
        form_id="",
        form_method="post",
        form_action_url="",
        form_action_kwargs={},
        is_upload_form=False,
        submit_btn_text="Create",
        perms="",
        current_password=None,
        hide_back_btn=False,
        hide_submit_btn=False,
        is_btns_enabled=True,
        extra_form_css_classes: str | None = None,
    ):
        # form_action_url syntax: app_name:endpoint: client:details
        # if form_action_url is not None:
        #
        #     if form_action_kwargs:
        #         form_action_url = reverse_lazy(form_action_url, kwargs=form_action_kwargs)
        #     else:
        #         form_action_url = reverse_lazy(form_action_url)
        #
        #     debugging_print(form_action_url)
        return {
            "form": form,
            "form_subtitle": form_subtitle,
            "form_title": form_title,
            "form_id": form_id,
            "form_method": form_method,
            "form_action_url": form_action_url,
            "is_upload_form": is_upload_form,
            "submit_btn_text": submit_btn_text,
            "perms": perms,
            "current_password": current_password,
            "hide_back_btn": hide_back_btn,
            "hide_submit_btn": hide_submit_btn,
            "is_btns_enabled": is_btns_enabled,
            "extra_form_css_classes": extra_form_css_classes,
        }
