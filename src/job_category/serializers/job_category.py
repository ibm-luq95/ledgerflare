# -*- coding: utf-8 -*-#
from rest_framework import serializers

from job_category.models import JobCategory


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ["id", "name"]
