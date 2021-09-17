"""Custom forms/fields that are inherited across multiple apps"""
from django import forms
from django.core.exceptions import ValidationError


class CustomChoiceField(forms.ChoiceField):
    """Overrides validation method to prevent validation against default list of choices. This
    enables custom validation to be performed in form.clean() method as the data is accessible
    via cleaned_data dict.

    IMPORTANT - default validation is removed using this class"""

    def validate(self, value) -> None:
        """Removes validation against initial choices list"""
        if value in self.empty_values and self.required:
            raise ValidationError(self.error_messages["required"], code="required")
        return True
