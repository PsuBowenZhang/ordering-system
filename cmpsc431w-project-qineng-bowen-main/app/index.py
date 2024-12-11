import decimal

from flask import render_template, Blueprint, flash, redirect, url_for, session, request, jsonify
from flask_login import login_required, logout_user

from db import con_my_sql

index_bp = Blueprint('index', __name__)


def get_categories():
    """Get category data, including first-level categories and their corresponding subcategories"""
    # Get first-level categories
    cate_query = "SELECT CateID, CateName FROM categories WHERE ParentID IS NULL"
    cursor = con_my_sql(cate_query)
    categories = cursor.fetchall()
    cursor.close()

    modified_categories = []
    # Get subcategories of each first-level category
    for category in categories:
        sub_query = "SELECT CateID, CateName FROM categories WHERE ParentID = %s"
        sub_cursor = con_my_sql(sub_query, category['CateID'])
        categories = sub_cursor.fetchall()
        category['subcategories'] = categories
        sub_cursor.close()
        modified_categories.append(category)


    return modified_categories


def get_menu_items_by_category(cate_id=None):
    """Retrieve menu items for a specific category (optional). If no category is provided, return all menu items."""
    # Start the base query to select items from MenuItem and join with Categories
    query = """
    SELECT ItemID, ItemName, ItemImage, Price, Description, Stock, CreateTime, categories.CateID, categories.CateName
    FROM menuitem
    INNER JOIN categories ON menuitem.CateID = categories.CateID
    """

    # If cate_id is provided, filter by category
    if cate_id:
        query += " WHERE categories.CateID = %s"

    query += " ORDER BY menuitem.CreateTime DESC"
    cursor = con_my_sql(query, (cate_id,) if cate_id else ())  # Execute the query with or without category filter
    menu_items = cursor.fetchall()
    cursor.close()
    return menu_items


@index_bp.context_processor
def inject_navigation_data():
    db_categories = get_categories()

    # Calculate total quantity of items in the cart
    cart = session.get('cart', {})
    if cart:
        product_count = len(cart)
    else:
        product_count = 0
    return {'categories': db_categories, 'product_count': product_count}

@index_bp.route("/login", methods=['GET'])
def login():
    return render_template("login.html", title="Login")


@index_bp.route("/register", methods=['GET'])
def register():
    return render_template("register.html", title="Register")

@index_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Logout successfully.', 'info')
    return redirect(url_for('index.index'))

@index_bp.route("/", methods=['GET'])
def index():
    """Display all menu items on the homepage"""
    menu_items = get_menu_items_by_category()
    return render_template("index.html", title="Homepage", menu_items=menu_items)

@index_bp.route("/category/<int:category_id>", methods=['GET'])
def category_page(category_id):
    """Display products for the selected category with breadcrumb navigation"""
    # Check if the category_id is valid
    if category_id == 0:
        flash("Invalid category ID.", "error")
        return redirect(url_for("index.index"))

    # Get the selected category name
    cate_query = "SELECT CateName FROM categories WHERE CateID = %s"
    cursor = con_my_sql(cate_query, category_id)
    category = cursor.fetchone()
    cursor.close()

    # If the category does not exist, flash a message and redirect to homepage
    if not category:
        flash("Category does not exist.", "error")
        return redirect(url_for("index.index"))

    # Get all products for the selected category
    menu_items = get_menu_items_by_category(category_id)
    return render_template("category.html", title=category["CateName"], menu_items=menu_items)


@index_bp.route("/cart/add", methods=['POST'])
def add_to_cart():
    item_id = request.form.get('ItemID')
    quantity = int(request.form.get('Quantity', 1))
    sql_query = "SELECT Stock, ItemName, Price FROM menuitem WHERE ItemID = %s "
    cursor = con_my_sql(sql_query, item_id)
    product = cursor.fetchone()
    if not product:
        return jsonify({"message": "Product not found!"}), 404

    stock = product['Stock']
    item_name = product['ItemName']
    price = product['Price']
    # Check stock availability
    if stock < quantity:
        return jsonify({"message": f"Insufficient stock for {item_name}. Available: {stock}."}), 400

    # Initialize cart if it doesn't exist in session
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    # Add item to cart or update quantity
    if item_id in cart:
        cart[item_id]['quantity'] += quantity
    else:
        cart[item_id] = {
            'item_name': item_name,
            'price': price,
            'quantity': quantity
        }

    # Update session
    session['cart'] = cart

    return jsonify({"message": f"{item_name} added to cart.", "cart": session['cart']}), 200


@index_bp.route("/cart", methods=['GET'])
def cart():
    """Display all items in the cart with updated details from the database"""
    session_cart = session.get('cart', {})
    if not session_cart:
        return render_template("cart.html", title="My Cart", cart_items=[], total=0.0)

    # Get the list of ItemIDs from the cart
    item_ids = list(session_cart.keys())
    placeholders = ', '.join(['%s'] * len(item_ids))

    # Query the menuitem table for the items in the cart
    query = f"""
    SELECT ItemID, ItemName, ItemImage, Price, Stock 
    FROM menuitem 
    WHERE ItemID IN ({placeholders})
    """
    cursor = con_my_sql(query, item_ids)
    products = cursor.fetchall()
    cursor.close()

    # Build the cart data with updated details
    cart_items = []
    total = decimal.Decimal(0.0)
    for product in products:
        item_id = str(product['ItemID'])
        quantity = session_cart[item_id]['quantity']
        subtotal = product['Price'] * quantity
        total += subtotal
        cart_items.append({
            "item_id": item_id,
            "item_name": product['ItemName'],
            "item_image": product['ItemImage'],
            "price": product['Price'],
            "quantity": quantity,
            "stock": product['Stock'],
            "subtotal": round(subtotal, 2),
        })

    return render_template("cart.html", title="Cart", cart_items=cart_items, total=round(total, 2))


@index_bp.route("/cart/remove", methods=['POST'])
def remove_from_cart():
    item_id = request.form.get('ItemID')
    print(item_id)
    if 'cart' in session and item_id in session['cart']:
        del session['cart'][item_id]
        session.modified = True
        return jsonify({"message": "Item removed from cart.", "cart": session['cart']}), 200
    return jsonify({"message": "Item not found in cart."}), 404

@index_bp.route("/cart/update", methods=['POST'])
def update_cart_quantity():
    """Update the quantity of an item in the cart, with stock validation."""
    item_id = request.form.get('ItemID')  # Get the ItemID from the request
    quantity = int(request.form.get('Quantity', 1))  # Get the desired quantity, default to 1

    # Fetch product information from the database to validate stock
    sql_query = "SELECT Stock, ItemName FROM menuitem WHERE ItemID = %s"
    cursor = con_my_sql(sql_query, item_id)
    product = cursor.fetchone()

    if not product:
        # Return an error if the product does not exist
        return jsonify({"message": "Product not found!"}), 404

    stock = product['Stock']  # Extract the stock from the database
    item_name = product['ItemName']  # Extract the item name for messaging

    # Ensure the cart exists in the session
    cart = session.get('cart', {})

    if item_id in cart:
        if quantity > stock:
            # If the requested quantity exceeds the available stock, return an error
            return jsonify({"message": f"Insufficient stock for {item_name}. Available: {stock}."}), 400
        elif quantity <= 0:
            # If the quantity is zero or less, remove the item from the cart
            del cart[item_id]
        else:
            # Update the cart with the new quantity
            cart[item_id]['quantity'] = quantity

        # Mark the session as modified to save changes
        session['cart'] = cart
        session.modified = True

        # Return a success response with the updated cart
        return jsonify({"message": "Cart updated.", "cart": session['cart']}), 200
    else:
        # If the item is not found in the cart, return a not-found message
        return jsonify({"message": "Item not found in cart."}), 200

@index_bp.route("/cart/count", methods=["GET"])
def cart_count():
    """Return the current count of items in the cart."""
    cart = session.get("cart", {})
    product_count = len(cart)
    return jsonify({"product_count": product_count})

@index_bp.route("/hot", methods=["GET"])
def hot():
    # SQL query to calculate the score and total sales quantity for each item
    query = """
           SELECT 
               m.ItemID, 
               m.ItemName, 
               m.ItemImage, 
               m.Price, 
               m.Description, 
               m.Stock, 
               c.CateID, 
               c.CateName,
               IFNULL(SUM(CASE WHEN od.IsLike = 1 THEN od.Quantity WHEN od.IsLike = 0 THEN -od.Quantity ELSE 0 END), 0) AS Score,
               IFNULL(SUM(od.Quantity), 0) AS TotalQuantity
           FROM menuitem m
           LEFT JOIN categories c ON m.CateID = c.CateID
           LEFT JOIN orderdetail od ON m.ItemID = od.ItemID
           WHERE m.Stock > 0
           GROUP BY m.ItemID
           ORDER BY Score DESC, TotalQuantity DESC
           LIMIT 8
           """
    # Execute the query
    cursor = con_my_sql(query)
    top_items = cursor.fetchall()
    return render_template("hot.html", title="Hot Sales", menu_items=top_items)

@index_bp.route("/products", methods=['GET'])
def products():
    """Display all menu items on the homepage"""
    menu_items = get_menu_items_by_category()

    if menu_items is not None and len(menu_items) > 0:
        db_products = [dict(row) for row in menu_items]
        return jsonify({"code": 200, "message": "Products query successfully", "data": db_products}), 200
    else:
        return jsonify({"code": 404, "message": "Product not found!"}), 200

@index_bp.route("/hot_products", methods=['GET'])
def hot_products():
    # SQL query to calculate the score and total sales quantity for each item
    query = """
           SELECT 
               m.ItemID, 
               m.ItemName, 
               m.ItemImage, 
               m.Price, 
               m.Description, 
               m.Stock, 
               c.CateID, 
               c.CateName,
               IFNULL(SUM(CASE WHEN od.IsLike = 1 THEN od.Quantity WHEN od.IsLike = 0 THEN -od.Quantity ELSE 0 END), 0) AS Score,
               IFNULL(SUM(od.Quantity), 0) AS TotalQuantity
           FROM menuitem m
           LEFT JOIN categories c ON m.CateID = c.CateID
           LEFT JOIN orderdetail od ON m.ItemID = od.ItemID
           WHERE m.Stock > 0
           GROUP BY m.ItemID
           ORDER BY Score DESC, TotalQuantity DESC
           LIMIT 8
           """
    # Execute the query
    cursor = con_my_sql(query)
    top_items = cursor.fetchall()

    if top_items is not None and len(top_items) > 0:
        db_products = [dict(row) for row in top_items]
        return jsonify({"code": 200, "message": "Hot products query successfully", "data": db_products}), 200
    else:
        return jsonify({"code": 404, "message": "Hot product not found!"}), 200