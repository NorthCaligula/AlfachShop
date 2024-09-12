from bson import ObjectId
from flask import Flask, request
from flask_restful import Api, Resource
import pymongo
from datetime import datetime
import pytz

app = Flask(__name__)
api = Api()

db_client = pymongo.MongoClient("mongodb://localhost:27017/")
current_db = db_client["AlfachShop"]
goodsCollections = current_db["goods"]
allOrdersCollections = current_db["orders"]
customersCollections = current_db["customers"]


def checkStorage(count_check, id_prod):
    # Функция, которая проверяет есть ли заявленное количество товара на складе
    res = goodsCollections.find_one({"_id": ObjectId(id_prod)})
    countInStock = res.get("count")
    if countInStock >= count_check:
        return True
    else:
        return countInStock - count_check


class GetGoodsByTypes(Resource):  # "/api/types/<string:type>"
    def get(self, type):
        # Здесь проверяем что отправленно, если None(All), то выводим типы
        if type == "All":
            pipeline = [
                {
                    "$group": {
                        "_id": "$type",
                        "avg_value_price": {"$avg": "$price"},
                        "avg_value_count": {"$sum": "$count"}
                    }
                }
            ]
            result = list(goodsCollections.aggregate(pipeline))
            response = []
            for i in range(len(result)):
                response.append({"type": result[i]["_id"],
                                 "count_prod": goodsCollections.count_documents({"type": result[i]["_id"]}),
                                 "avg_price": result[i]["avg_value_price"], "all_count": result[i]["avg_value_count"]})
            return response
        else:
            if goodsCollections.count_documents({"type": type}) > 0:
                o = list(goodsCollections.find({"type": type}))
                response = []
                for i in range(len(o)):
                    p = dict(o[i])
                    test2 = str(ObjectId(p["_id"]))
                    wish_count = len(p.get("_id_wish_customers"))
                    del p["_id"], p["_id_wish_customers"]
                    prokl = {"_id_product": test2, "wish_count": wish_count}
                    prokl.update(p)
                    response.append(prokl)
                print(response)
                return response, 200
            else:
                return "Передан некоректный тип товара", 400


class ChangeDataInCarts(Resource):  # "/api/carts/<string:id_cust>"
    def get(self, id_cust_get_carts):
        order = allOrdersCollections.find_one({"_id_customer": ObjectId(id_cust_get_carts), "paid": False})
        if not order: return "Не найдена корзина. Скорее всего, у вас нет в ней товаров. Если это не так, " \
                             "обратитесь к администратору", 404
        order_id = str(order["_id"])
        goods_list = order.get("_id_goods", [])
        cart_response = {"_id_orders": order_id, "goods": []}
        product_ids = {ObjectId(item.get("_id_one_goods")) for item in goods_list}
        for item in goods_list:
            cart_response["goods"].append({
                "count": item.get('count'),
                "id_product": str(item.get("_id_one_goods"))
            })
        products = list(goodsCollections.find({"_id": {"$in": list(product_ids)}}))
        product_attributes = {
            str(product["_id"]): {
                **{k: v for k, v in product.items() if k not in ["_id", "_id_wish_customers"]},
                "count_of_wish_customers": str(len(product.get('_id_wish_customers', [])))
            }
            for product in products
        }
        cart_response["product_attributes"] = product_attributes
        getCartsRes = [cart_response]
        return getCartsRes, 200

    def post(self, id_cust_post):
        data = request.get_json()
        id_products = data.get("id_products")
        count = data.get("count")
        if allOrdersCollections.count_documents({"_id_customer": ObjectId(id_cust_post), "paid": False}) == 0:
            allOrdersCollections.insert_one({"_id_customer": ObjectId(id_cust_post), "date_of_orders": 0,
                                             "paid": False, "delivered": False, "_id_goods": [{"count": count,
                                                                                               "_id_one_goods": ObjectId(
                                                                                                   id_products)}]})
            return 200
        else:
            return "Не тот метод, уже создана корзина, нужен PATCH", 400

    def patch(self, id_cust_patch):
        data = request.get_json()
        id_products = data.get("id_products")
        count = data.get("count")
        if not count.isdecimal():
            if int(count) == 0:
                return "Вы пытаетесь добавить ровно 0 объектов в корзину", 400
            return "Сервер не смог добавить ЭТО количество объектов", 400
        # Проверка в целом на наличие корзины, иначе POST
        if allOrdersCollections.count_documents({"_id_customer": ObjectId(id_cust_patch), "paid": False}) == 1:
            res = allOrdersCollections.find_one(
                {"_id_customer": ObjectId(id_cust_patch), "paid": False, "_id_goods._id_one_goods": ObjectId(id_products)})
            if res:
                # Если меняем кол-во товара
                allOrdersCollections.update_one(
                    {"_id_customer": ObjectId(id_cust_patch), "paid": False,
                     "_id_goods._id_one_goods": ObjectId(id_products)},
                    {"$set": {"_id_goods.$.count": count}})
                return "Обновленно кол-во", 200
            else:
                allOrdersCollections.find_one_and_update({"_id_customer": ObjectId(id_cust_patch), "paid": False},
                                                         {"$push": {
                                                             "_id_goods": {"count": count,
                                                                           "_id_one_goods": ObjectId(id_products)}}})
                return "Обновленно, добавлен новый объект", 200
        else:
            return "Или вы выбрали не тот метод, нужен POST, или надо проверить коллекции, создалось 2 корзины", 400

    def delete(self, id_cust_del):
        data = request.get_json()
        id_products = data.get("id_products")
        res1 = allOrdersCollections.find_one(
            {"_id_customer": ObjectId(id_cust_del), "paid": False, "_id_goods._id_one_goods": ObjectId(id_products)})
        if res1:
            allOrdersCollections.update_one({"_id_customer": ObjectId(id_cust_del), "paid": False},
                                            {"$pull": {"_id_goods": {"_id_one_goods": ObjectId(id_products)}}})
        else:
            return "Нет этого объекта у пользователя в корзине", 410
        res2 = allOrdersCollections.find_one({"_id_customer": ObjectId(id_cust_del), "paid": False})
        if res2 and len(res2['_id_goods']) == 0:
            allOrdersCollections.delete_one({"_id_customer": ObjectId(id_cust_del), "paid": False})
            return "Документ удален, так как последний товар был удален.", 200
        else:
            return "Товар успешно удален из массива.", 200


class PayForCarts(Resource):  # "/api/orders/<string:id_cust>"
    def patch(self, id_cust):
        data = request.get_json()
        paid = data.get("paid")
        if allOrdersCollections.count_documents({"_id_customer": ObjectId(id_cust), "paid": False}) == 1:
            # Берем за константу, то, что оплата проходит 100%. Поэтоум необходимо добавить функции, который будут
            # сначала проверять товар на наличие а потом вычитать его со склада
            res = dict(list(allOrdersCollections.find({"_id_customer": ObjectId(id_cust), "paid": False}))[0]).get(
                "_id_goods")
            serso = {}
            errors = {}
            for i in range(len(res)):
                serso[i] = res[i]
            for i in range(len(res)):
                gett = checkStorage(int(serso[i].get('count')), str(serso[i].get('_id_one_goods')))
                if not gett:
                    errors[i] = {"count_dif": gett, "_id_prod": serso[i].get('_id_one_goods')}
            if len(errors) != 0:
                return errors, 400
            # Начинаем вычитание, по хорошему бы написать транзакции, но я пока не понял как
            for i in range(len(serso)):
                goodsCollections.update_one({"_id": ObjectId(serso[i].get('_id_one_goods'))},
                                            {"$inc": {"count": -(int(serso[i].get('count')))}})
                timenow = int(datetime.now(pytz.utc).timestamp())
                allOrdersCollections.update_one({"_id_customer": ObjectId(id_cust), "paid": False},
                                                {"$set": {"paid": paid, "date_of_orders": timenow}})
            return "Оплачено, ждите уведомление о возможности забрать заказ", 200
        else:
            return "No carts", 404


class WishListReturn(Resource):  # "/api/admin/wish/<string:id_prod>"
    def get(self, id_prod):
        if id_prod.isdecimal():
            res = list(goodsCollections.find({"_id_wish_customers": {"$ne": []}}))
            response = []
            wish_id = {}
            for i in range(len(res)):
                p = res[i]
                qwe = p.get("_id_wish_customers")
                for j in range(len(qwe)):
                    wish_id[j] = str(qwe[j])
                response.append({"_id_products": str(p.get("_id")), "_id_wish": dict(wish_id)})
            return response
        else:
            res = dict(goodsCollections.find_one({"_id": ObjectId(id_prod)}))
            qwe = res.get("_id_wish_customers")
            wish_id = {}
            for k in range(len(qwe)):
                wish_id[k] = str(qwe[k])
            response = {"_id_products": str(res.get("_id")), "_id_wish": wish_id}
            return response


class GetCustomersOrders(Resource):  # "/api/orders/<string:id_cust>"
    def get(self, id_cust):
        if allOrdersCollections.count_documents({"_id_customer": ObjectId(id_cust), "paid": True}) > 0:
            main_id = []
            res = list(allOrdersCollections.find({"_id_customer": ObjectId(id_cust), "paid": True},
                                                 {"_id": 1, "_id_customer": 1, "_id_goods": 1}))
            for p in res:
                order_id = str(ObjectId(p["_id"]))
                goods = [{"count": item.get('count'), "id_product": str(item.get("_id_one_goods"))} for item in
                         p["_id_goods"]]
                order_data = {"_id_orders": order_id, "goods": goods}
                del p["_id"], p["_id_customer"], p["_id_goods"]
                order_data.update(p)
                main_id.append(order_data)
            return main_id, 200
        else:
            return "There are no orders, including just paid ones", 404


class GetFullOrders(Resource):  # "/api/admin/orders"
    def get(self):
        data = request.get_json()
        id_order = data.get("id_order")
        paid = data.get("paid")
        if id_order.isdecimal():
            # Если 0
            if paid:
                res = list(allOrdersCollections.find({"paid": paid}))
            else:
                res = list(allOrdersCollections.find())
            responses = []
            for i in range(len(res)):
                p = res[i]
                main_id = {"_id_orders": str(p.get("_id"))}
                test = [{"count": item.get("count"), "_id_one_goods": str(item.get("_id_one_goods"))} for item in
                        p.get("_id_goods")]
                del p["_id"], p["_id_customer"], p["_id_goods"]
                main_id.update(p)
                main_id.update({"id_goods": test})
                responses.append(main_id)
            return responses, 200
        else:
            # Если передан id
            if paid:
                res = list(allOrdersCollections.find({"_id": ObjectId(id_order), "paid": paid}))[0]
            else:
                res = list(allOrdersCollections.find({"_id": ObjectId(id_order)}))[0]
            main_id = [{"_id_orders": str(res.get("_id")), "_id_customer": str(res.get("_id_customer"))}]
            test = [{"count": item.get("count"), "_id_one_goods": str(item.get("_id_one_goods"))} for item in
                    res.get("_id_goods")]
            del res["_id"], res["_id_customer"], res["_id_goods"]
            main_id[0].update(res)
            main_id.append(test)
            return main_id


class WishList(Resource):  # "/api/wish/<string:id_customers>"
    def get(self, id_cust_get):
        customer = customersCollections.find_one({"_id": ObjectId(id_cust_get), "_id_wish_goods": {"$ne": []}})
        if customer:
            wl = customer.get("_id_wish_goods", [])
            dataInWishList = [str(item) for item in wl]
            return dataInWishList, 200
        else:
            return "Нет товаров в желаемом", 400

    def patch(self, id_cust_patch):
        data = request.get_json()
        append = data.get("append")
        id_prod = data.get("id_products")
        res1 = customersCollections.find_one({"_id": ObjectId(id_cust_patch), "_id_wish_goods": ObjectId(id_prod)})
        res2 = goodsCollections.find_one({"_id": ObjectId(id_prod), "_id_wish_customers": ObjectId(id_cust_patch)})
        if res1 and res2 and append:
            return "Already in the wishlist", 400
        if not res1 and not res2 and not append:
            return "Already not in the wishlist", 400
        if append:
            if not res1:
                customersCollections.update_one({"_id": ObjectId(id_cust_patch)},
                                                {"$push": {"_id_wish_goods": ObjectId(id_prod)}})
            if not res2:
                goodsCollections.update_one({"_id": ObjectId(id_prod)},
                                            {"$push": {"_id_wish_customers": ObjectId(id_cust_patch)}})
            return "Updated", 200
        else:
            if res1:
                customersCollections.update_one({"_id": ObjectId(id_cust_patch)},
                                                {"$pull": {"_id_wish_goods": ObjectId(id_prod)}})
            if res2:
                goodsCollections.update_one({"_id": ObjectId(id_prod)},
                                            {"$pull": {"_id_wish_customers": ObjectId(id_cust_patch)}})
            return "Updated", 200


class WorkWithGoods(Resource):  # "/api/admin/goods"
    def post(self):
        data = request.get_json()
        name = data.get("name")
        needtype = {"type": str, "name": str, "country": str, "price": int, "count": int}
        for i in range(len(needtype)):
            print(list(needtype)[i])
            y = data.get(list(needtype)[i], None)
            print(y)
            if y is None:
                return "No attribute: " + str(list(needtype)[i]), 422
            if not (isinstance(y, needtype.get(list(needtype)[i]))):
                return "No, attribute: " + str(list(needtype)[i]) + " with value: " + str(y) + " but need type: " + str(
                    needtype.get(list(needtype)[i])), 400
        data.update({"_id_wish_customers": []})
        res = goodsCollections.insert_one(data)
        if res:
            return "Add: " + str(name), 200
        else:
            return "NOT ALL OK", 400

    def delete(self):
        data = request.get_json()
        id_prod = data.get("id_products")
        print(id_prod)
        res = goodsCollections.find_one({"_id": ObjectId(id_prod)})
        if res:
            goodsCollections.delete_one({"_id": ObjectId(id_prod)})
            return "ALL OK", 200
        else:
            return "No Data", 410

    def patch(self):
        data = request.get_json()
        id_prod = data.get("id_products")
        count = data.get("count")
        if not isinstance(count, int): return "Not int in 'Count'", 422
        if goodsCollections.find_one({"_id": ObjectId(id_prod)}):
            goodsCollections.update_one({"_id": ObjectId(id_prod)}, {"$set": {"count": count}})
            return ("Update count to " + str(count)), 200
        else:
            return ("Not found product with id" + str(id_prod)), 404


api.add_resource(ChangeDataInCarts, "/api/carts/<string:id_cust>")
api.add_resource(PayForCarts, "/api/orders/<string:id_cust>")
api.add_resource(GetGoodsByTypes, "/api/types/<string:type>")
api.add_resource(GetCustomersOrders, "/api/orders/<string:id_cust>")
api.add_resource(GetFullOrders, "/api/admin/orders")
api.add_resource(WishList, "/api/wish/<string:id_cust>")
api.add_resource(WorkWithGoods, "/api/admin/goods")
api.add_resource(WishListReturn, "/api/admin/wish/<string:id_prod>")
api.init_app(app)

if __name__ == "__main__":
    app.run(debug=True, port=3000, host="127.0.0.1")
