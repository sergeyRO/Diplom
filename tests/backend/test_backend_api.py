import json
import random
import requests
import pytest
from rest_framework.test import APIClient, APIRequestFactory, RequestsClient
from backend.models import User, Shop, Category, \
    Product, ProductInfo, Parameter, ProductParameter, \
    Contact, Order, OrderItem, ConfirmEmailToken
from model_bakery import baker
#from backend.views import RegisterAccount

#pytestmark = pytest.mark.django_db

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def user(client):
    new_user =dict()
    response = client.post("/api/v1/user/register", data={'first_name': 'Serge1', 'last_name': 'Rogch1',
                                                          'email': 'glich-gange@mail.ru', 'password': 'Qwe123@rteA',
                                                          'company': 'nelt11', 'position': 1, 'type': 'shop',
                                                          'username': 'gggg'}, format='json')
    new_user['token_key'] = response.json()['key']
    new_user['email'] = response.json()['email']
    new_user['user_id'] = response.json()['user_id']
    new_user['status_code'] = response.status_code
    new_user['password'] = 'Qwe123@rteA'
    return new_user

@pytest.fixture
def user_confirm(client, user):
    user = user
    response = client.post('/api/v1/user/register/confirm',
                           data={'token': user['token_key'],
                                 'email': user['email']},
                           format='json')
    return response

@pytest.fixture
def user_login(client, user, user_confirm):
    resp = user_confirm
    if resp.json()['Status'] == True:
        print(f"Pass ====> {user['password']}    email===>  {user['email']}")
        response = client.post('/api/v1/user/login', data={"password": user['password'],
                                                           "email": user['email']},
                                 format='json')
        response['user_id'] = user['user_id']
        print(f"RESP=====>   {response}   ----->>>    {response.json()}")
        return response

@pytest.mark.django_db(True)
class Test:

    def test_create_user(self, client, user):
        count_users_start = User.objects.count()
        response = client.post("/api/v1/user/register", data={'first_name': 'Serge2', 'last_name': 'Rogch2',
                                                              'email': 'sergey_r.o@mail.ru', 'password': '@Qwe123@rteA',
                                                              'company': 'nelt', 'position': 2, 'type': 'shop',
                                                              'username': 'gli'}, format='json')
        #assert request.config.cache.get('status_code', None) == 200, "Статус код"
        assert response.status_code == 200, "Статус код"
        assert User.objects.count() == count_users_start + 1, "Кол-во +1"
        # request.config.cache.set('token_key', response.json()['key'])
        # request.config.cache.set('email', response.json()['email'])
        # request.config.cache.set('user_id', response.json()['user_id'])

    def test_confirm(self, user_confirm):
        # print(f"TOKEN_KEY ===> {request.config.cache.get('token_key', None)}")
        print(f"USER2_count  =====>>    {User.objects.count()}")
        # response = client.post('/api/v1/user/register/confirm',
        #                        data={'token': request.config.cache.get('token_key', None),
        #                              'email': request.config.cache.get('email', None)},
        #                        format='json')
        response = user_confirm
        print(f"TEST2 ===> {response.json()['Status']} and {response.status_code}")
        assert response.status_code == 200
        assert response.json()['Status'] == True

    def test_login(self, user_login):
        response = user_login
        print(f"TOKEN ---> {response.json()}")
        assert response.status_code == 200
        assert response.json()['Status'] == True

    def test_user_detail(self, user_login):
        print(f"USER_LOGIN======>>>>     {user_login}")
        response = requests.get(f'/api/v1/user/details/{user_login["user_id"]}',
                               headers={'Content-Type': 'application/json',
                                        'Authorization': f'Token {user_login["Token"]}'})
        print(f"TEST_detail======>>>       {response}")
        assert response.status_code == 200

# @pytest.mark.django_db
# def test_user_detail(request):
#     response = requests.post(f'http://localhost/api/v1/user/details/{request.config.cache.get("user_id", None)}',
#                            headers={'Content-Type': 'application/json',
#                                     'Authorization': f'Token {request.config.cache.get("token")}'})
#     assert response.status_code == 200
