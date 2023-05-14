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

@pytest.fixture
def client():
    return APIClient()



@pytest.mark.django_db
def test_user_admin():

    User.objects.create(first_name="Serge11",last_name="Rogch11",email="1sergey_r.o@mail.ru",password="password1",
            company="nelt111",position=2,type="admin",username="gggg",is_superuser=True,is_active=True)

    print(User.objects.count())
    admin = User.objects.get(email='1sergey_r.o@mail.ru')
    assert admin.is_superuser

@pytest.mark.django_db
def test_create_user(client, request):
    count_users_start = User.objects.count()
    #view = RegisterAccount.as_view()
    #client = RequestsClient()
    response = client.post("http://localhost/api/v1/user/register", json={"first_name": "Serge1",
                                                                             "last_name": "Rogch1",
                                                                             "email": "glich-gange@mail.ru",
                                                                             "password": "password",
                                                                             "company": "nelt11",
                                                                             "position": 1,
                                                                             "type": "shop",
                                                                             "username": "gggg"})
    print(response)
    print(response.json())
    print(response.json()['email'])
    #response = view(request)
    print(response.status_code)
    assert response.status_code == 200
    assert response.json()['email'] == 'glich-gange@mail.ru'
    assert User.objects.count() == count_users_start+1
    # assert User.objects.count() == count_users_start + 1
    # request.config.cache.set('token_key', response.key)
    # request.config.cache.set('email', response.email)
    # request.config.cache.set('user_id', response.user_id)
    # print(request.config.cache.get('token_key', None))

# @pytest.mark.django_db
# def test_create_user(request):
#     count_users_start = User.objects.count()
#     headers = {'Content-type': 'application/json'}
#     response = requests.post('http://localhost/api/v1/user/register', json={"first_name": "Serge1",
#                                                                              "last_name": "Rogch1",
#                                                                              "email": "glich-gange@mail.ru",
#                                                                              "password": "password",
#                                                                              "company": "nelt11",
#                                                                              "position": 1,
#                                                                              "type": "shop",
#                                                                              "username": "gggg"},  headers=headers)
#     print(response)
#     assert response.status_code == 200
#     assert User.objects.count() == count_users_start + 1
#     request.config.cache.set('token_key', response.key)
#     request.config.cache.set('email', response.email)
#     request.config.cache.set('user_id', response.user_id)
#     print(request.config.cache.get('token_key', None))
#
# @pytest.mark.django_db
# def test_confirm(request):
#     response = requests.post(f'http://localhost/api/v1/user/register/confirm', data={'token': request.config.cache.get('token_key', None),
#                                                                     'email': request.config.cache.get('email', None)},
#                             format='json')
#     assert response.status_code == 200
#
# @pytest.mark.django_db
# def test_login(request):
#     response = requests.post(f'http://localhost/api/v1/user/login', data={"password": "password",
#                                                         "email": "sergey_r.o@mail.ru"},
#                            format='json')
#     assert response.status_code == 200
#     request.config.cache.set('token', response.Token)
#
# @pytest.mark.django_db
# def test_user_detail(request):
#     response = requests.post(f'http://localhost/api/v1/user/details/{request.config.cache.get("user_id", None)}',
#                            headers={'Content-Type': 'application/json',
#                                     'Authorization': f'Token {request.config.cache.get("token")}'})
#     assert response.status_code == 200
