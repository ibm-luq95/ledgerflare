# -*- coding: utf-8 -*-#
"""
Placeholder template tags for future models (Bank Account, Transaction, Customer, Vendor)

These tags generate dummy data that can be easily replaced when the actual models are created.
"""
import random
from datetime import datetime, timedelta

from django import template
from django.utils import timezone

from core.utils import get_request_context

register = template.Library()


def _generate_dummy_bank_accounts(client, limit=3):
    """Generate dummy bank account data for placeholder"""
    banks = [
        {"name": "Chase", "prefix": "****"},
        {"name": "Bank of America", "prefix": "****"},
        {"name": "Wells Fargo", "prefix": "****"},
        {"name": "Citibank", "prefix": "****"},
        {"name": "US Bank", "prefix": "****"},
        {"name": "PNC Bank", "prefix": "****"},
        {"name": "Capital One", "prefix": "****"},
        {"name": "TD Bank", "prefix": "****"},
    ]
    
    account_types = ["Checking", "Savings", "Money Market", "Business Checking"]
    
    accounts = []
    for i in range(limit):
        bank = random.choice(banks)
        account_number = f"{bank['prefix']}{random.randint(1000, 9999)}"
        accounts.append({
            "id": i + 1,
            "client_id": client.pk,
            "account_name": f"{bank['name']} Business {random.choice(account_types)}",
            "account_number": account_number,
            "bank_name": bank["name"],
            "account_type": random.choice(account_types),
            "balance": round(random.uniform(1000, 100000), 2),
            "status": "active",
        })
    
    return accounts


def _generate_dummy_transactions(client, limit=10):
    """Generate dummy transaction data for placeholder"""
    descriptions_spent = [
        "Office Supplies", "Utilities Payment", "Software Subscription",
        "Insurance Premium", "Rent Payment", "Equipment Purchase",
        "Professional Services", "Marketing Expenses", "Travel Expenses",
        "Maintenance & Repairs", "Phone & Internet", "Cleaning Services"
    ]
    
    descriptions_receive = [
        "Client Payment - ABC Corp", "Service Revenue", "Consulting Fee",
        "Project Payment - XYZ", "Monthly Retainer", "Product Sale",
        "Refund Received", "Interest Income", "Client Payment - Tech Solutions"
    ]
    
    transactions = []
    base_date = timezone.now().date()
    
    for i in range(limit):
        is_receive = random.random() > 0.4  # 60% chance of income
        if is_receive:
            amount = round(random.uniform(500, 15000), 2)
            description = random.choice(descriptions_receive)
            transaction_type = "receive"
        else:
            amount = round(random.uniform(50, 3000), 2)
            description = random.choice(descriptions_spent)
            transaction_type = "spent"
        
        date = base_date - timedelta(days=random.randint(0, 30))
        
        transactions.append({
            "id": i + 1,
            "client_id": client.pk,
            "date": date,
            "description": description,
            "transaction_type": transaction_type,
            "amount": amount if is_receive else -amount,
            "bank_account": f"Chase ****{random.randint(1000, 9999)}",
            "status": "completed",
        })
    
    # Sort by date descending
    transactions.sort(key=lambda x: x["date"], reverse=True)
    return transactions


def _generate_dummy_chart_of_accounts(client):
    """Generate dummy chart of accounts summary data"""
    return [
        {
            "id": 1,
            "category": "Assets",
            "balance": round(random.uniform(30000, 80000), 2),
            "icon": "fa-wallet",
            "color": "blue",
        },
        {
            "id": 2,
            "category": "Liabilities",
            "balance": round(random.uniform(5000, 25000), 2),
            "icon": "fa-hand-holding-dollar",
            "color": "red",
        },
        {
            "id": 3,
            "category": "Equity",
            "balance": round(random.uniform(20000, 60000), 2),
            "icon": "fa-scale-balanced",
            "color": "green",
        },
        {
            "id": 4,
            "category": "Revenue",
            "balance": round(random.uniform(50000, 150000), 2),
            "icon": "fa-chart-line",
            "color": "teal",
        },
        {
            "id": 5,
            "category": "Expenses",
            "balance": round(random.uniform(15000, 50000), 2),
            "icon": "fa-money-bill-transfer",
            "color": "orange",
        },
    ]


def _generate_dummy_customers(client, limit=5):
    """Generate dummy customer data for placeholder"""
    cities = [
        ("New York", "NY", "USA"),
        ("Los Angeles", "CA", "USA"),
        ("Chicago", "IL", "USA"),
        ("Houston", "TX", "USA"),
        ("Phoenix", "AZ", "USA"),
        ("Philadelphia", "PA", "USA"),
        ("San Antonio", "TX", "USA"),
        ("San Diego", "CA", "USA"),
        ("Dallas", "TX", "USA"),
        ("Miami", "FL", "USA"),
    ]
    
    business_names = [
        "ABC Corporation", "Tech Solutions Inc", "Global Services LLC",
        "Innovative Industries", "Premier Partners", "Elite Enterprises",
        "Summit Solutions", "Apex Associates", "Prime Properties",
        "Visionary Ventures", "Strategic Systems", "Dynamic Designs"
    ]
    
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    
    customers = []
    used_names = set()
    
    for i in range(limit):
        business_name = random.choice(business_names)
        while business_name in used_names:
            business_name = random.choice(business_names)
        used_names.add(business_name)
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        city, state, country = random.choice(cities)
        
        customers.append({
            "id": i + 1,
            "client_id": client.pk,
            "business_name": business_name,
            "contact_person": f"{first_name} {last_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}@{business_name.split()[0].lower()}.com",
            "phone": f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 9999)} Business Ave",
            "address1": f"{random.randint(100, 9999)} Business Ave",
            "address2": f"Suite {random.randint(100, 999)}" if random.random() > 0.5 else "",
            "city": city,
            "state": state,
            "zip": f"{random.randint(10000, 99999)}",
            "country": country,
        })
    
    return customers


def _generate_dummy_vendors(client, limit=5):
    """Generate dummy vendor data for placeholder"""
    vendor_types = [
        ("Office Depot", "Sales Department", "office", True),
        ("Verizon Business", "Support Team", "telecom", True),
        ("AWS", "Billing Department", "technology", False),
        ("Local Cleaning Co", "Maria Garcia", "services", True),
        ("Software Licensing Inc", "License Team", "software", False),
        ("Utility Company", "Customer Service", "utilities", True),
        ("Insurance Partners", "Claims Department", "insurance", False),
        ("Marketing Agency", "Account Manager", "marketing", False),
        ("Legal Services LLC", "Paralegal Team", "legal", False),
        ("Equipment Rentals", "Rental Desk", "equipment", True),
    ]
    
    vendors = []
    used_vendors = set()
    
    for i in range(limit):
        business_name, contact_person, category, is_1099 = random.choice(vendor_types)
        while business_name in used_vendors:
            business_name, contact_person, category, is_1099 = random.choice(vendor_types)
        used_vendors.add(business_name)
        
        vendors.append({
            "id": i + 1,
            "client_id": client.pk,
            "business_name": business_name,
            "contact_person": contact_person,
            "email": f"contact@{business_name.split()[0].lower()}.com",
            "phone": f"(800) {random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "address": f"{random.randint(1000, 9999)} Vendor Street",
            "w9_details": "On file" if is_1099 else "Not required",
            "is_1099_vendor": is_1099,
        })
    
    return vendors


@register.inclusion_tag("bw_ui_components/elements/placeholders/bank_accounts.html", takes_context=True)
def placeholder_bank_accounts(context, *args, **kwargs) -> dict:
    """
    Display placeholder bank accounts for a client.
    
    Usage: {% placeholder_bank_accounts client=object limit=3 %}
    """
    context_data = get_request_context(context, kwargs)
    client = kwargs.get("client", None)
    limit = kwargs.get("limit", 3)
    
    if client:
        accounts = _generate_dummy_bank_accounts(client, limit)
    else:
        accounts = []
    
    kwargs.update({
        "accounts": accounts,
        "limit": limit,
    })
    
    return {**context_data, **kwargs}


@register.inclusion_tag("bw_ui_components/elements/placeholders/transactions.html", takes_context=True)
def placeholder_transactions(context, *args, **kwargs) -> dict:
    """
    Display placeholder transactions for a client.
    
    Usage: {% placeholder_transactions client=object limit=10 %}
    """
    context_data = get_request_context(context, kwargs)
    client = kwargs.get("client", None)
    limit = kwargs.get("limit", 10)
    
    if client:
        transactions = _generate_dummy_transactions(client, limit)
    else:
        transactions = []
    
    kwargs.update({
        "transactions": transactions,
        "limit": limit,
    })
    
    return {**context_data, **kwargs}


@register.inclusion_tag("bw_ui_components/elements/placeholders/chart_of_accounts_summary.html", takes_context=True)
def placeholder_chart_of_accounts_summary(context, *args, **kwargs) -> dict:
    """
    Display placeholder chart of accounts summary for a client.
    
    Usage: {% placeholder_chart_of_accounts_summary client=object %}
    """
    context_data = get_request_context(context, kwargs)
    client = kwargs.get("client", None)
    
    if client:
        accounts = _generate_dummy_chart_of_accounts(client)
    else:
        accounts = []
    
    kwargs.update({
        "accounts": accounts,
    })
    
    return {**context_data, **kwargs}


@register.inclusion_tag("bw_ui_components/elements/placeholders/customers.html", takes_context=True)
def placeholder_customers(context, *args, **kwargs) -> dict:
    """
    Display placeholder customers for a client.
    
    Usage: {% placeholder_customers client=object limit=5 %}
    """
    context_data = get_request_context(context, kwargs)
    client = kwargs.get("client", None)
    limit = kwargs.get("limit", 5)
    
    if client:
        customers = _generate_dummy_customers(client, limit)
    else:
        customers = []
    
    kwargs.update({
        "customers": customers,
        "limit": limit,
    })
    
    return {**context_data, **kwargs}


@register.inclusion_tag("bw_ui_components/elements/placeholders/vendors.html", takes_context=True)
def placeholder_vendors(context, *args, **kwargs) -> dict:
    """
    Display placeholder vendors for a client.
    
    Usage: {% placeholder_vendors client=object limit=5 %}
    """
    context_data = get_request_context(context, kwargs)
    client = kwargs.get("client", None)
    limit = kwargs.get("limit", 5)
    
    if client:
        vendors = _generate_dummy_vendors(client, limit)
    else:
        vendors = []
    
    kwargs.update({
        "vendors": vendors,
        "limit": limit,
    })
    
    return {**context_data, **kwargs}
