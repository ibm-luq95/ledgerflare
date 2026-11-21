from __future__ import annotations

import pytest
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import RequestFactory
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import TaskStatusEnum, TaskTypeEnum
from job.models import JobProxy
from task.filters import TaskFilter
from task.models import TaskProxy


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def setup_groups(db):
    call_command("create_groups")


@pytest.mark.unit
def test_task_header_render_defaults(rf: RequestFactory):
    """Test task header component rendering with default context."""
    request = rf.get("/dashboard/task/")
    context = {
        "request": request,
        "page_header": "Tasks",
        "kpi_stats": {"total_tasks": 42},
        "total_records": 42,
        "actions_base_url": "dashboard:task",
        "is_show_create_btn": True,
    }
    rendered = render_to_string(
        "bw_components/task/header.html", context, request=request
    )

    assert "Tasks" in rendered
    assert "42" in rendered
    assert "total" in rendered
    assert "Export" in rendered
    assert "CSV (.csv)" in rendered
    assert "Excel (.xlsx)" in rendered
    assert "taskViewTableBtn" in rendered
    assert "taskViewGridBtn" in rendered
    assert "/dashboard/task/create" in rendered
    assert "New Task" in rendered


@pytest.mark.unit
def test_task_header_render_custom_context(rf: RequestFactory):
    """Test task header with custom title, subtitle, and hidden create button."""
    request = rf.get("/dashboard/task/?status=in_progress")
    context = {
        "request": request,
        "page_header": "Custom Task Board",
        "subtitle": "Custom workflow tracking subtitle",
        "kpi_stats": {"total_tasks": 15},
        "total_records": 15,
        "actions_base_url": "dashboard:task",
        "is_show_create_btn": False,
        "export_url": "/dashboard/task/export",
    }
    rendered = render_to_string(
        "bw_components/task/header.html", context, request=request
    )

    assert "Custom Task Board" in rendered
    assert "Custom workflow tracking subtitle" in rendered
    assert "15" in rendered
    assert "New Task" not in rendered
    assert "/dashboard/task/export/excel/?status=in_progress" in rendered
    assert "/dashboard/task/export/csv/?status=in_progress" in rendered


@pytest.mark.unit
def test_task_kpi_ribbon_render_metrics(rf: RequestFactory):
    """Test KPI ribbon renders all 5 metric cards with formatted counts and links."""
    request = rf.get("/dashboard/task/")
    kpi_stats = {
        "total_tasks": 1250,
        "in_progress_tasks": 45,
        "past_due_tasks": 12,
        "urgent_tasks": 7,
        "completed_tasks": 1186,
    }
    context = {
        "request": request,
        "kpi_stats": kpi_stats,
    }
    rendered = render_to_string(
        "bw_components/task/kpi_ribbon.html", context, request=request
    )

    assert "Total Tasks" in rendered
    assert "1,250" in rendered
    assert "In Progress" in rendered
    assert "45" in rendered
    assert "Past Due" in rendered
    assert "12" in rendered
    assert "Urgent" in rendered
    assert "7" in rendered
    assert "Completed" in rendered
    assert "1,186" in rendered

    # Verify URLs
    assert 'href="/dashboard/task/"' in rendered
    assert 'href="/dashboard/task/?status=in_progress"' in rendered
    assert 'href="/dashboard/task/?status=past_due"' in rendered
    assert 'href="/dashboard/task/?task_type=urgent"' in rendered
    assert 'href="/dashboard/task/?status=completed"' in rendered


@pytest.mark.unit
def test_task_kpi_ribbon_empty_stats(rf: RequestFactory):
    """Test KPI ribbon handles zero / empty stats gracefully without errors."""
    request = rf.get("/dashboard/task/")
    context = {
        "request": request,
        "kpi_stats": {},
    }
    rendered = render_to_string(
        "bw_components/task/kpi_ribbon.html", context, request=request
    )

    assert "Total Tasks" in rendered
    assert "In Progress" in rendered
    assert "Past Due" in rendered
    assert "Urgent" in rendered
    assert "Completed" in rendered
    assert "0" in rendered


@pytest.mark.unit
def test_task_filter_accordion_render_defaults(rf: RequestFactory):
    """Test task filter accordion rendering with clean request and default stats."""
    request = rf.get("/dashboard/task/")
    filterset = TaskFilter()
    kpi_stats = {
        "total_tasks": 100,
        "in_progress_tasks": 30,
        "past_due_tasks": 10,
        "urgent_tasks": 5,
        "completed_tasks": 55,
    }
    context = {
        "request": request,
        "filter_form": filterset.form,
        "filter_form_id": "tasksFilterForm",
        "kpi_stats": kpi_stats,
        "pagination_list_url_name": "dashboard:task:list",
    }
    rendered = render_to_string(
        "bw_components/task/filter_accordion.html", context, request=request
    )

    # Status tabs
    assert "All" in rendered
    assert "100" in rendered
    assert "In Progress" in rendered
    assert "30" in rendered
    assert "Past Due" in rendered
    assert "10" in rendered
    assert "Urgent" in rendered
    assert "5" in rendered
    assert "Completed" in rendered
    assert "55" in rendered

    # Trigger button & Accordion state
    assert "Filter Tasks" in rendered
    assert "toggleFilterAccordionBtn" in rendered
    assert "filterChevronIcon" in rendered
    assert "taskFilterPanel" in rendered
    assert "hidden" in rendered
    assert "tasksFilterForm" in rendered

    # Form fields
    assert "Task Title" in rendered
    assert "Hints" in rendered
    assert "Task Type" in rendered
    assert "Status" in rendered
    assert "Completion Status" in rendered
    assert "Job" in rendered
    assert "Client" in rendered
    assert "Managed By" in rendered
    assert "Bookkeeper" in rendered
    assert "Date Created" in rendered
    assert "Created Between" in rendered

    # Form actions
    assert "Apply Filters" in rendered
    assert "Cancel" in rendered
    assert "closeFilterAccordionBtn" in rendered


@pytest.mark.unit
def test_task_filter_accordion_render_active_filters(rf: RequestFactory):
    """Test task filter accordion with active filter query params."""
    request = rf.get("/dashboard/task/?status=in_progress&task_type=urgent")
    filterset = TaskFilter(data=request.GET)
    kpi_stats = {
        "total_tasks": 80,
        "in_progress_tasks": 20,
        "past_due_tasks": 5,
        "urgent_tasks": 8,
        "completed_tasks": 47,
    }
    context = {
        "request": request,
        "filter_form": filterset.form,
        "filter_form_id": "tasksFilterForm",
        "kpi_stats": kpi_stats,
        "pagination_list_url_name": "dashboard:task:list",
    }
    rendered = render_to_string(
        "bw_components/task/filter_accordion.html", context, request=request
    )

    # Active filter indicator !
    assert "!" in rendered
    # Clear and Reset buttons
    assert "Clear" in rendered
    assert "reset-filters-btn" in rendered
    assert "Reset Filters" in rendered
    # Panel is not hidden
    assert (
        'class=" p-4' in rendered
        or 'class="p-4' in rendered
        or "hidden" not in rendered.split('id="taskFilterPanel"')[1].split(">")[0]
    )


@pytest.mark.unit
def test_task_quick_peek_drawer_skeleton(rf: RequestFactory):
    """Test task quick peek drawer shell structure with loading spinner."""
    request = rf.get("/dashboard/task/")
    context = {"request": request}
    rendered = render_to_string(
        "bw_components/task/quick_peek_drawer.html", context, request=request
    )

    assert "taskQuickPeekBackdrop" in rendered
    assert "taskQuickPeekDrawer" in rendered
    assert "taskQuickPeekDrawerLabel" in rendered
    assert "Task Quick Peek" in rendered
    assert "closeTaskQuickPeekBtn" in rendered
    assert "taskQuickPeekDrawerBody" in rendered
    assert "animate-spin" in rendered


@pytest.mark.unit
def test_task_quick_peek_drawer_with_task(rf: RequestFactory):
    """Test task quick peek drawer when populated with a task object."""
    request = rf.get("/dashboard/task/")
    client = baker.make(ClientProxy, name="Acme Corporation")
    manager = baker.make(BWUser, first_name="Sarah", email="sarah@ledgerflare.com")
    job = baker.make(
        JobProxy,
        title="Q4 Financial Audit",
        client=client,
        managed_by=manager,
    )
    task = baker.make(
        TaskProxy,
        title="Reconcile PayPal transactions",
        hints="Check PayPal business account statement",
        additional_notes="<b>High priority reconciliation</b>",
        task_type=TaskTypeEnum.URGENT,
        status=TaskStatusEnum.IN_PROGRESS,
        job=job,
    )

    context = {
        "request": request,
        "task": task,
    }
    rendered = render_to_string(
        "bw_components/task/quick_peek_drawer.html", context, request=request
    )

    assert "Reconcile PayPal transactions" in rendered
    assert "Acme Corporation" in rendered
    assert "Q4 Financial Audit" in rendered
    assert "Sarah" in rendered or "sarah@ledgerflare.com" in rendered
    assert "Check PayPal business account statement" in rendered
    assert (
        "<b>High priority reconciliation</b>" in rendered
        or "High priority reconciliation" in rendered
    )
    assert "In progress" in rendered or "In Progress" in rendered
    assert "Urgent" in rendered
    assert "Edit Task" in rendered
    assert "View Job" in rendered
    assert f"/dashboard/task/update/{task.pk}" in rendered
    assert f"/dashboard/job/{job.pk}" in rendered


@pytest.mark.unit
def test_task_quick_peek_content_direct_render(rf: RequestFactory):
    """Test task quick peek content component directly."""
    request = rf.get("/dashboard/task/")
    client = baker.make(ClientProxy, name="Globex Industries")
    job = baker.make(JobProxy, title="Tax Prep 2026", client=client)
    task = baker.make(
        TaskProxy,
        title="File 1099 Forms",
        hints="Send copy to contractors",
        additional_notes="Ensure contractor SSN/EIN are verified.",
        task_type=TaskTypeEnum.RECURRING,
        status=TaskStatusEnum.COMPLETED,
        is_completed=True,
        job=job,
    )

    context = {
        "request": request,
        "task": task,
    }
    rendered = render_to_string(
        "bw_components/task/quick_peek_content.html", context, request=request
    )

    assert "File 1099 Forms" in rendered
    assert "Globex Industries" in rendered
    assert "Tax Prep 2026" in rendered
    assert "Send copy to contractors" in rendered
    assert "Ensure contractor SSN/EIN are verified." in rendered
    assert "Completed" in rendered
    assert "Recurring" in rendered
    assert "Timestamps & Audit" in rendered
    assert "Created Date:" in rendered
    assert "Edit Task" in rendered
    assert "View Job" in rendered


@pytest.mark.unit
def test_task_table_list_render(rf: RequestFactory):
    """Test task table_list.html component rendering with full task data."""
    request = rf.get("/dashboard/task/")
    manager = baker.make(BWUser, first_name="Alice", email="alice@example.com")
    client = baker.make(ClientProxy, name="Stark Industries")
    job = baker.make(JobProxy, title="FY2026 Audit", client=client, managed_by=manager)
    task1 = baker.make(
        TaskProxy,
        title="Verify invoices",
        hints="Check vendor portal for latest batch",
        task_type=TaskTypeEnum.ONE_TIME,
        status=TaskStatusEnum.IN_PROGRESS,
        is_completed=False,
        job=job,
    )
    task2 = baker.make(
        TaskProxy,
        title="Prepare tax forms",
        hints="",
        task_type=TaskTypeEnum.RECURRING,
        status=TaskStatusEnum.COMPLETED,
        is_completed=True,
        job=job,
    )

    context = {
        "request": request,
        "page_obj": [task1, task2],
        "object_list": [task1, task2],
        "app_label": "task",
        "header_title": "Tasks",
        "header_subtitle": "Manage tasks",
        "base_url_name": "dashboard:task",
        "actions_base_url": "dashboard:task",
        "actions_app_name": "task",
        "actions_items": "update,delete",
        "is_actions_menu_enabled": True,
        "is_show_create_btn": True,
        "is_checkbox_enabled": True,
        "is_show_created_at": True,
        "is_header_enabled": True,
        "is_footer_enabled": True,
        "total_records": 2,
    }

    rendered = render_to_string(
        "bw_components/task/table_list.html", context, request=request
    )

    # Headers
    assert "task_table" in rendered
    assert "task-table-list" in rendered
    assert "Task Title" in rendered
    assert "Client" in rendered
    assert "Job" in rendered
    assert "Managed By" in rendered
    assert "Type" in rendered
    assert "Status" in rendered
    assert "Created" in rendered
    assert "Actions" in rendered

    # Desktop Table Row checks
    assert "Verify invoices" in rendered
    assert "Check vendor portal for latest batch" in rendered
    assert "Stark Industries" in rendered
    assert "FY2026 Audit" in rendered
    assert "Alice" in rendered or "alice@example.com" in rendered
    assert "Prepare tax forms" in rendered
    assert "Done" in rendered
    assert "quick-peek-task-btn" in rendered

    # Mobile Cards Grid checks
    assert "taskGridView" in rendered
    assert f'data-task-pk="{task1.pk}"' in rendered
    assert f'data-task-pk="{task2.pk}"' in rendered


@pytest.mark.unit
def test_task_table_list_render_fallbacks(rf: RequestFactory):
    """Test task table_list.html handles tasks without client, job, manager or hints."""
    request = rf.get("/dashboard/task/")
    task_orphan = baker.make(
        TaskProxy,
        title="Unassigned standalone task",
        hints="",
        task_type=TaskTypeEnum.NO_TYPE,
        status=TaskStatusEnum.NOT_STARTED,
        job=None,
    )

    context = {
        "request": request,
        "page_obj": [task_orphan],
        "object_list": [task_orphan],
        "app_label": "task",
        "header_title": "Tasks",
        "header_subtitle": "Manage tasks",
        "base_url_name": "dashboard:task",
        "actions_base_url": "dashboard:task",
        "actions_app_name": "task",
        "total_records": 1,
    }

    rendered = render_to_string(
        "bw_components/task/table_list.html", context, request=request
    )

    assert "Unassigned standalone task" in rendered
    assert "No client" in rendered
    assert "No job" in rendered
    assert "Unassigned" in rendered


@pytest.mark.unit
def test_task_master_list_template_orchestration(rf: RequestFactory):
    """Test master task/list.html orchestrating all dashboard components."""
    request = rf.get("/dashboard/task/")
    manager = baker.make(BWUser, first_name="Bob", email="bob@example.com")
    job = baker.make(JobProxy, title="Bookkeeping 2026", managed_by=manager)
    task = baker.make(TaskProxy, title="Review ledger entries", job=job)
    filterset = TaskFilter()

    kpi_stats = {
        "total_tasks": 10,
        "in_progress_tasks": 3,
        "past_due_tasks": 1,
        "urgent_tasks": 2,
        "completed_tasks": 4,
    }

    context = {
        "request": request,
        "page_obj": [task],
        "object_list": [task],
        "kpi_stats": kpi_stats,
        "filter_form": filterset.form,
        "filter_form_id": "tasksFilterForm",
        "is_filters_enabled": True,
        "page_header": "Tasks",
        "subtitle": "Track accounting tasks",
        "is_show_create_btn": True,
        "app_label": "task",
        "actions_base_url": "dashboard:task",
        "base_url_name": "dashboard:task",
        "total_records": 10,
        "pagination_list_url_name": "dashboard:task:list",
    }

    rendered = render_to_string("task/list.html", context, request=request)

    # Master list container
    assert "taskListRoot" in rendered

    # Header component
    assert "Tasks" in rendered
    assert "Track accounting tasks" in rendered
    assert "taskViewTableBtn" in rendered
    assert "taskViewGridBtn" in rendered

    # KPI Ribbon component
    assert "Total Tasks" in rendered
    assert "In Progress" in rendered
    assert "Past Due" in rendered

    # Filter Accordion component
    assert "toggleFilterAccordionBtn" in rendered
    assert "tasksFilterForm" in rendered

    # Table List component
    assert "task-table-list" in rendered
    assert "Review ledger entries" in rendered
    assert "taskGridView" in rendered

    # Quick Peek Drawer component
    assert "taskQuickPeekDrawer" in rendered
    assert "taskQuickPeekBackdrop" in rendered


@pytest.mark.unit
def test_task_master_list_template_empty_state(rf: RequestFactory):
    """Test master task/list.html renders empty card when object_list is empty."""
    request = rf.get("/dashboard/task/")
    filterset = TaskFilter()
    kpi_stats = {"total_tasks": 0}

    context = {
        "request": request,
        "page_obj": [],
        "object_list": [],
        "kpi_stats": kpi_stats,
        "filter_form": filterset.form,
        "filter_form_id": "tasksFilterForm",
        "is_filters_enabled": True,
        "page_header": "Tasks",
        "app_label": "task",
        "actions_base_url": "dashboard:task",
        "base_url_name": "dashboard:task",
        "total_records": 0,
        "empty_label": "task",
    }

    rendered = render_to_string("task/list.html", context, request=request)

    assert "taskListRoot" in rendered
    assert (
        "No task" in rendered or "No tasks" in rendered or "empty" in rendered.lower()
    )
    assert "taskQuickPeekDrawer" in rendered
