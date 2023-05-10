import random
import requests
import pytest
from rest_framework.test import APIClient
from backend.models import User, Shop, Category, \
    Product, ProductInfo, Parameter, ProductParameter, \
    Contact, Order, OrderItem, ConfirmEmailToken
from model_bakery import baker


# @pytest.fixture
# def client():
#     return APIClient()


# @pytest.fixture
# def user():
#     return baker.make(User)
#
#
# @pytest.fixture
# def users():
#     return baker.make(User, 10)
#
#
# @pytest.fixture
# def shop():
#     return baker.make(Shop, 10)

# @pytest.mark.django_db
# def test_get_course(client, user):
#     response = client.get(f'/api/v1/courses/{course.id}/')
#     assert response.status_code == 200
#     assert response.data['id'] == course.id
#
#
# @pytest.mark.django_db
# def test_get_courses(client, courses):
#     response = client.get('/api/v1/courses/')
#     assert response.status_code == 200
#     assert len(courses) == len(response.data)
#
#
# @pytest.mark.django_db
# def test_get_filter_course_id(client, courses):
#     id_course = [item.id for item in courses][random.randint(0, 9)]
#     response = client.get(f'/api/v1/courses/?id={id_course}')
#     assert response.status_code == 200
#     assert response.data[0]['id'] == id_course
#
#
# @pytest.mark.django_db
# def test_get_filter_course_name(client, courses):
#     name_course = [item.name for item in courses][random.randint(0, 9)]
#     response = client.get(f'/api/v1/courses/', {'name': name_course})
#     assert response.status_code == 200
#     assert response.data[0]['name'] == name_course


@pytest.mark.django_db
def test_create_user(request):
    count_users_start = User.objects.count()
    response = requests.post('http://localhost/api/v1/user/register', data={"first_name": "Serge1",
                                                                             "last_name": "Rogch1",
                                                                             "email": "glich-gange@mail.ru",
                                                                             "password": "password",
                                                                             "company": "nelt11",
                                                                             "position": 1,
                                                                             "type": "shop",
                                                                             "username": "gggg"},  verify=False, timeout=30)
    assert response.status_code == 200
    assert User.objects.count() == count_users_start + 1
    request.config.cache.set('token_key', response.key)
    request.config.cache.set('email', response.email)
    request.config.cache.set('user_id', response.user_id)
    print(request.config.cache.get('token_key', None))

@pytest.mark.django_db
def test_confirm(request):
    response = requests.post(f'http://localhost/api/v1/user/register/confirm', data={'token': request.config.cache.get('token_key', None),
                                                                    'email': request.config.cache.get('email', None)},
                            format='json')
    assert response.status_code == 200

@pytest.mark.django_db
def test_login(request):
    response = requests.post(f'http://localhost/api/v1/user/login', data={"password": "password",
                                                        "email": "sergey_r.o@mail.ru"},
                           format='json')
    assert response.status_code == 200
    request.config.cache.set('token', response.Token)

@pytest.mark.django_db
def test_user_detail(request):
    response = requests.post(f'http://localhost/api/v1/user/details/{request.config.cache.get("user_id", None)}',
                           headers={'Content-Type': 'application/json',
                                    'Authorization': f'Token {request.config.cache.get("token")}'})
    assert response.status_code == 200
