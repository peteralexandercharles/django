from django.db import models
from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import isolate_apps

from .models import (
    AbstractBase1,
    AbstractBase2,
    AbstractBase3,
    Child1,
    Child2,
    Child3,
    Child4,
    Child5,
    Child6,
    Child7,
    RelatedModel,
    RelationModel,
)


class ManagersRegressionTests(TestCase):
    def test_managers(self):
        a1 = Child1.objects.create(name="fred", data="a1")
        a2 = Child1.objects.create(name="barney", data="a2")
        b1 = Child2.objects.create(name="fred", data="b1", value=1)
        b2 = Child2.objects.create(name="barney", data="b2", value=42)
        c1 = Child3.objects.create(name="fred", data="c1", comment="yes")
        c2 = Child3.objects.create(name="barney", data="c2", comment="no")
        d1 = Child4.objects.create(name="fred", data="d1")
        d2 = Child4.objects.create(name="barney", data="d2")
        fred1 = Child5.objects.create(name="fred", comment="yes")
        Child5.objects.create(name="barney", comment="no")
        f1 = Child6.objects.create(name="fred", data="f1", value=42)
        f2 = Child6.objects.create(name="barney", data="f2", value=42)
        fred2 = Child7.objects.create(name="fred")
        barney = Child7.objects.create(name="barney")

        self.assertSequenceEqual(Child1.manager1.all(), [a1])
        self.assertSequenceEqual(Child1.manager2.all(), [a2])
        self.assertSequenceEqual(Child1._default_manager.all(), [a1])

        self.assertSequenceEqual(Child2._default_manager.all(), [b1])
        self.assertSequenceEqual(Child2.restricted.all(), [b2])

        self.assertSequenceEqual(Child3._default_manager.all(), [c1])
        self.assertSequenceEqual(Child3.manager1.all(), [c1])
        self.assertSequenceEqual(Child3.manager2.all(), [c2])

        # Since Child6 inherits from Child4, the corresponding rows from f1 and
        # f2 also appear here. This is the expected result.
        self.assertSequenceEqual(
            Child4._default_manager.order_by("data"),
            [d1, d2, f1.child4_ptr, f2.child4_ptr],
        )
        self.assertCountEqual(Child4.manager1.all(), [d1, f1.child4_ptr])
        self.assertCountEqual(Child5._default_manager.all(), [fred1])
        self.assertCountEqual(Child6._default_manager.all(), [f1, f2])
        self.assertSequenceEqual(
            Child7._default_manager.order_by("name"),
            [barney, fred2],
        )

    def test_abstract_manager(self):
        # Accessing the manager on an abstract model should
        # raise an attribute error with an appropriate message.
        # This error message isn't ideal, but if the model is abstract and
        # a lot of the class instantiation logic isn't invoked; if the
        # manager is implied, then we don't get a hook to install the
        # error-raising manager.
        msg = "type object 'AbstractBase3' has no attribute 'objects'"
        with self.assertRaisesMessage(AttributeError, msg):
            AbstractBase3.objects.all()

    def test_custom_abstract_manager(self):
        # Accessing the manager on an abstract model with a custom
        # manager should raise an attribute error with an appropriate
        # message.
        msg = "Manager isn't available; AbstractBase2 is abstract"
        with self.assertRaisesMessage(AttributeError, msg):
            AbstractBase2.restricted.all()

    def test_explicit_abstract_manager(self):
        # Accessing the manager on an abstract model with an explicit
        # manager should raise an attribute error with an appropriate
        # message.
        msg = "Manager isn't available; AbstractBase1 is abstract"
        with self.assertRaisesMessage(AttributeError, msg):
            AbstractBase1.objects.all()

    @override_settings(TEST_SWAPPABLE_MODEL="managers_regress.Parent")
    @isolate_apps("managers_regress")
    def test_swappable_manager(self):
        class SwappableModel(models.Model):
            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        # Accessing the manager on a swappable model should
        # raise an attribute error with a helpful message
        msg = (
            "Manager isn't available; 'managers_regress.SwappableModel' "
            "has been swapped for 'managers_regress.Parent'"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            SwappableModel.objects.all()

    @override_settings(TEST_SWAPPABLE_MODEL="managers_regress.Parent")
    @isolate_apps("managers_regress")
    def test_custom_swappable_manager(self):
        class SwappableModel(models.Model):
            stuff = models.Manager()

            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        # Accessing the manager on a swappable model with an
        # explicit manager should raise an attribute error with a
        # helpful message
        msg = (
            "Manager isn't available; 'managers_regress.SwappableModel' "
            "has been swapped for 'managers_regress.Parent'"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            SwappableModel.stuff.all()

    @override_settings(TEST_SWAPPABLE_MODEL="managers_regress.Parent")
    @isolate_apps("managers_regress")
    def test_explicit_swappable_manager(self):
        class SwappableModel(models.Model):
            objects = models.Manager()

            class Meta:
                swappable = "TEST_SWAPPABLE_MODEL"

        # Accessing the manager on a swappable model with an
        # explicit manager should raise an attribute error with a
        # helpful message
        msg = (
            "Manager isn't available; 'managers_regress.SwappableModel' "
            "has been swapped for 'managers_regress.Parent'"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            SwappableModel.objects.all()

    def test_regress_3871(self):
        related = RelatedModel.objects.create()

        relation = RelationModel()
        relation.fk = related
        relation.gfk = related
        relation.save()
        relation.m2m.add(related)

        t = Template(
            "{{ related.test_fk.all.0 }}{{ related.test_gfk.all.0 }}{{ related.test_m2m.all.0 }}"
        )

        self.assertEqual(
            t.render(Context({"related": related})),
            "".join([str(relation.pk)] * 3),
        )

    def test_field_can_be_called_exact(self):
        # Make sure related managers core filters don't include an
        # explicit `__exact` lookup that could be interpreted as a
        # reference to a foreign `exact` field. refs #23940.
        related = RelatedModel.objects.create(exact=False)
        relation = related.test_fk.create()
        self.assertEqual(related.test_fk.get(), relation)


@isolate_apps("managers_regress")
class TestManagerInheritance(SimpleTestCase):
    def test_implicit_inheritance(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            custom_manager = CustomManager()

            class Meta:
                abstract = True

        class PlainModel(models.Model):
            custom_manager = CustomManager()

        self.assertIsInstance(PlainModel._base_manager, models.Manager)
        self.assertIsInstance(PlainModel._default_manager, CustomManager)

        class ModelWithAbstractParent(AbstractModel):
            pass

        self.assertIsInstance(ModelWithAbstractParent._base_manager, models.Manager)
        self.assertIsInstance(ModelWithAbstractParent._default_manager, CustomManager)

        class ProxyModel(PlainModel):
            class Meta:
                proxy = True

        self.assertIsInstance(ProxyModel._base_manager, models.Manager)
        self.assertIsInstance(ProxyModel._default_manager, CustomManager)

        class MTIModel(PlainModel):
            pass

        self.assertIsInstance(MTIModel._base_manager, models.Manager)
        self.assertIsInstance(MTIModel._default_manager, CustomManager)

    def test_default_manager_inheritance(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            another_manager = models.Manager()
            custom_manager = CustomManager()

            class Meta:
                default_manager_name = "custom_manager"
                abstract = True

        class PlainModel(models.Model):
            another_manager = models.Manager()
            custom_manager = CustomManager()

            class Meta:
                default_manager_name = "custom_manager"

        self.assertIsInstance(PlainModel._default_manager, CustomManager)

        class ModelWithAbstractParent(AbstractModel):
            pass

        self.assertIsInstance(ModelWithAbstractParent._default_manager, CustomManager)

        class ProxyModel(PlainModel):
            class Meta:
                proxy = True

        self.assertIsInstance(ProxyModel._default_manager, CustomManager)

        class MTIModel(PlainModel):
            pass

        self.assertIsInstance(MTIModel._default_manager, CustomManager)

    def test_base_manager_inheritance(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            another_manager = models.Manager()
            custom_manager = CustomManager()

            class Meta:
                base_manager_name = "custom_manager"
                abstract = True

        class PlainModel(models.Model):
            another_manager = models.Manager()
            custom_manager = CustomManager()

            class Meta:
                base_manager_name = "custom_manager"

        self.assertIsInstance(PlainModel._base_manager, CustomManager)

        class ModelWithAbstractParent(AbstractModel):
            pass

        self.assertIsInstance(ModelWithAbstractParent._base_manager, CustomManager)

        class ProxyModel(PlainModel):
            class Meta:
                proxy = True

        self.assertIsInstance(ProxyModel._base_manager, CustomManager)

        class MTIModel(PlainModel):
            pass

        self.assertIsInstance(MTIModel._base_manager, CustomManager)

    def test_manager_no_duplicates(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            custom_manager = models.Manager()

            class Meta:
                abstract = True

        class TestModel(AbstractModel):
            custom_manager = CustomManager()

        self.assertEqual(TestModel._meta.managers, (TestModel.custom_manager,))
        self.assertEqual(
            TestModel._meta.managers_map, {"custom_manager": TestModel.custom_manager}
        )

    def test_manager_class_getitem(self):
        self.assertIs(models.Manager[Child1], models.Manager)
