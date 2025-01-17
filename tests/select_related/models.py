"""
Tests for select_related()

``select_related()`` follows all relationships and pre-caches any foreign key
values so that complex trees can be fetched in a single query. However, this
isn't always a good idea, so the ``depth`` argument control how many "levels"
the select-related behavior will traverse.
"""

from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Who remembers high school biology?


class Domain(models.Model):
    name = models.CharField(max_length=50)


class Kingdom(models.Model):
    name = models.CharField(max_length=50)
    domain = models.ForeignKey(Domain, models.CASCADE)


class Phylum(models.Model):
    name = models.CharField(max_length=50)
    kingdom = models.ForeignKey(Kingdom, models.CASCADE)


class Klass(models.Model):
    name = models.CharField(max_length=50)
    phylum = models.ForeignKey(Phylum, models.CASCADE)


class Order(models.Model):
    name = models.CharField(max_length=50)
    klass = models.ForeignKey(Klass, models.CASCADE)


class Family(models.Model):
    name = models.CharField(max_length=50)
    order = models.ForeignKey(Order, models.CASCADE)


class Genus(models.Model):
    name = models.CharField(max_length=50)
    family = models.ForeignKey(Family, models.CASCADE)


class Species(models.Model):
    name = models.CharField(max_length=50)
    genus = models.ForeignKey(Genus, models.CASCADE)


# and we'll invent a new thing so we have a model with two foreign keys


class HybridSpecies(models.Model):
    name = models.CharField(max_length=50)
    parent_1 = models.ForeignKey(Species, models.CASCADE, related_name="child_1")
    parent_2 = models.ForeignKey(Species, models.CASCADE, related_name="child_2")


class Topping(models.Model):
    name = models.CharField(max_length=30)


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping)


class TaggedItem(models.Model):
    tag = models.CharField(max_length=30)

    content_type = models.ForeignKey(
        ContentType, models.CASCADE, related_name="select_related_tagged_items"
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")


class Bookmark(models.Model):
    url = models.URLField()
    tags = GenericRelation(TaggedItem)
