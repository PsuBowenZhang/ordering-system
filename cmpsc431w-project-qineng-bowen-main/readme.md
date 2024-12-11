# Online Restaurant System

## **Overview**
This project is a web-based online food ordering system designed to streamline the ordering process for customers and simplify management for administrators. The system is developed using the following technologies:

- **Backend**: Python3, Flask  
- **Frontend**: Bootstrap 4, jQuery  
- **Database**: MySQL 8  

The application provides an intuitive user interface for browsing menus, placing orders, and managing the system.

---

## **Features**
- Customers can browse available menu items, add them to the cart, and place orders.  
- Administrators can manage menu items, categories, and monitor orders.  
- Secure login functionality for both administrators and customers.  

---

## **Getting Started**

### **Prerequisites**
1. Python 3.10+ installed on your system.  
2. MySQL 8.0+ installed and running.  

---

### **Installation Steps**
1. Install the required Python packages using the following command:  
   ```bash
   pip install -r requirements.txt
   ```
2. Restore the `restaurant.sql` file to your MySQL 8.0 database.
3. Configure the MySQL database connection in the application (config.py).  
4. Start the project using the command:  
   ```bash
   python3 run.py
   ```
5. Access the application through a browser:  
   ```
   http://127.0.0.1:80/
   ```

---

## **Deployed Project**
The project has been successfully deployed and is accessible at:  
[https://megamaxp.pythonanywhere.com/](https://megamaxp.pythonanywhere.com/)

---

## **Accounts**
The system comes with the following pre-configured accounts for testing:  

| **Role**      | **Email**          | **Password**      |
|---------------|--------------------|-------------------|
| Administrator | admin@mail.com     | admin@mail.com    |
| Customer      | admin@email.com     | admin@email.com    |

---

## **Technologies Used**
- **Python**: Flask framework for backend development.  
- **Bootstrap 4**: For responsive and mobile-friendly UI.  
- **jQuery**: For dynamic and interactive user interfaces.  
- **MySQL 8**: Database management system to store and manage application data.  
