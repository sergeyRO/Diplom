import pytest
from rest_framework.test import APIClient
from backend.models import User, Shop, Category, \
    Product, ProductInfo, Parameter, ProductParameter, \
    Contact, Order, OrderItem, ConfirmEmailToken

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
        response = client.post('/api/v1/user/login', data={"password": user['password'],
                                                           "email": user['email']},
                                 format='json')
        response.json()['user_id'] = user['user_id']
        response.json()['email'] = user['email']
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
        response = user_confirm
        assert response.status_code == 200
        assert response.json()['Status'] == True

    def test_login(self, user_login):
        response = user_login
        assert response.status_code == 200
        assert response.json()['Status'] == True

    def test_user_detail(self, client, user_login):
        user = user_login
        response = client.get(f'/api/v1/user/details/{user.json()["user_id"]}',
                               headers={'Content-Type': 'application/json',
                                        'Authorization': f'Token {user.json()["Token"]}'})
        assert response.status_code == 200
        assert response.json()['email'] == user.json()['email']

    def test_user_detail_update(self, client, user_login):
        user = user_login
        response = client.patch(f'/api/v1/user/details/{user.json()["user_id"]}',
                               headers={'Content-Type': 'application/json',
                                        'Authorization': f'Token {user.json()["Token"]}'},
                                data={'first_name':'Serge1322',
                                      'last_name':'Rogch1322',
                                      'company':'nelt13122'}, format='json')
        user_update = User.objects.filter(id=user.json()["user_id"]).first()
        assert response.status_code == 200
        assert response.json()['Status'] == True
        assert user_update.email == user.json()['email']