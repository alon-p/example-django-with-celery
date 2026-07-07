from django.urls import reverse

from app_example.tests.base import BaseAppExampleTestCase


class SendNotificationTestCase(BaseAppExampleTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.given_admin_exits()
        self.client.force_login(self.admin)
        self.path = reverse("app_example:notify")

    def tearDown(self):
        super().tearDown()

    def test_user_can_send_notification(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'OK'})


    def test_log_was_created_after_notification_sent(self):
        with self.assertLogs("app_example.services.notification_service", level="INFO") as logs:
            response = self.client.get(self.path)

        self.assertIn(
            'INFO:app_example.services.notification_service:Sending notification: hello celery task',
            logs.output[0],
        )



