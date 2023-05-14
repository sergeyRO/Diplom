from distutils.util import strtobool

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from requests import get
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
from ujson import loads as load_json
from yaml import load as load_yaml, Loader

from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, \
    Contact, ConfirmEmailToken, User
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderItemSerializer, OrderSerializer, ContactSerializer, ParameterSerializer, ProductParameterSerializer

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from netology_pd_diplom.celery import app
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

@app.task()
def send_message(title, message, email):
    subject, from_email, to = title, settings.EMAIL_HOST_USER, email
    text_content = message
    html_content = f'{message}'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)

@app.task()
def do_import(file, request):
    return yaml_in_db(file, request)

def yaml_in_db(file, request):
    data = load_yaml(file, Loader=Loader)
    shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        category_object.shops.add(shop.id)
        category_object.save()
    ProductInfo.objects.filter(shop_id=shop.id).delete()
    for item in data['goods']:
        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

        product_info = ProductInfo.objects.create(product_id=product.id,
                                                  external_id=item['id'],
                                                  model=item['model'],
                                                  price=item['price'],
                                                  price_rrc=item['price_rrc'],
                                                  quantity=item['quantity'],
                                                  shop_id=shop.id)
        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(name=name)
            ProductParameter.objects.create(product_info_id=product_info.id,
                                            parameter_id=parameter_object.id,
                                            value=value)

def auth_user(is_authenticated):
    if not is_authenticated:
        return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)


class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):
        # return JsonResponse({'first_name': request.data['first_name'],
        #                      'last_name': request.data['last_name'],
        #                      'email': request.data['email']})
        # проверяем обязательные аргументы
        return JsonResponse({'first_name': {'first_name'}.issubset(request.data),
                             'last_name': {'last_name'}.issubset(request.data),
                             'email': {'email'}.issubset(request.data),
                             'password': {'password'}.issubset(request.data),
                             'company': {'company'}.issubset(request.data),
                             'position': {'position'}.issubset(request.data),
                             'type': {'type'}.issubset(request.data)
                             })
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', 'type'}.issubset(request.data):
            errors = {}

            # проверяем пароль на сложность

            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:

                # проверяем данные для уникальности имени пользователя
                # request.data._mutable = True
                # request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    #new_user_registered.send(sender=self.__class__, user_id=user.id)
                    send_message.delay(f"Password Reset Token for {token.user.email}", token.key, token.user.email)
                    return JsonResponse({'Status': True, 'key': token.key, 'email': token.user.email, 'user_id': user.id})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class AccountDetails(ModelViewSet):
    """
    Класс для работы данными пользователя
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    permission_classes = (IsAuthenticated,)

    # получить данные
    @action(detail=True, methods=["get"], url_path=r'user-details', )
    def retrieve(self, request, pk=None):
        instance = self.get_object()
        return Response(self.serializer_class(instance).data,
                        status=status.HTTP_200_OK)

    # Редактирование методом PATCH
    @action(detail=True, methods=["patch"], url_path=r'user-details', )
    def update(self, request, pk=None, *args, **kwargs):
        user = request.user
        if 'password' in request.data:
            errors = {}
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])
        # проверяем остальные данные
        user_serializer = self.serializer_class(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

# class AccountDetails(APIView):
#     """
#     Класс для работы данными пользователя
#     """
#
#     # получить данные
#     def get(self, request, *args, **kwargs):
#         auth_user(request.user.is_authenticated)
#
#         serializer = UserSerializer(request.user)
#         return Response(serializer.data)
#
#     # Редактирование методом POST
#     def post(self, request, *args, **kwargs):
#         auth_user(request.user.is_authenticated)
#         # проверяем обязательные аргументы
#
#         if 'password' in request.data:
#             errors = {}
#             # проверяем пароль на сложность
#             try:
#                 validate_password(request.data['password'])
#             except Exception as password_error:
#                 error_array = []
#                 # noinspection PyTypeChecker
#                 for item in password_error:
#                     error_array.append(item)
#                 return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
#             else:
#                 request.user.set_password(request.data['password'])
#
#         # проверяем остальные данные
#         user_serializer = UserSerializer(request.user, data=request.data, partial=True)
#         if user_serializer.is_valid():
#             user_serializer.save()
#             return JsonResponse({'Status': True})
#         else:
#             return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """
    # Авторизация методом POST
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Класс для поиска товаров
    """

    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дуликаты
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """

    # получить корзину
    def get(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # добавить позиции в корзину
    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                #items_dict = load_json(items_sting)
                items_dict = items_sting
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            objects_created += 1
                            #new_order_admin.send(sender=self.__class__)
                            send_message.delay(f"Обновление статуса заказа", 'Заказ сформирован', settings.EMAIL_ADMIN)
                    else:

                        JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # редактировать корзину
    def put(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        items_sting = request.data.get('items')
        if items_sting:
            try:
                #items_dict = load_json(items_sting)
                items_dict = items_sting
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)}, status=403)
            else:
                stream = get(url).content
                yaml_in_db(stream, request)
                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика
    """

    # получить текущий статус
    def get(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # изменить текущий статус
    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """
    def get(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class ContactView(APIView):
    """
    Класс для работы с контактами покупателей
    """

    # получить мои контакты
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # добавить новый контакт
    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить контакт
    def delete(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # редактировать контакт
    def put(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                print(contact)
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
    """

    # получить мои заказы
    def get(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        order = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        if {'id', 'contact'}.issubset(request.data):
            if str(request.data['id']).isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        #new_order.send(sender=self.__class__, user_id=request.user.id)
                        #send_email_order.delay(sender=self.__class__, user_id=request.user.id)
                        user = User.objects.get(id=request.user.id)
                        send_message.delay(f"Обновление статуса заказа", 'Заказ сформирован', user.email)
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderContactView(APIView):
    """
    Класс для размещения заказов пользователей с вводом контакта на доставку
    """

    # разместить заказ из корзины c вводом адреса доставки
    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        id_contact_order = Order.objects.filter(user_id=request.user.id, id=request.data['id']).first()

        contact = Contact.objects.filter(id=id_contact_order.contact_id, user_id=request.user.id).update(
            city=request.data['contact'][0]['city'],
            street=request.data['contact'][0]['street'],
            house=request.data['contact'][0]['house'],
            structure=request.data['contact'][0]['structure'],
            building=request.data['contact'][0]['building'],
            apartment=request.data['contact'][0]['apartment'],
            phone=request.data['contact'][0]['phone'])

        comment = f"Город доставки:{request.data['contact'][0]['city']}\n" \
                  f"Aдрес доставки:ул.{request.data['contact'][0]['street']},{request.data['contact'][0]['house']}\n" \
                  f"cтр.{request.data['contact'][0]['structure']}\n" \
                  f"cтр.{request.data['contact'][0]['building']}\n" \
                  f"апр.{request.data['contact'][0]['apartment']}\n" \
                  f"тел.{request.data['contact'][0]['phone']}"

        if str(request.data['id']).isdigit():
            try:
                is_updated = Order.objects.filter(
                    user_id=request.user.id, id=request.data['id']).update(
                    contact_id=id_contact_order.contact_id,
                    state='new')
            except IntegrityError as error:
                print(error)
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
            else:
                if is_updated:
                    #d = new_order_contact.send(sender=self.__class__, user_id=request.user.id, comment=comment)
                    #d = send_email_order_contact.delay(sender=self.__class__, user_id=request.user.id, comment=comment)
                    user = User.objects.get(id=request.user.id)
                    send_message.delay(f"Обновление статуса заказа", f'Заказ сформирован\n'
                                                                     f'Проверьте корректность адреса доставки ниже\n'
                                                                     f'{comment}', user.email)
                    return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ParameterView(APIView):
    '''
        Класс для просмотра и создания параметров товаров
    '''
    def get(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        param = Parameter.objects.all()

        return JsonResponse(list(param.values()), safe=False)

    def post(self, request, *args, **kwargs):
        auth_user(request.user.is_authenticated)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        id = Parameter.objects.create(name=request.data['name'])
        param = Parameter.objects.filter(id=id.id)
        if not param:
            return JsonResponse({'Status': False, 'Error': 'Create parameter not success'}, status=403)
        else:
            return JsonResponse({'id': id.id, 'desc': 'Create parameter success'})


class ImportProductView(APIView):

    def post(self, request):
        auth_user(request.user.is_authenticated)
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        file = request.FILES['file']
        #yaml_in_db(file, request)
        print(f"file=====>    {file}")
        print(f"request=====>    {request}")
        print(f"user=====>    {request.user.id}")
        do_import.delay(file, request)
        return JsonResponse({'Status': True})