class MakeRequestObjectAvailableInFormMixin:
    """Passes request object into form to enable custom queries"""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class AddUserToFormMixin:
    """Adds user to form when validated - enables user to be stored on object creation"""

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
