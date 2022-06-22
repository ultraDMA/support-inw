import logging

import faker
from django.urls import reverse
from drfsite.settings import SIMPLE_JWT
from rest_framework import status
from rest_framework.test import APITestCase
from support.models import TicketComment, TicketInstance

logging.basicConfig(level='INFO')
logger = logging.getLogger('tests')
fake = faker.Faker()


class TestAPI(APITestCase):

    f_username = fake.first_name()
    f_email = fake.email()
    f_password = fake.password()

    def test_registration(self):    # 1
        """
        User registration test
        :return: None
        """
        url = reverse('user-list')
        data = {"username": f"{self.f_username}", "email": f"{self.f_email}", "password": f"{self.f_password}"}
        logger.warning(f'TEST_REGISTRATION: DATA: {data}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('email'), self.f_email)
        assert response.data.get('id')
        assert isinstance(response.data.get('id'), int)
        logger.warning(f'RESPONSE DATA = {response.data}')

    def test_token_creation(self) -> str:  # 2
        """
        Ensure we can obtain access and refresh tokens
        :return: str
        """
        self.test_registration()
        url = '/auth/jwt/create'
        data = {"username": f"{self.f_username}", "password": f"{self.f_password}"}
        response = self.client.post(url, data, format='json')
        logger.warning(f'RESPONSE: {response}\nDATA: {data}')
        access_token = response.data.get('access')
        refresh_token = response.data.get('refresh')
        logger.warning(f'access_token: {access_token}\nrefresh_token: {refresh_token}')
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        return access_token

    def test_create_ticket(self):
        """
        Ensure we can create a new Ticket instance object.
        """
        token_prefix = SIMPLE_JWT.get('AUTH_HEADER_TYPES')[0]   # in this case: Bearer
        authorization = f'{token_prefix} {self.test_token_creation()}'
        url = reverse('ticket-list')
        data = {'message': 'Lorem Ipsum'}
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=authorization)
        logger.warning(f'RESPONSE = {response}, URL = {url}')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TicketInstance.objects.count(), 1)
        self.assertEqual(TicketInstance.objects.get().message, 'Lorem Ipsum')

    def test_answer_on_ticket(self):
        """
        Ensure we can make answer on Ticket
        """
        token_prefix = SIMPLE_JWT.get('AUTH_HEADER_TYPES')[0]   # in this case: Bearer
        authorization = f'{token_prefix} {self.test_token_creation()}'
        # Here we create new Ticket instance
        url = reverse('ticket-list')
        data = {'message': 'Lorem Ipsum'}
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=authorization)
        logger.warning(f'RESPONSE = {response}, URL = {url}')
        # Here we create answer
        action = '/answer'
        url_to_instance = reverse('ticket-detail', kwargs={'pk': '1'}) + action
        data = {'message': 'Answer to Ticket'}
        logger.warning(url_to_instance)
        response = self.client.post(url_to_instance, data, format='json', HTTP_AUTHORIZATION=authorization)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TicketComment.objects.count(), 1)
        self.assertEqual(TicketComment.objects.get().message, 'Answer to Ticket')

    def test_registration_negative(self):
        """
        User without email can't register
        """
        url = reverse('user-list')
        data = {"username": f"{self.f_username}", "email": "", "password": f"{self.f_password}"}
        logger.warning(f'TEST_REGISTRATION: DATA: {data}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        logger.warning(f'RESPONSE DATA = {response.data}')

    def test_create_ticket_negative(self):
        """
        Ensure we can not create a new Ticket instance object without JWT token.
        """
        token_prefix = SIMPLE_JWT.get('AUTH_HEADER_TYPES')[0]   # in this case: Bearer
        authorization = f'{token_prefix} '
        url = reverse('ticket-list')
        data = {'message': 'Lorem Ipsum'}
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=authorization)
        logger.warning(f'RESPONSE = {response}, URL = {url}')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
