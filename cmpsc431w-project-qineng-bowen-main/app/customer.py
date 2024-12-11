import decimal
import time

import pymysql
from flask import Blueprint, render_template, session, flash, redirect, url_for, jsonify, request
from flask_login import login_required, current_user

from app.cert import roles_required
from app.index import get_categories
from db import conn, con_my_sql

customer_bp = Blueprint('customer', __name__, url_prefix='/customer')

@customer_bp.context_processor
def inject_navigation_data():
    db_categories = get_categories()

    # Calculate total quantity of items in the cart
    cart = session.get('cart', {})
    if cart:
        product_count = len(cart)
    else:
        product_count = 0
    return {'categories': db_categories, 'product_count': product_count}

@customer_bp.route("/", methods=['GET'])
@login_required
@roles_required(["Customer", "Manager"])
def index():
    """Retrieve summary statistics for the logged-in user's orders."""
    user_id = current_user.get_id()

    # Total amount for paid bills
    paid_query = """
        SELECT COALESCE(SUM(bill.BillTotalAmount), 0.0) AS total_paid_amount 
        FROM bill 
        INNER JOIN orders ON bill.OrderID = orders.OrderID 
        WHERE orders.UserID = %s
        """
    cursor_paid = con_my_sql(paid_query, (user_id,))
    total_paid_amount = cursor_paid.fetchone().get('total_paid_amount', 0.0)

    # Total amount for unpaid orders
    unpaid_query = """
        SELECT COALESCE(SUM(orders.OrderAmount), 0.0) AS total_unpaid_amount 
        FROM orders 
        LEFT JOIN bill ON orders.OrderID = bill.OrderID 
        WHERE orders.UserID = %s AND bill.BillID IS NULL
        """
    cursor_unpaid = con_my_sql(unpaid_query, (user_id,))
    total_unpaid_amount = cursor_unpaid.fetchone().get('total_unpaid_amount', 0.0)

    # Count of orders in the bill
    orders_in_bill_query = """
        SELECT COUNT(*) AS orders_in_bill 
        FROM orders 
        WHERE orders.UserID = %s AND orders.OrderStatus = 'Paid'
        """
    cursor_orders_in_bill = con_my_sql(orders_in_bill_query, (user_id,))
    orders_in_bill_count = cursor_orders_in_bill.fetchone().get('orders_in_bill', 0)

    # Count of orders not in the bill
    orders_not_in_bill_query = """
        SELECT COUNT(*) AS orders_not_in_bill 
        FROM orders 
        WHERE orders.UserID = %s AND orders.OrderStatus <> 'Paid'
        """
    cursor_orders_not_in_bill = con_my_sql(orders_not_in_bill_query, (user_id,))
    orders_not_in_bill_count = cursor_orders_not_in_bill.fetchone().get('orders_not_in_bill', 0)

    return render_template(
        "customer.html",
        total_paid_amount=total_paid_amount,
        total_unpaid_amount=total_unpaid_amount,
        orders_in_bill_count=orders_in_bill_count,
        orders_not_in_bill_count=orders_not_in_bill_count,
        title="Customer"
    )

@customer_bp.route("/cart/checkout", methods=["GET", "POST"])
@login_required
@roles_required(["Customer", "Manager"])
def checkout():
    """Process checkout by creating an order, adding order details, and updating stock."""
    cart = session.get("cart", {})  # Retrieve the cart from session
    if not cart:
        flash("Cart is empty.")
        return redirect(url_for('index.cart'))

    try:
        conn.ping(reconnect=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Step 1: Create an order
        order_query = """
        INSERT INTO orders (UserID, OrderAmount)
        VALUES (%s, %s)
        """
        # Ensure price and quantity are converted to the correct numeric types
        total_amount = sum(float(item["price"]) * int(item["quantity"]) for item in cart.values())

        cursor.execute("SET time_zone = '-05:00';")
        cursor.execute(order_query, (current_user.get_id(), total_amount))
        order_id = cursor.lastrowid  # Get the newly created OrderID

        # Step 2: Insert order details and update stock
        for item_id, item in cart.items():
            quantity = item["quantity"]

            # Check if stock is sufficient
            stock_check_query = "SELECT Stock FROM menuitem WHERE ItemID = %s"
            cursor.execute(stock_check_query, (item_id,))
            stock_result = cursor.fetchone()
            if not stock_result or stock_result["Stock"] < quantity:
                flash(f"Insufficient stock for item ID {item_id}.")
                raise ValueError(f"Insufficient stock for item ID {item_id}.")

            # Insert into orderdetail
            order_detail_query = """
            INSERT INTO orderdetail (OrderID, ItemID, Quantity)
            VALUES (%s, %s, %s)
            """
            cursor.execute(order_detail_query, (order_id, item_id, quantity))

            # Update stock in menuitem
            stock_update_query = """
            UPDATE menuitem SET Stock = Stock - %s WHERE ItemID = %s
            """
            cursor.execute(stock_update_query, (quantity, item_id))

        # Step 3: Commit the transaction
        conn.commit()

        # Clear the cart after successful checkout
        session.pop("cart", None)
        return redirect(url_for('customer.index'))

    except pymysql.MySQLError as err:
        conn.rollback()  # Rollback transaction on any SQL error
        return jsonify({"message": "Checkout failed.", "error": str(err)}), 500

    except ValueError as e:
        conn.rollback()  # Rollback transaction for insufficient stock
        return jsonify({"message": str(e)}), 400

    finally:
        cursor.close()

@customer_bp.route("/orders", methods=['GET'])
@login_required
@roles_required(["Customer", "Manager"])
def user_orders():
    """Display all orders for the logged-in user"""
    # Query to get the user's orders with left join on Bill table
    query = """
    SELECT O.OrderID, O.OrderTime, COALESCE(O.OrderAmount, 0.0) AS OrderAmount, O.OrderStatus, 
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
    WHERE O.UserID = %s
    ORDER BY O.OrderTime DESC
    """
    cursor = con_my_sql(query, (current_user.get_id(),))
    orders = cursor.fetchall()

    # Render the orders page
    return render_template("customer_orders.html", orders=orders)

@customer_bp.route("/orders/pay", methods=['POST'])
@login_required
@roles_required(["Customer", "Manager"])
def pay_order():
    """Process payment for an order."""
    try:
        order_id = request.form.get('order_id')
        tip_amount = decimal.Decimal(request.form.get('tip_amount'))

        # Ensure tip amount is non-negative
        if tip_amount < 0:
            return jsonify({"message": "Tip amount must be greater than or equal to 0"}), 400

        conn.ping(reconnect=True)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Retrieve the existing bill and order details
        bill_query = """
        SELECT b.DiscountAmount, b.TaxAmount, o.OrderAmount
        FROM bill b
        JOIN orders o ON b.OrderID = o.OrderID
        WHERE b.OrderID = %s AND o.UserID = %s 
        """
        cursor.execute(bill_query, (order_id, current_user.get_id()))
        bill = cursor.fetchone()

        if not bill:
            return jsonify({"message": "Bill or order not found"}), 404

        discount_amount = decimal.Decimal(bill['DiscountAmount'])
        tax_amount = decimal.Decimal(bill['TaxAmount'])
        order_amount = decimal.Decimal(bill['OrderAmount'])

        # Calculate the new total bill amount
        total_amount = order_amount - discount_amount + tax_amount + tip_amount

        # Update the bill with the new tip amount and total amount
        update_bill_query = """
        UPDATE bill
        SET TipAmount = %s, BillTotalAmount = %s
        WHERE OrderID = %s
        """
        cursor.execute(update_bill_query, (tip_amount, total_amount, order_id))

        # Update the order status to 'Paid'
        update_order_query = """
        UPDATE orders
        SET OrderStatus = 'Paid'
        WHERE OrderID = %s
        """
        cursor.execute(update_order_query, (order_id,))

        # Commit the transaction
        conn.commit()

        return jsonify({"message": "Payment successful", "total_amount": str(total_amount)}), 200

    except Exception as e:
        print(e)
        # Roll back transaction in case of an error
        conn.rollback()
        return jsonify({"message": "Error processing payment", "error": str(e)}), 500


@customer_bp.route("/orders/<int:order_id>", methods=['GET'])
@login_required
@roles_required(["Customer", "Manager"])
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
        "customer_orders_detail.html",
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


@customer_bp.route("/orders/<int:order_detail_id>/update_like", methods=['POST'])
@login_required
def update_like_status(order_detail_id):
    is_like = request.form.get('is_like')
    print(is_like)
    # Validate the input
    if isinstance(is_like, str):
        if is_like.lower() == 'true':
            is_like = True
        elif is_like.lower() == 'false':
            is_like = False
    if is_like not in [True, False]:
        return jsonify({"message": "Invalid value for 'is_like'"}), 400

    # Update the IsLike value in the database
    query = """
    UPDATE orderdetail SET IsLike = %s WHERE OrderDetailID = %s
    """
    cursor = con_my_sql(query, (is_like, order_detail_id))

    if isinstance(cursor, tuple):
        return jsonify({"message": "Error updating like status"}), 200
    else:
        return jsonify({"message": f"Like status updated to {'Liked' if is_like else 'Unliked'} successfully!"}), 200
