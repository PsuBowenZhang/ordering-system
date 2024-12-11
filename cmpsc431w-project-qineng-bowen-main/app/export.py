import csv
from io import StringIO

from db import *


def export_users_to_csv():
    """Export user data (including order count) to CSV."""
    users = get_users_with_order_counts()

    # Create a CSV in-memory string buffer
    output = StringIO()
    writer = csv.writer(output)

    # Define CSV header
    header = ['No', 'UserName', 'Role', 'Email', 'OrderCount', 'PaidAmount']
    writer.writerow(header)

    # Write user data
    for index, user in enumerate(users, start=1):
        # Write the 'No' as the incremented index value (starting from 1)
        writer.writerow([index, user['UserName'], user['Role'], user['Email'], user['OrderCount'], user['BillTotalAmount']])

    # Save CSV to file or return as a response (for download)
    # You can save this to a file or return it as a Flask response
    output.seek(0)  # Move to the start of the StringIO buffer
    return output.getvalue()

def export_categories_to_csv():
    """
    Export category data (including product counts) to CSV.
    """
    # Fetch category data
    categories = get_category_product_counts()

    # Calculate the total product count
    total_product_count = sum(category['ProductCount'] for category in categories)

    # Create a CSV in-memory string buffer
    output = StringIO()
    writer = csv.writer(output)

    # Define CSV header
    header = ['No', 'ParentCategory', 'CategoryName', 'ProductCount']
    writer.writerow(header)

    # Write category data
    for index, category in enumerate(categories, start=1):
        writer.writerow([
            index,
            category['ParentCategoryName'],
            category['CategoryName'],
            category['ProductCount']
        ])

    # Write the total row
    writer.writerow(['Total', '', '', total_product_count])

    # Save CSV to file or return as a response (for download)
    output.seek(0)  # Move to the start of the StringIO buffer
    return output.getvalue()

def export_products_to_csv():
    """
    Export all product details to a CSV file.
    """
    products = get_all_product_details()

    # Create a CSV in-memory string buffer
    output = StringIO()
    writer = csv.writer(output)

    # Define CSV header
    header = ['No', 'ItemName', 'CateName', 'ItemImage', 'Price', 'Description', 'Stock',
              'CreateTime', 'SaleQuantity', 'Likes', 'UnLikes']
    writer.writerow(header)

    # Write product data
    for index, product in enumerate(products, start=1):
        writer.writerow([
            index,
            product['ItemName'],
            product['CateName'] or 'None',
            product['ItemImage'] or 'None',
            product['Price'],
            product['Description'] or 'None',
            product['Stock'],
            product['CreateTime'].strftime("%Y-%m-%d %H:%M:%S"),
            product['SaleQuantity'],
            product['Likes'],
            product['UnLikes']
        ])

    # Save CSV to file or return as a response (for download)
    output.seek(0)  # Move to the start of the StringIO buffer
    return output.getvalue()

def export_orders_to_csv():
    """
    Export all order details to a CSV file, including discount, tax, and tip details.
    """
    orders = get_all_order_details()

    # Calculate the total amounts for all orders
    total_discount = sum(order['DiscountAmount'] for order in orders)
    total_tax = sum(order['TaxAmount'] for order in orders)
    total_tip = sum(order['TipAmount'] for order in orders)
    total_paid = sum(order['BillTotalAmount'] for order in orders)

    # Create a CSV in-memory string buffer
    output = StringIO()
    writer = csv.writer(output)

    # Define CSV header
    header = [
        'No', 'OrderUserName', 'OrderTime', 'OrderAmount', 'OrderStatus',
        'ProductCount', 'DiscountName', 'DiscountPercent', 'DiscountAmount',
        'TaxName', 'TaxPercent', 'TaxAmount', 'TipAmount', 'BillTotalAmount'
    ]
    writer.writerow(header)

    # Write order data
    for index, order in enumerate(orders, start=1):
        writer.writerow([
            index,
            order['OrderUserName'],
            order['OrderTime'].strftime("%Y-%m-%d %H:%M:%S"),
            order['OrderAmount'],
            order['OrderStatus'],
            order['ProductCount'],
            order['DiscountName'],
            f"{order['DiscountPercent']}%" if order['DiscountPercent'] is not None else '',
            order['DiscountAmount'],
            order['TaxName'],
            f"{order['TaxPercent']}%" if order['TaxPercent'] is not None else '',
            order['TaxAmount'],
            order['TipAmount'],
            order['BillTotalAmount']
        ])

    # Add summary row for totals
    writer.writerow([
        'Total', '', '', '', '', '', '', '', total_discount,
        '', '', total_tax, total_tip, total_paid
    ])

    # Save CSV to file or return as a response
    output.seek(0)  # Move to the start of the StringIO buffer
    return output.getvalue()

