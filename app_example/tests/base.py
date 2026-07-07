from django.contrib.auth import get_user_model
from django.test import TestCase


class BaseAppExampleTestCase(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @staticmethod
    def given_admin_exits(
            username: str = "admin",
            password: str = "123",
            email: str = "admin@test.test",
    ):
        UserModel = get_user_model()
        admin = UserModel.objects.create_superuser(
            username=username, password=password, email=email
        )
        return admin
