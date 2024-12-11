import decimal
import os

from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, render_template, Response, request, jsonify, session
from flask_login import login_required
from werkzeug.security import generate_password_hash

from app.cert import roles_required
from app.export import *
from app.index import get_categories, get_menu_items_by_category
from app.utils import save_image, delete_file
from db import *

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')

@manager_bp.context_processor
def inject_navigation_data():
    db_categories = get_categories()

    # Calculate total quantity of items in the cart
    cart = session.get('cart', {})
    if cart:
        product_count = len(cart)
    else:
        product_count = 0
    return {'categories': db_categories, 'product_count': product_count}

@manager_bp.route("/", methods=['GET'])
@login_required
@roles_required(["Manager"])
def index():
    # Get counts for users by role
    manager_count = count_users_by_role('Manager')
    customer_count = count_users_by_role('Customer')

    # Get category counts
    parent_category_count = count_parent_category()
    sub_category_count = count_sub_category()

    # Get product stock counts
    product_stock_counts = count_products_by_stock()

    # Get order status counts
    order_status_counts = count_orders_by_status()

    # Pass all the data to the template
    return render_template(
        "manager.html",
        title="Manager",
        manager_count=manager_count,
        customer_count=customer_count,
        parent_category_count=parent_category_count,
        sub_category_count=sub_category_count,
        product_stock_counts=product_stock_counts,
        order_status_counts=order_status_counts
    )

@manager_bp.route("/users", methods=['GET'])
@login_required
@roles_required(["Manager"])
def users():
    db_users = get_users()
    return render_template("manager_users.html", title="Users Management", users=db_users)


@manager_bp.route("/users/delete/<int:user_id>", methods=['DELETE'])
@login_required
@roles_required(["Manager"])
def delete_user(user_id):
    """Delete a user from the database"""
    query = "DELETE FROM users WHERE UserID = %s"
    cursor = con_my_sql(query, user_id)
    cursor.close()
    return jsonify({"message": "User deleted successfully"})


@manager_bp.route("/users/edit", methods=['POST'])
@login_required
@roles_required(["Manager"])
def edit_user():
    """Edit a user's details including name, email, role, and status"""
    user_id = request.form['UserID']
    user_name = request.form['UserName']
    user_email = request.form['Email']
    user_role = request.form['Role']
    user_status = request.form['Status']

    # Update query with status included
    query = """
    UPDATE users
    SET UserName = %s, Email = %s, Role = %s, IsActive = %s
    WHERE UserID = %s
    """
    cursor = con_my_sql(query, (user_name, user_email, user_role, user_status, user_id))
    cursor.close()

    return jsonify({"message": "User updated successfully"})

@manager_bp.route("/add_user", methods=['POST'])
def add_user():
    """Admin adds a new user with a specified role."""
    # Get data from the form
    username = request.form['username'].strip()
    email = request.form['email'].strip()
    password = request.form['password'].strip()
    role = request.form['role'].strip()  # Get selected role

    # Validate username length
    if len(username) < 5:
        return jsonify({"message": "Username must be at least 5 characters long."}), 200

    # Validate email format
    try:
        email_info = validate_email(email, check_deliverability=False)
        email = email_info.normalized
    except EmailNotValidError as e:
        print(e)
        return jsonify({"message": "Invalid email format."}), 200

    # Validate password length
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters long."}), 200

    # Check if email already exists
    sql_check = "SELECT COUNT(*) AS con FROM users WHERE email = %s"
    cursor_ans = con_my_sql(sql_check, email)
    if cursor_ans.fetchone()['con'] > 0:
        return jsonify({"message": "Email already registered."}), 200
    cursor_ans.close()

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Insert user into database with the specified role
    sql_insert = "INSERT INTO users (UserName, Role, Email, Password, IsActive) VALUES (%s, %s, %s, %s, TRUE)"
    con_my_sql(sql_insert, (username, role, email, hashed_password))

    # Return success message
    return jsonify({"message": "User added successfully!"}), 200

@manager_bp.route("/export_users", methods=['GET'])
@login_required
@roles_required(["Manager"])
def export_users():
    """Route to export users data (with order counts) to CSV."""
    csv_data = export_users_to_csv()

    # Send the CSV data as a response with appropriate headers for download
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=users_with_order_counts.csv"}
    )

@manager_bp.route("/categories", methods=['GET'])
@login_required
@roles_required(["Manager"])
def categories():
    return render_template("manager_categories.html", title="Categories Management")


@manager_bp.route("/categories/add_parent", methods=['POST'])
@login_required
@roles_required(["Manager"])
def add_parent_category():
    cate_name = request.form['CateName'].strip()

    # Validate the category name
    if not cate_name:
        return jsonify({"message": "Category name is required"}), 200

    # Insert into the Categories table
    query = "INSERT INTO categories (CateName) VALUES (%s)"
    cursor = con_my_sql(query, (cate_name,))
    cursor.close()

    return jsonify({"message": "Parent category added successfully!"}), 200


@manager_bp.route("/categories/add_sub", methods=['POST'])
@login_required
@roles_required(["Manager"])
def add_sub_category():
    parent_id = request.form['ParentID']
    cate_name = request.form['CateName'].strip()

    # Validate inputs
    if not cate_name or not parent_id:
        return jsonify({"message": "Both category name and parent category are required"}), 200

    # Insert into the Categories table
    query = "INSERT INTO categories (CateName, ParentID) VALUES (%s, %s)"
    cursor = con_my_sql(query, (cate_name, parent_id))
    cursor.close()

    return jsonify({"message": "Subcategory added successfully!"}), 200


@manager_bp.route("/categories/edit", methods=['POST'])
@login_required
@roles_required(["Manager"])
def edit_category():
    cate_id = request.form.get('CateID')
    cate_name = request.form.get('CateName', '').strip()
    parent_id = request.form.get('ParentID')  # Optional ParentID

    # Validate inputs
    if not cate_name or not cate_id:
        return jsonify({"message": "Category ID and name are required"}), 200

    # Construct the query dynamically based on the presence of ParentID
    if parent_id is not None:
        # Check if the ParentID exists and is valid
        query_check_parent = "SELECT CateID FROM categories WHERE CateID = %s"
        cursor = con_my_sql(query_check_parent, (parent_id,))
        if cursor.fetchone() is None:
            cursor.close()
            return jsonify({"message": "Invalid ParentID provided"}), 200
        cursor.close()

        # Update both CateName and ParentID
        query = "UPDATE categories SET CateName = %s, ParentID = %s WHERE CateID = %s"
        params = (cate_name, parent_id, cate_id)
    else:
        # Update only CateName
        query = "UPDATE categories SET CateName = %s WHERE CateID = %s"
        params = (cate_name, cate_id)

    # Execute the update query
    cursor = con_my_sql(query, params)
    cursor.close()

    return jsonify({"message": "Category updated successfully!"}), 200

@manager_bp.route("/categories/delete/<int:cate_id>", methods=['DELETE'])
@login_required
@roles_required(["Manager"])
def delete_category(cate_id):
    # Check if category has associated menu items
    query_check_menu = """
        SELECT COUNT(*) AS con
        FROM menuitem
        WHERE CateID = %s OR CateID IN (SELECT CateID FROM categories WHERE ParentID = %s)
    """
    cursor = con_my_sql(query_check_menu, (cate_id, cate_id))
    menu_item_count = cursor.fetchone()['con']
    cursor.close()

    if menu_item_count > 0:
        return jsonify({"message": "Cannot delete category. Associated menu items exist."}), 200

    # Check if category is a parent with subcategories
    query_check_subcategories = "SELECT COUNT(*) AS con FROM categories WHERE ParentID = %s"
    cursor = con_my_sql(query_check_subcategories, (cate_id,))
    subcategory_count = cursor.fetchone()['con']
    cursor.close()

    if subcategory_count > 0:
        return jsonify({"message": "Cannot delete parent category. Subcategories exist."}), 200

    # Proceed to delete the category
    query_delete = "DELETE FROM categories WHERE CateID = %s"
    cursor = con_my_sql(query_delete, (cate_id,))
    if isinstance(cursor, tuple):
        return jsonify({"message": "Category deleted failed!"}), 200

    return jsonify({"message": "Category deleted successfully!"}), 200

@manager_bp.route("/products", methods=['GET'])
@login_required
@roles_required(["Manager"])
def products():
    db_products = get_menu_items_by_category()
    return render_template("manager_products.html", products=db_products)

@manager_bp.route("/products/add", methods=['POST'])
@login_required
@roles_required(["Manager"])
def add_product():
    item_name = request.form['ItemName']
    price = request.form['Price']
    description = request.form['Description']
    stock = request.form['Stock']
    cate_id = request.form['CateID']
    item_image = request.files.get('ItemImage')

    # Validate stock
    if int(stock) < 0:
        return jsonify({"message": "Product stock can't less than 0!"}), 200

    # Save the image if provided
    image_path = save_image(item_image) if item_image else None
    # Insert product into database
    query = """
        INSERT INTO menuitem (ItemName, Price, Description, Stock, CateID, ItemImage)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
    cursor = con_my_sql(query, (item_name, price, description, stock, cate_id, image_path))
    if isinstance(cursor, tuple):
        delete_file(image_path)
        return jsonify({"message": "Product added failed!"}), 200
    else:
        return jsonify({"message": "Product added successfully!"}), 200

@manager_bp.route("/products/edit", methods=['POST'])
@login_required
@roles_required(["Manager"])
def edit_product():
    product_id = request.form['ItemID']
    item_name = request.form['ItemName']
    price = request.form['Price']
    description = request.form['Description']
    stock = request.form['Stock']
    cate_id = request.form['CateID']
    item_image = request.files.get('ItemImage')

    # Validate stock
    if int(stock) < 0:
        return jsonify({"message": "Product stock can't less than 0!"}), 200

    # Fetch the old image path
    query = "SELECT ItemImage FROM menuitem WHERE ItemID = %s"
    cursor = con_my_sql(query, (product_id,))
    old_image_path = cursor.fetchone().get('ItemImage')

    # Save the new image if uploaded
    new_image_path = save_image(item_image) if item_image else old_image_path

    # If a new image was uploaded, delete the old image
    if item_image and old_image_path:
        try:
            os.remove(old_image_path)
        except FileNotFoundError:
            pass

    # Update product details
    query = """
    UPDATE menuitem
    SET ItemName = %s, Price = %s, Description = %s, Stock = %s, CateID = %s, ItemImage = %s
    WHERE ItemID = %s
    """
    con_my_sql(query, (item_name, price, description, stock, cate_id, new_image_path, product_id))

    return jsonify({"message": "Product updated successfully!"}), 200

@manager_bp.route("/products/delete/<int:product_id>", methods=['DELETE'])
@login_required
@roles_required(["Manager"])
def delete_product(product_id):
    # Fetch the image path
    query = "SELECT ItemImage FROM menuitem WHERE ItemID = %s"
    cursor = con_my_sql(query, (product_id,))
    image_path = cursor.fetchone().get('ItemImage')

    # Delete the product from the database
    query = "DELETE FROM menuitem WHERE ItemID = %s"
    con_my_sql(query, (product_id,))

    # Delete the image file if it exists
    if image_path:
        try:
            os.remove(image_path)
        except FileNotFoundError:
            pass

    return jsonify({"message": "Product deleted successfully!"}), 200


@manager_bp.route("/orders", methods=['GET'])
@login_required
@roles_required(["Manager"])
def user_orders():
    """Display all orders for the logged-in user with discount and tax details"""
    # Query to fetch orders along with discount and tax names and percentages
    query = """
    SELECT U.UserName, O.OrderID, O.OrderTime, COALESCE(O.OrderAmount, 0.0) AS OrderAmount, O.OrderStatus, 
           (COALESCE(O.OrderAmount, 0.0) - COALESCE(B.DiscountAmount, 0.0) + COALESCE(B.TaxAmount, 0.0)) AS TotalAmount,
           B.TipAmount, 
           B.BillTotalAmount AS BillTotalAmount, 
           COALESCE(D.DiscountPercent, 0.0) AS DiscountPercent, 
           COALESCE(D.DiscountName, 'No') AS DiscountName, 
           COALESCE(T.TaxPercent, 0.0) AS TaxPercent, 
           COALESCE(T.TaxName, 'No') AS TaxName
    FROM orders O
    LEFT JOIN bill B ON O.OrderID = B.OrderID
    LEFT JOIN discount D ON B.DiscountID = D.DiscountID
    LEFT JOIN tax T ON B.TaxID = T.TaxID
    LEFT JOIN users U ON O.UserID = U.UserID
    ORDER BY O.OrderTime DESC
    """
    cursor = con_my_sql(query)
    orders = cursor.fetchall()

    # Get all discount
    db_discounts = get_discounts()
    # Get all tax
    db_taxes = get_taxes()
    # Render the orders page
    return render_template("manager_orders.html", orders=orders, discounts=db_discounts, taxes=db_taxes)


@manager_bp.route("/orders/<int:order_id>", methods=['GET'])
@login_required
@roles_required(["Manager"])
def order_detail(order_id):
    """
    Fetch order details and related billing information for a specific order.
    """

    # Query to fetch order details, including menu items and quantities
    order_detail_query = """
        SELECT 
            O.UserID,
            menuitem.ItemID,
            menuitem.ItemName,
            menuitem.ItemImage,
            menuitem.Price,
            orderdetail.Quantity,
            orderdetail.IsLike,
            orderdetail.OrderDetailID,
            O.OrderStatus,
            menuitem.Price * orderdetail.Quantity AS Subtotal
        FROM orderdetail
        JOIN menuitem ON orderdetail.ItemID = menuitem.ItemID
        JOIN orders O ON O.OrderID = orderdetail.OrderID
        WHERE orderdetail.OrderID = %s
    """

    # Query to fetch billing details
    billing_query = """
        SELECT 
            O.OrderStatus,
            O.OrderAmount,
            B.DiscountAmount,
            B.TaxAmount,
            B.TipAmount,
            B.BillTotalAmount
        FROM orders O
        LEFT JOIN bill B ON O.OrderID = B.OrderID
        WHERE O.OrderID = %s
    """

    # Execute the queries
    cursor = con_my_sql(order_detail_query, (order_id,))
    order_items = cursor.fetchall()

    cursor = con_my_sql(billing_query, (order_id,))
    billing_info = cursor.fetchone()

    # Calculate the total food amount (sum of subtotals)
    total_food = sum(item['Subtotal'] for item in order_items)

    # Assign billing details or default to 0 if no billing info found
    order_amount = billing_info.get("OrderAmount")
    discount_amount = billing_info.get("DiscountAmount")
    tax_amount = billing_info.get("TaxAmount")
    tip_amount = billing_info.get("TipAmount")
    bill_total_amount = billing_info.get("BillTotalAmount")
    order_status = billing_info.get("OrderStatus")

    # Render the template with additional details
    return render_template(
        "manager_orders_detail.html",
        title="Order Detail",
        order_items=order_items,
        order_id=order_id,
        order_status=order_status,
        total_food=total_food,
        order_amount=order_amount,
        discount_amount=discount_amount,
        tax_amount=tax_amount,
        tip_amount=tip_amount,
        bill_total_amount=bill_total_amount
    )

@manager_bp.route("/orders/<int:order_id>/update_status", methods=['POST'])
@login_required
@roles_required(["Manager"])
def update_order_status(order_id):
    new_status = request.form.get('new_status')
    if new_status not in ['Confirmed', 'Completed']:
        return jsonify({"message": "Invalid order status"}), 400

    # Update the order status in the database
    query = """
            UPDATE orders SET OrderStatus = %s WHERE OrderID = %s
            """
    cursor = con_my_sql(query, (new_status, order_id))

    if isinstance(cursor, tuple):
        return jsonify({"message": "Error updating order status"}), 200
    else:
        return jsonify({"message": f"Order status updated to {new_status} successfully!"})

@manager_bp.route("/orders/<int:order_id>/complete", methods=['POST'])
@login_required
@roles_required(["Manager"])
def complete_order(order_id):
    """
    Complete an order by updating its status and creating a bill with selected discount and tax.
    """
    discount_id = request.form.get('discount_id')
    tax_id = request.form.get('tax_id')

    if not discount_id or not tax_id:
        return jsonify({"message": "Both discount and tax must be selected"}), 400

    try:
        conn.ping(reconnect=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Start transaction
        conn.begin()

        # Get order amount
        cursor.execute("SELECT OrderAmount FROM orders WHERE OrderID = %s", (order_id,))
        order = cursor.fetchone()
        if not order:
            raise ValueError("Order not found")

        order_amount = order['OrderAmount']

        # Get discount percentage
        cursor.execute("SELECT DiscountPercent FROM discount WHERE DiscountID = %s", (discount_id,))
        discount = cursor.fetchone()
        if not discount:
            raise ValueError("Discount not found")

        discount_percent = discount['DiscountPercent']
        discount_amount = (discount_percent / decimal.Decimal(100.0)) * order_amount

        # Get tax percentage
        cursor.execute("SELECT TaxPercent FROM tax WHERE TaxID = %s", (tax_id,))
        tax = cursor.fetchone()
        if not tax:
            raise ValueError("Tax not found")

        tax_percent = tax['TaxPercent']
        tax_amount = (tax_percent / decimal.Decimal(100.0)) * (order_amount - discount_amount)

        # Insert into bill table
        bill_query = """
        INSERT INTO bill (OrderID, DiscountID, DiscountAmount, TaxID, TaxAmount)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(bill_query, (order_id, discount_id, discount_amount, tax_id, tax_amount))

        # Update order status
        update_query = """
        UPDATE orders SET OrderStatus = 'Completed' WHERE OrderID = %s
        """
        cursor.execute(update_query, (order_id,))

        # Commit transaction
        conn.commit()

        return jsonify({"message": "Order completed successfully!"})

    except (pymysql.MySQLError, ValueError) as e:
        conn.rollback()  # Rollback transaction on error
        return jsonify({"message": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


@manager_bp.route("/export_categories", methods=['GET'])
@login_required
@roles_required(["Manager"])
def export_categories():
    """
    Route to export categories data (with product counts) to CSV.
    """
    csv_data = export_categories_to_csv()

    # Send the CSV data as a response with appropriate headers for download
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=categories_with_product_counts.csv"}
    )

@manager_bp.route("/export_products", methods=['GET'])
@login_required
@roles_required(["Manager"])
def export_products():
    """
    Route to export product details to a CSV file.
    """
    csv_data = export_products_to_csv()

    # Send the CSV data as a response with appropriate headers for download
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=products_with_details.csv"}
    )

@manager_bp.route("/export_orders", methods=['GET'])
@login_required
@roles_required(["Manager"])
def export_orders():
    """
    Route to export order details to a CSV file, including a summary row.
    """
    csv_data = export_orders_to_csv()

    # Send the CSV data as a response with appropriate headers for download
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=orders_with_details.csv"}
    )

@manager_bp.route("/taxes_discounts", methods=['GET'])
@login_required
@roles_required(["Manager"])
def taxes_discounts():
    db_discounts = con_my_sql("SELECT * FROM discount")
    db_taxes = con_my_sql("SELECT * FROM tax")
    return render_template("manager_taxes_discounts.html", title="Discount And Taxes Management",
                           discounts=db_discounts, taxes=db_taxes)

@manager_bp.route("/discounts", methods=['GET'])
@login_required
@roles_required(["Manager"])
def discounts():
    db_discounts = con_my_sql("SELECT * FROM discount")
    if isinstance(db_discounts, tuple):
        return jsonify({"code": 400, "message": "Get all discounts failed!"}), 200
    else:
        res_discounts = [dict(row) for row in db_discounts]
        return jsonify({"code": 200, "message": "Get all discounts successfully", "data": res_discounts}), 200

@manager_bp.route("/discount", methods=['POST'])
@login_required
@roles_required(["Manager"])
def add_discount():
    discount_name = request.form['DiscountName'].strip()
    discount_percent = request.form['DiscountPercent']

    # validate
    if not discount_name or not discount_percent.isnumeric():
        return jsonify({"code": 400, "message": "Invalid input."}), 200

    query = "INSERT INTO discount (DiscountName, DiscountPercent) VALUES (%s, %s)"
    res = con_my_sql(query, (discount_name, discount_percent))
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Discount added failed!"}), 200
    else:
        return jsonify({"code": 200, "message": "Discount added successfully!"}), 200

@manager_bp.route("/discount/<int:discount_id>", methods=['GET'])
@login_required
@roles_required(["Manager"])
def get_discount(discount_id):
    # SQL query to get the existing discount record
    query = """
    SELECT * FROM discount
    WHERE DiscountID = %s
    """
    res = con_my_sql(query, discount_id)
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Discount query failed!"}), 200
    else:
        discount = res.fetchall()
        if discount is not None and len(discount) > 0:
            res_discount = [dict(row) for row in discount]
            return jsonify({"code": 200, "message": "Discount query successfully", "data": res_discount}), 200
        else:
            return jsonify({"code": 404, "message": "Discount not found!"}), 200

@manager_bp.route("/discount/<int:discount_id>", methods=['PUT'])
@login_required
@roles_required(["Manager"])
def edit_discount(discount_id):
    discount_name = request.form['DiscountName'].strip()
    discount_percent = request.form['DiscountPercent']

    query = """
    UPDATE discount
    SET DiscountName = %s, DiscountPercent = %s
    WHERE DiscountID = %s
    """
    res = con_my_sql(query, (discount_name, discount_percent, discount_id))
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Discount updated failed!"}), 200
    else:
        return jsonify({"code": 200, "message": "Discount updated successfully!"}), 200


@manager_bp.route("/discount/<int:discount_id>", methods=['DELETE'])
@login_required
@roles_required(["Manager"])
def delete_discount(discount_id):
    # Query to check if the discount is referenced in the 'bill' table
    check_query = "SELECT COUNT(*) AS con FROM bill WHERE DiscountID = %s"
    count = con_my_sql(check_query, discount_id)  # Assume con_my_sql returns the query result

    if count.fetchone()['con'] > 0:  # If the discount is referenced in 'bill'
        return jsonify({"code": 400, "message": "Discount cannot be deleted as it is referenced in bills."}), 200

    # Query to delete the discount if not referenced
    delete_query = "DELETE FROM discount WHERE DiscountID = %s"
    res = con_my_sql(delete_query, discount_id)
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Discount deleted failed!"}), 200
    else:
        return jsonify({"code": 200, "message": "Discount deleted successfully!"}), 200

@manager_bp.route("/taxes", methods=['GET'])
@login_required
@roles_required(["Manager"])
def taxes():
    db_taxes = con_my_sql("SELECT * FROM tax")
    if isinstance(db_taxes, tuple):
        return jsonify({"code": 400, "message": "Get all taxes failed!"}), 200
    else:
        res_taxes = [dict(row) for row in db_taxes]
        return jsonify({"code": 200, "message": "Get all taxes successfully", "data": res_taxes}), 200

@manager_bp.route("/tax", methods=['POST'])
@login_required
@roles_required(["Manager"])
def add_tax():
    # Get form data for tax name and tax percentage
    tax_name = request.form['TaxName'].strip()
    tax_percent = request.form['TaxPercent']

    # Validate the input
    if not tax_name or not tax_percent.isnumeric():
        return jsonify({"message": "Invalid input."}), 200

    # SQL query to insert the new tax record
    query = "INSERT INTO tax (TaxName, TaxPercent) VALUES (%s, %s)"
    res = con_my_sql(query, (tax_name, tax_percent))
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Tax added failed!"}), 200
    else:
        return jsonify({"code": 200, "message": "Tax added successfully!"}), 200

@manager_bp.route("/tax/<int:tax_id>", methods=['GET'])
@login_required
@roles_required(["Manager"])
def get_tax(tax_id):
    # SQL query to get the existing tax record
    query = """
    SELECT * FROM tax
    WHERE TaxID = %s
    """
    res = con_my_sql(query, tax_id)
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Tax query failed!"}), 200
    else:
        tax = res.fetchall()
        if tax is not None and len(tax) > 0:
            res_tax = [dict(row) for row in tax]
            return jsonify({"code": 200, "message": "Tax query successfully!", "data": res_tax}), 200
        else:
            return jsonify({"code": 404, "message": "Tax not found!"}), 200

@manager_bp.route("/tax/<int:tax_id>", methods=['PUT'])
@login_required
@roles_required(["Manager"])
def edit_tax(tax_id):
    # Get form data for name, and percentage
    tax_name = request.form['TaxName'].strip()
    tax_percent = request.form['TaxPercent']

    # SQL query to update the existing tax record
    query = """
    UPDATE tax
    SET TaxName = %s, TaxPercent = %s
    WHERE TaxID = %s
    """
    res = con_my_sql(query, (tax_name, tax_percent, tax_id))
    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Tax updated failed!"}), 200
    else:
        return jsonify({"code": 200, "message": "Tax updated successfully"}), 200

@manager_bp.route("/tax/<int:tax_id>", methods=['DELETE'])
@login_required
@roles_required(["Manager"])
def delete_tax(tax_id):
    # Query to check if the tax is referenced in the 'bill' table
    check_query = "SELECT COUNT(*) AS con FROM bill WHERE TaxID = %s"
    count = con_my_sql(check_query, tax_id)  # Assume con_my_sql returns the query result

    if count.fetchone()['con'] > 0:  # If the tax is referenced in 'bill'
        return jsonify({"message": "Tax cannot be deleted as it is referenced in bills."}), 200

    # Query to delete the tax if not referenced
    delete_query = "DELETE FROM tax WHERE TaxID = %s"
    res = con_my_sql(delete_query, tax_id)

    if isinstance(res, tuple):
        return jsonify({"code": 400, "message": "Tax deleted failed!"}), 200
    else:
        return jsonify({"code": 200, "message": "Tax deleted successfully"}), 200