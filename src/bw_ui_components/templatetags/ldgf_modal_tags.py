import ast
import logging
from django import template
from django.urls import reverse_lazy

register = template.Library()
logger = logging.getLogger(__name__)

@register.inclusion_tag("bw_ui_components/elements/ldgf_pop_modal.html", takes_context=True)
def ldgf_pop_modal(context, **kwargs):
    """
    Renders a custom, accessible, Preline-independent modal component.
    """
    # 1. Parse Extra Hidden Inputs safely
    extra_hidden_inputs_str = kwargs.get("extra_hidden_inputs", "")
    extra_hidden_inputs_dict = {}
    
    if extra_hidden_inputs_str:
        try:
            extra_hidden_inputs_dict = ast.literal_eval(extra_hidden_inputs_str)
            if not isinstance(extra_hidden_inputs_dict, dict):
                extra_hidden_inputs_dict = {}
        except (ValueError, SyntaxError) as e:
            logger.error(f"Failed to parse extra_hidden_inputs in ldgf_pop_modal: {e}")

    # Generate hidden input HTML markup
    extra_hidden_inputs_markup = [
        f'<input type="hidden" name="{key}" value="{value}">'
        for key, value in extra_hidden_inputs_dict.items()
    ]

    # 2. Map Tailwind max-width classes based on size
    size_map = {
        "sm": "sm:max-w-sm",
        "md": "sm:max-w-md lg:max-w-lg",
        "lg": "sm:max-w-lg lg:max-w-3xl",
        "xl": "sm:max-w-xl lg:max-w-5xl",
        "full": "sm:max-w-full sm:mx-4"
    }
    modal_size_class = size_map.get(kwargs.get("modal_size", "md"), size_map["md"])

    # 3. Resolve Action URL safely
    action_url = kwargs.get("action_url", None)
    action_url_pk = kwargs.get("action_url_pk", None)
    resolved_form_action_url = "#"
    
    if action_url:
        if action_url_pk:
            resolved_form_action_url = reverse_lazy(action_url, kwargs={"pk": action_url_pk})
        else:
            resolved_form_action_url = reverse_lazy(action_url)

    # 4. Build and return context
    return {
        # Core
        "modal_css_id": kwargs.get("modal_css_id"),
        "modal_size_class": modal_size_class,
        "modal_title": kwargs.get("modal_title", ""),
        
        # Form Data
        "is_form_modal": kwargs.get("is_form_modal", False),
        "form_object": kwargs.get("form_object", None),
        "is_upload_form": kwargs.get("is_upload_form", False),
        "form_id": kwargs.get("form_id", ""),
        "form_submit_text": kwargs.get("form_submit_text", "Submit"),
        "form_action_url": resolved_form_action_url,
        "form_method": kwargs.get("form_method", "post"),
        "enable_hidden_method": kwargs.get("enable_hidden_method", False),
        "is_only_checkbox_form": kwargs.get("is_only_checkbox_form", False),
        "custom_styled_checkboxes": kwargs.get("custom_styled_checkboxes", False),
        "extra_hidden_inputs_markup_list": extra_hidden_inputs_markup,
        
        # Buttons
        "is_submit_btn_enabled": kwargs.get("is_submit_btn_enabled", False),
        
        # Pass through global context (request, user, csrf_token)
        "request": context.get("request"),
        "csrf_token": context.get("csrf_token"),
    }
