from django.contrib.auth import get_user_model
from django.test import TestCase


class UserManagerTest(TestCase):
    def setUp(self) -> None:
        self.test_email = "test@email.com"
        self.test_password = "test1234"
        return super().setUp()

    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email=self.test_email, password=self.test_password
        )

        self.assertEqual(user.email, self.test_email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_supervisor)
