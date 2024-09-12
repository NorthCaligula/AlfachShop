import json
import sys

import requests


def showGoods():
    res = requests.get("http://127.0.0.1:3000/api/types/All")
    jsonanswer = res.json()
    print(json.dumps(jsonanswer, indent=2))
    while True:
        answer_new = input("Выберите тип товара (лучше скопировать, проверьте на пробелы в конце):\n")
        if any(answer_new == item.get("type") for item in jsonanswer):
            break
        print("Не найден такой тип, попробуйте еще раз!")
    res = requests.get("http://127.0.0.1:3000/api/types/" + answer_new)
    jsonanswer = res.json()
    print(json.dumps(jsonanswer, indent=2))
    return True


def showOrders(id_cust):
    res = requests.get("http://127.0.0.1:3000/api/orders/" + str(id_cust))
    print(res)
    jsonanswer = res.json()
    if res.status_code == 200:
        print(json.dumps(jsonanswer, indent=2))
    else:
        print(jsonanswer)
        return False


def updateDataInCarts(id_cust, id_prod, quantity):
    res = requests.patch("http://127.0.0.1:3000/api/carts/" + id_cust, json={"id_products": id_prod, "count": quantity})
    print(res)
    print(res.json())
    return True


def createCart(id_cust, id_prod, quantity):
    res = requests.post("http://127.0.0.1:3000/api/carts/" + id_cust, json={"id_products": id_prod, "count": quantity})
    print(res)
    print(res.json())
    return True


def deleteDataInCarts(id_cust, id_prod):
    res = requests.delete("http://127.0.0.1:3000/api/carts/" + id_cust, json={"id_products": id_prod})
    print(res)
    print(res.json())
    return True


def getCartsById(id_cust):
    res = requests.get("http://127.0.0.1:3000/api/carts/" + str(id_cust))
    print(res)
    if res.status_code == 200:
        jsonanswer = res.json()
        print(json.dumps(jsonanswer, indent=2))
    else:
        print(res.json())
        return False


def workWithCarts(id_cust):
    # Потом на фронте автоматически будет выбираться метод отправки данных
    mode = input("Введите режим: 1-GET, 2-POST, 3-PATCH, 4-DELETE, Z - EXIT\n")
    if mode == "Z":
        return False
    if mode != "1":
        id_prod = input("Введите id товара\n")
    if mode == "2" or mode == "3":
        quantity = input("Введите количество\n")
        if not quantity.isdecimal():
            print("Введите коректное число в количестве\n")
            return True
        else:
            quantity = int(quantity)
    if mode == "1":
        return getCartsById(id_cust)
    if mode == "2":
        return createCart(id_cust, id_prod, quantity)
    if mode == "3":
        return updateDataInCarts(id_cust, id_prod, quantity)
    if mode == "4":
        return deleteDataInCarts(id_cust, id_prod)
    return False


def payForCarts(id_cust, paid=True):
    res = requests.patch("http://127.0.0.1:3000/api/orders/" + id_cust, json={"paid": paid})
    print(res)
    print(res.json())
    return True


def getWishList(id_cust):
    res = requests.get("http://127.0.0.1:3000/api/wish/" + str(id_cust))
    if res.status_code == 200:
        jsonanswer = res.json()
        print(json.dumps(jsonanswer, indent=2))
    else:
        print(res.json())
        return False


def workWishList(append, id_cust, id_prod):
    res = requests.patch("http://127.0.0.1:3000/api/wish/" + str(id_cust),
                         json={"append": append, "id_products": id_prod})
    print(res)
    print(res.json())


id_customer = "66bc6d31a0db858f341da690"
options = input("Выберите режим:\n1 - Просмотр ассортимента\n2 - Работа с корзиной\n3 - Оплатить корзину\n"
                    "4 - Работа с пользователем (Просто записать свой id, чтобы не вводить его каждый раз) "
                    "(Текущий Id - " + id_customer + ")\n5 - Просмотреть свои заказы и их статус\n6 - Работа с WishListом\n0 - Выход из кода\n")
while options != "0":
    if options.isdecimal(): options = int(options)
    else:
        print("Не число, программа будет завершена")
        exit()
    if options == 1:
        print(
            "Добрый день, на текущий момент вы находитесь на экране, на котором можно посмотреть все возможные товары")
        showGoods()
    elif options == 2:
        print(
            "Добрый день, на текущий момент вы находитесь на экране, на котором происходит взаимодействие с корзиной, посредством выбора метода")
        if id_customer == "NULL ID":
            print("Нет айди пользователя")
        else:
            workWithCarts(id_customer)
    elif options == 3:
        print("Добрый день, на текущий момент вы находитесь на экране, на котором можно оплатить корзину (Я потом "
              "придумаю отдельный сервис для оплаты, на текущий момент просто скинем флаг что вы оплатили)")
        if input('Чтобы оплатить заказ введите: "ОПЛАТИТЬ"\n') == "ОПЛАТИТЬ":
            try:
                payForCarts(id_customer)
            except:
                print("Ошибка транзакции")
    elif options == 4:
        id_customer = input("Введите свой id (Отсутсвуют проверки на наличие!!!!!)\n")
    elif options == 5:
        print("Добрый день, здесь вам отобразится ваша корзина")
        showOrders(id_customer)
    elif options == 6:
        mode = input("Просмотр/Добавить/Убрать 1/2/3\n")
        if mode == "1":
            getWishList(id_customer)
        elif mode == "2":
            prod = input("id товара\n")
            workWishList(True, id_customer, prod)
        elif mode == "3":
            prod = input("id товара\n")
            workWishList(False, id_customer, prod)
    options = input("Выберите режим:\n1 - Просмотр ассортимента\n2 - Работа с корзиной\n3 - Оплатить корзину\n"
                        "4 - Работа с пользователем (Просто записать свой id, чтобы не вводить его каждый раз) "
                        "(Текущий Id - " + id_customer + ")\n5 - Просмотреть свои заказы и их статус\n6 - Работа с WishListом\n0 - Выход из кода\n")
