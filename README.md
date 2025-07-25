# eCommerce Simulator

## Overview
The eCommerce Simulator is a web application built with Flask, SQLite3, and HTML, designed to manage an online store with products, customers, vendors, and a personalized tiered discount/rewards system. It supports user authentication (admin and customer roles), CRUD operations for products, customers, vendors, and discounts, and a dynamic discount system that assigns 15%, 10%, and 5% discounts based on customer purchase history. The database is initialized from and synchronized with a `sample_data.txt` file, ensuring data persistence.

## Features
- **User Authentication**: Login and registration for admins and customers.
- **Shopping Interface**: Customers can view and purchase products with applicable discounts.
- **Admin Management**: CRUD operations for products, customers, vendors, and discounts.
- **Tiered Discount System**: Automatically assigns discounts (15%, 10%, 5%) to customers based on total purchases (5, 10, 20) and category-specific purchase counts (5+ per category).
- **Recommendations**: Admins can generate product recommendations and manually assign discounts.
- **Data Synchronization**: Database state is synced with `sample_data.txt` for persistence.

## Technologies
- **Backend**: Flask (Python), SQLite3
- **Frontend**: HTML with minimal CSS
- **Data Storage**: SQLite database (`database.db`) and `sample_data.txt`

## Installation
### Prerequisites
- Python 3.8+
- Flask (`pip install flask`)
- SQLite3 (included with Python)

### Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd ecommerce-simulator
   ```

2. **Install Dependencies**:
   ```bash
   pip install flask
   ```

3. **Prepare the Data File**:
   - Ensure `sample_data.txt` is in the project root with at least 20 tuples per table (see example below).
   - Example `sample_data.txt` snippet:
     ```
     # Sample data for e-commerce database
     PRODUCTS
     999.99,Laptop,Electronics
     29.99,T-Shirt,Clothing
     ...
     CUSTOMERS
     Jane Doe
     John Smith
     ...
     USERS
     admin,admin123,Admin,NULL
     customer1,123,Customer,Jane Doe
     ...
     ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   - The app runs at `http://localhost:5000` in debug mode.

## Database Schema
The SQLite database (`database.db`) includes seven tables:

1. **Product** (`PID`, `Price`, `Name`, `Category`)
   - Primary Key: `PID`
   - Example: `(1, 999.99, 'Laptop', 'Electronics')`

2. **Customer** (`CID`, `Name`)
   - Primary Key: `CID`
   - Example: `(1, 'Jane Doe')`

3. **Vendor** (`VID`, `Name`)
   - Primary Key: `VID`
   - Example: `(1, 'TechCorp')`

4. **Discount** (`DID`, `Percentage`, `Type`, `CID`, `Category`)
   - Primary Key: `DID`
   - Foreign Key: `CID → Customer(CID)`
   - Example: `(1, 15.0, 'Rewards', 1, 'Electronics')`

5. **Buys** (`CID`, `PID`, `DiscountApplied`)
   - Primary Key: `(CID, PID)`
   - Foreign Keys: `CID → Customer(CID)`, `PID → Product(PID)`
   - Example: `(1, 1, 1)`

6. **Supplies** (`VID`, `PID`)
   - Primary Key: `(VID, PID)`
   - Foreign Keys: `VID → Vendor(VID)`, `PID → Product(PID)`
   - Example: `(1, 1)`

7. **Users** (`UID`, `Username`, `Password`, `UserType`, `CID`)
   - Primary Key: `UID`
   - Foreign Key: `CID → Customer(CID)`
   - Example: `(1, 'admin', 'admin123', 'Admin', NULL)`

## Usage
### Running the App
1. Start the server: `python app.py`.
2. Open `http://localhost:5000` in a browser.

### Example Scenarios
1. **Admin Actions**:
   - **Login**: Use `admin`/`admin123`.
   - **Manage Products**: Go to `/products` to add (e.g., `Mouse`, $99.99, Electronics), update, or delete products.
   - **View Customers**: Go to `/customers` to add/delete customers or view purchase history (e.g., Jane Doe’s Laptop purchase at $849.99 with 15% off).
   - **Manage Discounts**: Go to `/discounts` to generate recommendations for Jane Doe (e.g., Electronics products) or manually assign a 10% Clothing discount.

2. **Customer Actions**:
   - **Login**: Use `customer1`/`123` (Jane Doe).
   - **Shop**: Go to `/shop` to view unpurchased products (e.g., Laptop at $849.99 with 15% off). Purchase a product to trigger discount updates.
   - **Discounts**: After 5 Electronics purchases, see a 15% discount; after 10 total (including 5 Clothing), see a 10% Clothing discount.

### Key Routes
- `/`: Login and registration page.
- `/shop`: Customer shopping interface with discounted products.
- `/products`: Admin product management (CRUD).
- `/customers`: Admin customer management and purchase history.
- `/vendors`: Admin vendor management with performance analysis.
- `/discounts`: Admin discount management and recommendations.
- `/logout`: Clears session and returns to login.

## Tiered Discount System
The advanced feature is a personalized discount system:
- **Logic**: Assigns discounts based on total purchases and category-specific counts:
  - 15% off the most-purchased category (5+ purchases, 5 total purchases).
  - 10% off the second most-purchased (5+ purchases, 10 total).
  - 5% off the third most-purchased (5+ purchases, 20 total).
- **Implementation**: The `update_discounts` function (`app.py`, lines 213–241) uses `GROUP BY` to rank categories and `DELETE`/`INSERT` to update discounts.
- **Example**: Jane Doe with 5 Electronics, 5 Clothing, 3 Books purchases gets 15% off Electronics and 10% off Clothing after 10 total purchases.
- **Uniqueness**: Unlike static coupon systems, discounts are dynamic, category-specific, and automatically updated after purchases.
