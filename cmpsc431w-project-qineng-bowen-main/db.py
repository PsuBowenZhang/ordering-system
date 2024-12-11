import pymysql
import config

conn = pymysql.connect(host=config.HOST, port=config.PORT, user=config.USER, password=config.PASSWORD,
                       database=config.DBNAME,
                       charset=config.CHARSET)


def con_my_sql(sql_code, params=None):
    try:
        conn.ping(reconnect=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SET time_zone = '-05:00';")
        cursor.execute(sql_code, params or {})
        conn.commit()
        conn.close()
        return cursor

    except pymysql.MySQLError as err:
        print(err)
        conn.rollback()
        conn.close()
        return type(err), err

def count_parent_category():
    query = "SELECT COUNT(*) AS con FROM categories WHERE ParentID IS NULL"
    cursor = con_my_sql(query)
    cursor.close()
    return cursor.fetchone()['con']

def count_sub_category():
    query = "SELECT COUNT(*) AS con FROM categories WHERE ParentID IS NOT NULL"
    cursor = con_my_sql(query)
    cursor.close()
    return cursor.fetchone()['con']

def count_users_by_role(role):
    """Count users by their role"""
    query = "SELECT COUNT(*) AS con FROM users WHERE Role = %s"
    cursor = con_my_sql(query, role)
    cursor.close()
    return cursor.fetchone()['con']


def count_products_by_stock():
    """Count products based on their stock levels"""
    # Stock = 0
    query_0 = "SELECT COUNT(*) AS con FROM menuitem WHERE Stock = 0"
    cursor_0 = con_my_sql(query_0)
    count_0 = cursor_0.fetchone()['con']

    # Stock between 1 and 10
    query_1_10 = "SELECT COUNT(*) AS con FROM menuitem WHERE Stock BETWEEN 1 AND 10"
    cursor_1_10 = con_my_sql(query_1_10)
    count_1_10 = cursor_1_10.fetchone()['con']

    # Stock between 11 and 100
    query_11_100 = "SELECT COUNT(*) AS con FROM menuitem WHERE Stock BETWEEN 11 AND 100"
    cursor_11_100 = con_my_sql(query_11_100)
    count_11_100 = cursor_11_100.fetchone()['con']

    # Stock > 100
    query_100_plus = "SELECT COUNT(*) AS con FROM menuitem WHERE Stock > 100"
    cursor_100_plus = con_my_sql(query_100_plus)
    count_100_plus = cursor_100_plus.fetchone()['con']

    return {
        'stock_0': count_0,
        'stock_1_10': count_1_10,
        'stock_11_100': count_11_100,
        'stock_100_plus': count_100_plus
    }


def count_orders_by_status():
    """Count orders by their status"""
    statuses = ['Waiting', 'Confirmed', 'Completed', 'Paid']
    order_counts = {}

    for status in statuses:
        query = "SELECT COUNT(*) AS con FROM orders WHERE OrderStatus = %s"
        cursor = con_my_sql(query, status)
        order_counts[status] = cursor.fetchone()['con']

    return order_counts

def get_users_with_order_counts():
    """Get all users and their corresponding order counts (including users with zero orders)."""
    query = """
    SELECT u.UserID, u.UserName, u.Role, u.Email, COUNT(o.OrderID) AS OrderCount, COALESCE(SUM(b.BillTotalAmount),0) AS BillTotalAmount
    FROM users u
    LEFT JOIN orders o ON u.UserID = o.UserID
    LEFT JOIN bill b ON o.OrderID = b.OrderID
    GROUP BY u.UserID
    """
    cursor = con_my_sql(query)
    return cursor.fetchall()

def get_discounts():
    """
    Get all discounts from the discount table, including their IDs, names, and percentages.
    """
    query = """
    SELECT DiscountID, DiscountName, DiscountPercent
    FROM discount
    ORDER BY DiscountID
    """
    cursor = con_my_sql(query)  # Assume `con_my_sql` is a helper function for executing queries
    return cursor.fetchall()

def get_taxes():
    """
    Get all taxes from the tax table, including their IDs, names, and percentages.
    """
    query = """
    SELECT TaxID, TaxName, TaxPercent
    FROM tax
    ORDER BY TaxID
    """
    cursor = con_my_sql(query)  # Assume `con_my_sql` is a helper function for executing queries
    return cursor.fetchall()



def get_users():
    """Get all users."""
    query = """
    SELECT UserID, UserName, Role, Email, IsActive
    FROM users
    """
    cursor = con_my_sql(query)
    return cursor.fetchall()

def get_category_product_counts():
    """
    Get all categories with their parent category and product counts.
    Includes parent categories and their product counts.
    """
    query = """
    SELECT 
        c1.CateID AS CategoryID,
        c1.CateName AS CategoryName,
        c2.CateName AS ParentCategoryName,
        COUNT(mi.ItemID) AS ProductCount
    FROM categories c1
    LEFT JOIN categories c2 ON c1.ParentID = c2.CateID
    LEFT JOIN menuitem mi ON mi.CateID = c1.CateID
    WHERE c1.ParentID IS NOT NULL
    GROUP BY c1.CateID, c2.CateName
    ORDER BY c2.CateName, c1.CateName
    """
    cursor = con_my_sql(query)  # Replace with your database connection function
    return cursor.fetchall()

def get_all_product_details():
    """
    Fetch all product details including:
    ItemName, CateName, ItemImage, Price, Description, Stock, CreateTime,
    SaleQuantity (sum of quantities sold, 0 if none),
    Likes (count of positive feedback, 0 if none),
    UnLikes (count of negative feedback, 0 if none).
    """
    query = """
    SELECT 
        mi.ItemID,
        mi.ItemName,
        c.CateName,
        mi.ItemImage,
        mi.Price,
        mi.Description,
        mi.Stock,
        mi.CreateTime,
        COALESCE(SUM(od.Quantity), 0) AS SaleQuantity,
        COUNT(CASE WHEN od.IsLike = TRUE THEN 1 END) AS Likes,
        COUNT(CASE WHEN od.IsLike = FALSE THEN 1 END) AS UnLikes
    FROM 
        menuitem mi
    LEFT JOIN 
        categories c ON mi.CateID = c.CateID
    LEFT JOIN 
        orderdetail od ON mi.ItemID = od.ItemID
    GROUP BY 
        mi.ItemID, c.CateName
    ORDER BY 
        mi.CreateTime DESC;
    """
    cursor = con_my_sql(query)
    return cursor.fetchall()

def get_all_order_details():
    """
    Fetch all order details including:
    OrderUserName, OrderTime, OrderAmount, OrderStatus,
    ProductCount (total items in the order),
    Discount, Tax, and BillTotalAmount.
    """
    query = """
    SELECT 
        o.OrderID,
        u.UserName AS OrderUserName,
        o.OrderTime,
        o.OrderAmount,
        o.OrderStatus,
        COUNT(od.ItemID) AS ProductCount,
        d.DiscountName,
        d.DiscountPercent,
        COALESCE(b.DiscountAmount, 0) AS DiscountAmount,
        t.TaxName,
        t.TaxPercent,
        COALESCE(b.TaxAmount, 0) AS TaxAmount,
        COALESCE(b.TipAmount, 0) AS TipAmount,
        COALESCE(b.BillTotalAmount, 0) AS BillTotalAmount
    FROM 
        orders o
    LEFT JOIN 
        users u ON o.UserID = u.UserID
    LEFT JOIN 
        orderdetail od ON o.OrderID = od.OrderID
    LEFT JOIN 
        bill b ON o.OrderID = b.OrderID
    LEFT JOIN 
        discount d ON b.DiscountID = d.DiscountID
    LEFT JOIN 
        tax t ON b.TaxID = t.TaxID
    GROUP BY 
        o.OrderID, u.UserName, o.OrderTime, o.OrderAmount, o.OrderStatus,
        d.DiscountName, d.DiscountPercent, b.DiscountAmount,
        t.TaxName, t.TaxPercent, b.TaxAmount, b.TipAmount, b.BillTotalAmount
    ORDER BY 
        o.OrderTime DESC;
    """
    cursor = con_my_sql(query)
    return cursor.fetchall()


# username = "admin"
# email = "admin@mail.com"
# pwd = "admin@mail.com"
# hashed_password = generate_password_hash(pwd, method='pbkdf2')

# sql = f"INSERT INTO users(UserName, Role, Email, Password) VALUES('{username}', 'Customer', '{email}', '{hashed_password}')"
# print(con_my_sql(sql))

# query_sql = "SELECT * FROM users WHERE email=%s AND IsActive = %s"
# cursor_ans = con_my_sql(query_sql, (email, 1))
# print(cursor_ans.fetchall())
