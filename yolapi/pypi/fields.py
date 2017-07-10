from django.db import models
from packaging.utils import canonicalize_name
from south.modelsinspector import add_introspection_rules


class CanonicalizedPackageNameField(models.CharField):
    """Normalize the name to the pypi normalized package style."""

    def _canonicalize_name(self, name):
        return canonicalize_name(name)

    def pre_save(self, model_instance, add):
        value = self._canonicalize_name(getattr(model_instance, self.attname))
        setattr(model_instance, self.attname, value)
        return super(CanonicalizedPackageNameField, self).pre_save(
            model_instance, add)

    def get_prep_value(self, value):
        value = self._canonicalize_name(value)
        return super(CanonicalizedPackageNameField, self).get_prep_value(value)


add_introspection_rules([], ["^pypi\.fields\.CanonicalizedPackageNameField"])
