from django.contrib.auth.mixins import LoginRequiredMixin


class LimitResultsToUserMixin(LoginRequiredMixin):
    """Override queryset to only show results for current user. This prevents user from
    accessing objects they do not own."""

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
