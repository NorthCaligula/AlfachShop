import json
import sys

import requests


# Администратор
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


def editCount(id_prod_c, count_c):
    res = requests.patch("http://127.0.0.1:3000/api/admin/goods", json={"id_products": id_prod_c, "count": count_c})
    print(res)
    print(res.json())


def deleteProd(id_prod_d):
    res = requests.delete("http://127.0.0.1:3000/api/admin/goods", json={"id_products": id_prod_d})
    print(res)
    print(res.json())


def addProd(jayson):
    res = requests.post("http://127.0.0.1:3000/api/admin/goods", json=jayson)
    print(res)
    print(res.json())


def getDataOrders(id_order_d, paid_d):
    res = requests.get("http://127.0.0.1:3000/api/admin/orders", json={"id_order": id_order_d, "paid": paid_d})
    print(res)
    jsonanswer = res.json()
    print(json.dumps(jsonanswer, indent=2))


def getWishProd(id_prod_g):
    res = requests.get("http://127.0.0.1:3000/api/admin/wish/" + str(id_prod_g))
    print(res)
    jsonanswer = res.json()
    print(json.dumps(jsonanswer, indent=2))


mode = input(
    "Введите режим работы, где: \n1 - Данные о желаемом товара\n2 - Полученние ассортимента\n3 - Редактирование"
    " кол-ва отображаемого товара\n4 - Удаление товара\n5 - Добавление товара\n6 - Данные о заказах\nZ - Exit\n")
while mode != "Z":
    if mode.isdecimal():
        mode = int(mode)
    else:
        print("Не число, программа будет завершена")
        sys.exit()
    if mode == 1:
        print("Данные о вишлисте товара")
        data_o = input("Введите id товара, или напишите '0' если нужны данные о всех товарах\n")
        getWishProd(data_o)
    if mode == 2:
        print("Получить ассортимент")
        showGoods()
    if mode == 3:
        print("Редактирование колчества")
        id_prod_t = input("Айди товара\n")
        count_t = int(input("Новое количество\n"))
        editCount(id_prod_t, count_t)
    if mode == 4:
        print("Удаление товара из базы данных")
        id_prod_f = input("Айди товара\n")
        deleteProd(id_prod_f)
    if mode == 5:
        print("Добавление товара в базу")
        data = {}
        data.update({"type": input("Введите тип товара\n")})
        data.update({"name": input("Введите название(name) товара\n")})
        data.update({"country": input("Введите страну производитель для товара\n")})
        data.update({"price": int(input("Введите цену для товара\n"))})
        data.update({"count": int(input("Введите сколько товара на складе\n"))})
        addProd(data)
    if mode == 6:
        print("Полученние данных о заказе(ах)")
        id_order = input("Введите id нужного заказа, или '0' если нужны все\n")
        if id_order == "0": paid_s = input("Только оплаченные? Y/N\n") == "Y"
        else: paid_s = False
        getDataOrders(id_order, paid_s)
    mode = input(
        "Введите режим работы, где: \n1 - Данные о желаемом товара\n2 - Полученние ассортимента\n3 - Редактирование"
        " кол-ва отображаемого товара\n4 - Удаление товара\n5 - Добавление товара\n6 - Данные о заказах\nZ - Exit\n")
