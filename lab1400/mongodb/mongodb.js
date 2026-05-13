db = db.getSiblingDB("shop_mongo");

// перезапуск
db.users.drop();
db.products.drop();
db.orders.drop();
//

print("1. Создание коллекций и вставка данных");

db.users.insertMany([
    {
        _id: 1,
        email: "alice@example.com",
        full_name: "Alice Smith",
        created_at: new Date(),
        address: {
            city: "Moscow",
            street: "Tverskaya",
            zipcode: "101000"
        }
    },
    {
        _id: 2,
        email: "bob@example.com",
        full_name: "Bob Johnson",
        created_at: new Date(),
        address: {
            city: "Saint Petersburg",
            street: "Nevsky",
            zipcode: "191186"
        }
    },
    {
        _id: 3,
        email: "carol@example.com",
        full_name: "Carol White",
        created_at: new Date(),
        address: {
            city: "Kazan",
            street: "Baumana",
            zipcode: "420111"
        }
    }
]);
print("Пользователи вставлены: " + db.users.countDocuments());

db.products.insertMany([
    {
        _id: 1,
        name: "Ноутбук",
        category: "Электроника",
        price: 75000,
        stock_quantity: 10,
        specs: { brand: "Lenovo", ram: "16GB", storage: "512GB SSD" }
    },
    {
        _id: 2,
        name: "Мышь",
        category: "Электроника",
        price: 1500,
        stock_quantity: 50
    },
    {
        _id: 3,
        name: "Книга SQL",
        category: "Книги",
        price: 2500,
        stock_quantity: 30,
        specs: { author: "Дмитрий К.", pages: 450 }
    },
    {
        _id: 4,
        name: "Клавиатура",
        category: "Электроника",
        price: 4500,
        stock_quantity: 20,
        specs: { type: "mechanical", switch: "Cherry MX Blue" }
    },
    {
        _id: 5,
        name: "Ручка шариковая",
        category: "Канцелярия",
        price: 100,
        stock_quantity: 200
    }
]);
print("Товары вставлены: " + db.products.countDocuments());

db.orders.insertMany([
    {
        _id: 1,
        user_id: 1,
        order_date: new Date("2026-04-15"),
        status: "completed",
        items: [
            { product_id: 1, quantity: 1, price: 75000 },
            { product_id: 2, quantity: 2, price: 1500 }
        ]
    },
    {
        _id: 2,
        user_id: 2,
        order_date: new Date("2026-04-20"),
        status: "completed",
        items: [
            { product_id: 3, quantity: 2, price: 2500 },
            { product_id: 4, quantity: 1, price: 4500 }
        ]
    },
    {
        _id: 3,
        user_id: 3,
        order_date: new Date("2026-04-28"),
        status: "pending",
        items: [
            { product_id: 5, quantity: 10, price: 100 },
            { product_id: 2, quantity: 1, price: 1500 }
        ]
    }
]);
print("Заказы вставлены: " + db.orders.countDocuments());



print("\n2. READ: Заказы Alice с итоговой суммой");
db.orders.aggregate([
    {
        $lookup: {
            from: "users",
            localField: "user_id",
            foreignField: "_id",
            as: "user_info"
        }
    },
    { $unwind: "$user_info" },
    { $match: { "user_info.email": "alice@example.com" } },
    {
        $addFields: {
            total_amount: {
                $sum: {
                    $map: {
                        input: "$items",
                        as: "item",
                        in: { $multiply: ["$$item.quantity", "$$item.price"] }
                    }
                }
            }
        }
    },
    { $project: { _id: 1, user_id: 1, status: 1, total_amount: 1, "user_info.full_name": 1 } }
]).pretty();



print("\n 3. UPDATE: Добавить скидку 10% на заказы дороже 80000 ");

db.orders.aggregate([
    {
        $addFields: {
            total_amount: {
                $sum: {
                    $map: {
                        input: "$items",
                        as: "i",
                        in: { $multiply: ["$$i.quantity", "$$i.price"] }
                    }
                }
            }
        }
    }
]).forEach(doc => {
    db.orders.updateOne(
        { _id: doc._id },
        { $set: { total_amount: doc.total_amount } }
    );
});

db.orders.updateMany(
    { total_amount: { $gt: 80000 } },
    { $set: { discount: 10 } }
);

print("Заказы со скидкой:");
db.orders.find({ discount: { $exists: true } }, { _id: 1, total_amount: 1, discount: 1 }).pretty();



print("\n4. DELETE: Удалить отменённые заказы старше 30 дней");
const thirtyDaysAgo = new Date();
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

const deleteResult = db.orders.deleteMany({
    status: "cancelled",
    order_date: { $lt: thirtyDaysAgo }
});
print("Удалено заказов: " + deleteResult.deletedCount);



print("\n5. Агрегация: категории, выручка, средняя цена");
db.orders.aggregate([
    { $unwind: "$items" },
    {
        $lookup: {
            from: "products",
            localField: "items.product_id",
            foreignField: "_id",
            as: "product_info"
        }
    },
    { $unwind: "$product_info" },
    {
        $group: {
            _id: "$product_info.category",
            total_quantity: { $sum: "$items.quantity" },
            total_revenue: {
                $sum: { $multiply: ["$items.quantity", "$items.price"] }
            },
            avg_price: { $avg: "$items.price" }
        }
    },
    { $sort: { total_revenue: -1 } },
    {
        $project: {
            category: "$_id",
            total_quantity: 1,
            total_revenue: 1,
            avg_price: { $round: ["$avg_price", 2] },
            _id: 0
        }
    }
]).pretty();



print("\n6. Топ 3 пользователей по сумме заказов");
db.orders.aggregate([
    { $unwind: "$items" },
    {
        $group: {
            _id: "$user_id",
            total_spent: {
                $sum: { $multiply: ["$items.quantity", "$items.price"] }
            }
        }
    },
    { $sort: { total_spent: -1 } },
    { $limit: 3 },
    {
        $lookup: {
            from: "users",
            localField: "_id",
            foreignField: "_id",
            as: "user"
        }
    },
    { $unwind: "$user" },
    {
        $project: {
            full_name: "$user.full_name",
            total_spent: 1,
            _id: 0
        }
    }
]).pretty();



print("\n7. Все заказы с пользователем и итоговой суммой");
db.orders.aggregate([
    {
        $addFields: {
            total_amount: {
                $sum: {
                    $map: {
                        input: "$items",
                        as: "i",
                        in: { $multiply: ["$$i.quantity", "$$i.price"] }
                    }
                }
            }
        }
    },
    {
        $lookup: {
            from: "users",
            localField: "user_id",
            foreignField: "_id",
            as: "user"
        }
    },
    { $unwind: "$user" },
    {
        $project: {
            order_id: "$_id",
            full_name: "$user.full_name",
            status: 1,
            order_date: 1,
            total_amount: 1,
            _id: 0
        }
    },
    { $sort: { order_id: 1 } }
]).pretty();



print("\n8. Создание индексов");
db.orders.createIndex({ user_id: 1 });
db.orders.createIndex({ status: 1, order_date: -1 });
db.products.createIndex({ name: "text" });

print("Индексы в orders:");
db.orders.getIndexes();
print("Индексы в products:");
db.products.getIndexes();

print("\n process stop"); 