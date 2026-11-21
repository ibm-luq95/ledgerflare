# -*- coding: utf-8 -*-#
"""
File: set_site.py
Author: Ibrahim Luqman
Date: 5/13/24

Description: Initiate django site, django site framework for this project
"""
from colorama import Fore
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _

from core.management.mixins import CommandStdOutputMixin
from core.utils.grab_env_file import grab_env_file


class Command(BaseCommand, CommandStdOutputMixin):
    help = _("Initiate django site, django site framework")

    def add_arguments(self, parser):
        parser.add_argument(
            "-i",
            "--init-set-site",
            nargs="?",
            action="store",
            const=True,
            type=str,
            help=_("Set django site settings"),
            required=False,
        )
        parser.add_argument(
            "-c",
            "--clear-current-sites",
            nargs="?",
            action="store",
            const=True,
            type=str,
            help=_("Clear all current site for django"),
            required=False,
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # print(Fore.YELLOW)
                init_set_site = options.get("init_set_site")
                clear_current_sites = options.get("clear_current_sites")
                if clear_current_sites is True:
                    all_sites = Site.objects.all()

                    if all_sites:
                        confirm = input(
                            Fore.YELLOW
                            + _(f"Do you want to delete all sites {all_sites}? ")
                        )
                        if confirm == "Y" or confirm == "y":
                            self.stdout_output(
                                "warn",
                                _(f"Clear all exists sites ({all_sites.count()}) ..."),
                            )
                            for site in all_sites:
                                self.stdout_output("warn", _(f"Deleting - ({site.name})"))
                                site.delete()
                        else:
                            self.stdout_output("warn", _("Quiting..."))
                            return
                    else:
                        self.stdout_output("warn", _("No sites to delete"))
                # else:
                #     self.stdout_output("error", "You have to pass -i option!")

                if init_set_site is True:
                    config = grab_env_file()
                    site_domain = config("SITE_DOMAIN", cast=str)
                    site_name = config("SITE_NAME", cast=str)
                    self.stdout_output("warn", _(f"Site domain - {site_domain}"))
                    self.stdout_output("warn", _(f"Site name - {site_name}"))
                    site_data = {
                        "name": site_name,
                        "domain": site_domain,
                        "defaults": {"domain": site_domain},
                    }
                    site_obj, created = Site.objects.get_or_create(**site_data)
                    if created is True:
                        self.stdout_output(
                            "success", _(f"Site created successfully - {site_obj}")
                        )
                    else:
                        self.stdout_output("warn", _(f"Site already exists - {site_obj}"))

        except Exception as ex:
            self.stdout_output("error", str(ex))
