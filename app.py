from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'COP4710' #Simple key used and isn't hidden as this was made for a DB class.

# Initialize SQLite3 database and populate with data from sample_data.txt
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Drop existing tables
    c.execute('DROP TABLE IF EXISTS Product')
    c.execute('DROP TABLE IF EXISTS Customer')
    c.execute('DROP TABLE IF EXISTS Vendor')
    c.execute('DROP TABLE IF EXISTS Discount')
    c.execute('DROP TABLE IF EXISTS Buys')
    c.execute('DROP TABLE IF EXISTS Supplies')
    c.execute('DROP TABLE IF EXISTS Users')
    
    # Create tables
    c.execute('''CREATE TABLE Product (
        PID INTEGER PRIMARY KEY AUTOINCREMENT,
        Price REAL,
        Name TEXT,
        Category TEXT)''')
    
    c.execute('''CREATE TABLE Customer (
        CID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT)''')
    
    c.execute('''CREATE TABLE Vendor (
        VID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT)''')
    
    c.execute('''CREATE TABLE Discount (
        DID INTEGER PRIMARY KEY AUTOINCREMENT,
        Percentage REAL,
        Type TEXT,
        CID INTEGER,
        Category TEXT,
        FOREIGN KEY (CID) REFERENCES Customer(CID))''')
    
    c.execute('''CREATE TABLE Buys (
        CID INTEGER,
        PID INTEGER,
        DiscountApplied INTEGER DEFAULT 0,
        PRIMARY KEY (CID, PID),
        FOREIGN KEY (CID) REFERENCES Customer(CID),
        FOREIGN KEY (PID) REFERENCES Product(PID))''')
    
    c.execute('''CREATE TABLE Supplies (
        VID INTEGER,
        PID INTEGER,
        PRIMARY KEY (VID, PID),
        FOREIGN KEY (VID) REFERENCES Vendor(VID),
        FOREIGN KEY (PID) REFERENCES Product(PID))''')
    
    c.execute('''CREATE TABLE Users (
        UID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT UNIQUE,
        Password TEXT,
        UserType TEXT,
        CID INTEGER,
        FOREIGN KEY (CID) REFERENCES Customer(CID))''')
    
    # Load data from sample_data.txt
    customer_name_to_cid = {}
    with open('sample_data.txt', 'r') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line in ['PRODUCTS', 'CUSTOMERS', 'VENDORS', 'BUYS', 'SUPPLIES', 'DISCOUNTS', 'USERS']:
                section = line
                continue
            data = line.split('#')[0].strip()
            if not data:
                continue
            if section == 'PRODUCTS':
                price, name, category = data.split(',')
                c.execute("INSERT INTO Product (Price, Name, Category) VALUES (?, ?, ?)", 
                         (float(price), name.strip(), category.strip()))
            elif section == 'CUSTOMERS':
                name = data
                c.execute("INSERT INTO Customer (Name) VALUES (?)", (name.strip(),))
                c.execute("SELECT last_insert_rowid()")
                cid = c.fetchone()[0]
                customer_name_to_cid[name.strip()] = cid
            elif section == 'VENDORS':
                name = data
                c.execute("INSERT INTO Vendor (Name) VALUES (?)", (name.strip(),))
            elif section == 'BUYS':
                parts = data.split(',')
                cid = int(parts[0])
                pid = int(parts[1])
                discount_applied = int(parts[2]) if len(parts) > 2 else 0
                c.execute("INSERT INTO Buys (CID, PID, DiscountApplied) VALUES (?, ?, ?)", (cid, pid, discount_applied))
            elif section == 'SUPPLIES':
                vid, pid = map(int, data.split(','))
                c.execute("INSERT INTO Supplies (VID, PID) VALUES (?, ?)", (vid, pid))
            elif section == 'DISCOUNTS':
                percentage, type_, cid, category = data.split(',')
                c.execute("INSERT INTO Discount (Percentage, Type, CID, Category) VALUES (?, ?, ?, ?)",
                         (float(percentage), type_.strip(), int(cid), category.strip()))
            elif section == 'USERS':
                username, password, user_type, cid_or_name = data.split(',')
                cid = None
                if cid_or_name != 'NULL':
                    c.execute("SELECT CID FROM Customer WHERE Name = ?", (cid_or_name.strip(),))
                    result = c.fetchone()
                    cid = result[0] if result else None
                c.execute("INSERT INTO Users (Username, Password, UserType, CID) VALUES (?, ?, ?, ?)",
                         (username.strip(), password.strip(), user_type.strip(), cid))
    
    # Add default admin only if no users exist in sample_data.txt
    with open('sample_data.txt', 'r') as f:
        if 'USERS' not in f.read():
            c.execute("INSERT INTO Users (Username, Password, UserType, CID) VALUES (?, ?, ?, NULL)",
                     ("admin", "admin123", "Admin"))
    
    conn.commit()
    conn.close()

# Sync database state to sample_data.txt
def sync_to_file():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    with open('sample_data.txt', 'w') as f:
        f.write("# Sample data for e-commerce database\n")
        
        f.write("\nPRODUCTS\n")
        c.execute("SELECT Price, Name, Category FROM Product ORDER BY PID")
        for price, name, category in c.fetchall():
            f.write(f"{price},{name},{category}\n")
        
        f.write("\nCUSTOMERS\n")
        c.execute("SELECT Name FROM Customer ORDER BY CID")
        for name in c.fetchall():
            f.write(f"{name[0]}\n")
        
        f.write("\nVENDORS\n")
        c.execute("SELECT Name FROM Vendor ORDER BY VID")
        for name in c.fetchall():
            f.write(f"{name[0]}\n")
        
        f.write("\nBUYS\n")
        c.execute("SELECT CID, PID, DiscountApplied FROM Buys ORDER BY CID, PID")
        for cid, pid, discount_applied in c.fetchall():
            f.write(f"{cid},{pid},{discount_applied}\n")
        
        f.write("\nSUPPLIES\n")
        c.execute("SELECT VID, PID FROM Supplies ORDER BY VID, PID")
        for vid, pid in c.fetchall():
            f.write(f"{vid},{pid}\n")
        
        f.write("\nDISCOUNTS\n")
        c.execute("SELECT Percentage, Type, CID, Category FROM Discount ORDER BY DID")
        for percentage, type_, cid, category in c.fetchall():
            if cid and category:
                f.write(f"{percentage},{type_},{cid},{category}\n")
        
        f.write("\nUSERS\n")
        c.execute("SELECT u.Username, u.Password, u.UserType, u.CID, c.Name FROM Users u LEFT JOIN Customer c ON u.CID = c.CID ORDER BY u.UID")
        for username, password, user_type, cid, name in c.fetchall():
            cid_str = name if cid is not None else 'NULL'
            f.write(f"{username},{password},{user_type},{cid_str}\n")
    
    conn.close()

# Login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'login' in request.form:
            username = request.form['username']
            password = request.form['password']
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT UID, UserType, CID FROM Users WHERE Username = ? AND Password = ?", (username, password))
            user = c.fetchone()
            conn.close()
            if user:
                session['uid'] = user[0]
                session['user_type'] = user[1]
                session['cid'] = user[2]
                if user[1] == 'Admin':
                    return redirect(url_for('products'))
                else:
                    return redirect(url_for('shop'))
            else:
                return render_template('login.html', error="Invalid credentials")
        elif 'register' in request.form:
            username = request.form['username']
            password = request.form['password']
            user_type = request.form['user_type']
            name = request.form.get('name', '')
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            try:
                if user_type == 'Customer' and name:
                    c.execute("SELECT CID FROM Customer WHERE Name = ?", (name,))
                    result = c.fetchone()
                    if result:
                        cid = result[0]
                    else:
                        c.execute("INSERT INTO Customer (Name) VALUES (?)", (name,))
                        c.execute("SELECT last_insert_rowid()")
                        cid = c.fetchone()[0]
                    c.execute("INSERT INTO Users (Username, Password, UserType, CID) VALUES (?, ?, ?, ?)",
                             (username, password, user_type, cid))
                else:
                    c.execute("INSERT INTO Users (Username, Password, UserType, CID) VALUES (?, ?, ?, NULL)",
                             (username, password, user_type))
                conn.commit()
                sync_to_file()
                return render_template('login.html', message="Account created! Please log in.")
            except sqlite3.IntegrityError:
                conn.close()
                return render_template('login.html', error="Username already exists")
            finally:
                conn.close()
    return render_template('login.html')

# Customer shopping page
@app.route('/shop', methods=['GET', 'POST'])
def shop():
    if 'uid' not in session or session['user_type'] != 'Customer':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST' and 'buy' in request.form:
        pid = int(request.form['pid'])
        cid = session['cid']
        c.execute('''SELECT d.Percentage 
                     FROM Discount d 
                     JOIN Product p ON p.Category = d.Category 
                     WHERE d.CID = ? AND p.PID = ?''', (cid, pid))
        discount = c.fetchone()
        discount_applied = 1 if discount else 0
        c.execute("INSERT OR IGNORE INTO Buys (CID, PID, DiscountApplied) VALUES (?, ?, ?)", 
                  (cid, pid, discount_applied))
        conn.commit()
        sync_to_file()
        # Update discounts after purchase
        update_discounts(cid)
    
    c.execute('''SELECT p.PID, p.Price, p.Name, p.Category, d.Percentage
                 FROM Product p
                 LEFT JOIN Discount d ON p.Category = d.Category AND d.CID = ?
                 WHERE p.PID NOT IN (SELECT PID FROM Buys WHERE CID = ?)''', 
                 (session['cid'], session['cid']))
    products = []
    for pid, price, name, category, percentage in c.fetchall():
        discounted_price = price * (1 - percentage / 100) if percentage else price
        products.append((pid, price, name, category, percentage, discounted_price))
    
    c.execute("SELECT Name FROM Customer WHERE CID = ?", (session['cid'],))
    customer_name = c.fetchone()[0]
    
    conn.close()
    return render_template('shop.html', products=products, customer_name=customer_name)

# Update discounts based on purchase history
def update_discounts(cid):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get purchase counts per category
    c.execute('''SELECT p.Category, COUNT(b.PID) as purchase_count
                 FROM Buys b
                 JOIN Product p ON b.PID = p.PID
                 WHERE b.CID = ?
                 GROUP BY p.Category
                 ORDER BY purchase_count DESC''', (cid,))
    category_counts = c.fetchall()
    
    # Get total purchases
    c.execute("SELECT COUNT(*) FROM Buys WHERE CID = ?", (cid,))
    total_purchases = c.fetchone()[0]
    
    # Determine unlocked discount tiers
    discounts_unlocked = []
    if total_purchases >= 5:  # Unlock 15% for top category
        discounts_unlocked.append((15.0, 0))  # (percentage, min_purchases)
    if total_purchases >= 10:  # 2x 5 for 10% discount
        discounts_unlocked.append((10.0, 1))
    if total_purchases >= 20:  # 2x 10 for 5% discount
        discounts_unlocked.append((5.0, 2))
    
    # Clear existing discounts for this customer
    c.execute("DELETE FROM Discount WHERE CID = ? AND Type = 'Rewards'", (cid,))
    
    # Assign discounts to top categories
    for i, (percentage, min_rank) in enumerate(discounts_unlocked):
        if i < len(category_counts) and category_counts[i][1] >= 5:  # At least 5 purchases in category
            category = category_counts[i][0]
            c.execute("INSERT INTO Discount (Percentage, Type, CID, Category) VALUES (?, 'Rewards', ?, ?)",
                     (percentage, cid, category))
    
    conn.commit()
    conn.close()

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Products CRUD with Vendor Information (Admin only)
@app.route('/products', methods=['GET', 'POST'])
def products():
    if 'uid' not in session or session['user_type'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        if 'add' in request.form:
            price = float(request.form['price'])
            name = request.form['name']
            category = request.form['category']
            c.execute("INSERT INTO Product (Price, Name, Category) VALUES (?, ?, ?)", (price, name, category))
        elif 'delete' in request.form:
            pid = int(request.form['pid'])
            c.execute("DELETE FROM Product WHERE PID = ?", (pid,))
        elif 'update' in request.form:
            pid = int(request.form['pid'])
            price = float(request.form['price'])
            c.execute("UPDATE Product SET Price = ? WHERE PID = ?", (price, pid))
        conn.commit()
        sync_to_file()
    
    search = request.args.get('search', '')
    if search:
        c.execute('''SELECT p.PID, p.Price, p.Name, p.Category, v.Name AS VendorName
                     FROM Product p
                     LEFT JOIN Supplies s ON p.PID = s.PID
                     LEFT JOIN Vendor v ON s.VID = v.VID
                     WHERE p.Name LIKE ? OR p.Category LIKE ?''', (f'%{search}%', f'%{search}%'))
    else:
        c.execute('''SELECT p.PID, p.Price, p.Name, p.Category, v.Name AS VendorName
                     FROM Product p
                     LEFT JOIN Supplies s ON p.PID = s.PID
                     LEFT JOIN Vendor v ON s.VID = v.VID''')
    products = c.fetchall()
    
    conn.close()
    return render_template('products.html', products=products)

# Customers CRUD with Purchase History (Admin only)
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if 'uid' not in session or session['user_type'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    purchases = None
    customer_name = None
    
    if request.method == 'POST':
        if 'add' in request.form:
            name = request.form['name']
            c.execute("INSERT INTO Customer (Name) VALUES (?)", (name,))
        elif 'delete' in request.form:
            cid = int(request.form['cid'])
            c.execute("DELETE FROM Customer WHERE CID = ?", (cid,))
        elif 'view_purchases' in request.form:
            cid = int(request.form['cid'])
            c.execute("SELECT Name FROM Customer WHERE CID = ?", (cid,))
            customer_name = c.fetchone()[0]
            c.execute('''SELECT p.PID, p.Name, p.Price, p.Category, b.DiscountApplied, d.Percentage
                         FROM Buys b
                         JOIN Product p ON b.PID = p.PID
                         LEFT JOIN Discount d ON d.CID = b.CID AND d.Category = p.Category
                         WHERE b.CID = ?''', (cid,))
            purchases_raw = c.fetchall()
            purchases = []
            for pid, name, price, category, discount_applied, percentage in purchases_raw:
                discounted_price = price * (1 - percentage / 100) if discount_applied and percentage else price
                purchases.append((pid, name, price, category, discount_applied, discounted_price))
        conn.commit()
        sync_to_file()
    
    c.execute("SELECT * FROM Customer")
    customers = c.fetchall()
    
    conn.close()
    return render_template('customers.html', customers=customers, purchases=purchases, customer_name=customer_name)

# Vendors CRUD with Performance Analysis (Admin only)
@app.route('/vendors', methods=['GET', 'POST'])
def vendors():
    if 'uid' not in session or session['user_type'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    performance = None
    vendor_name = None
    
    if request.method == 'POST':
        if 'add' in request.form:
            name = request.form['name']
            c.execute("INSERT INTO Vendor (Name) VALUES (?)", (name,))
        elif 'delete' in request.form:
            vid = int(request.form['vid'])
            c.execute("DELETE FROM Vendor WHERE VID = ?", (vid,))
        elif 'view_performance' in request.form:
            vid = int(request.form['vid'])
            c.execute("SELECT Name FROM Vendor WHERE VID = ?", (vid,))
            vendor_name = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM Supplies WHERE VID = ?", (vid,))
            total_products = c.fetchone()[0]
            
            c.execute('''SELECT COUNT(b.PID), SUM(p.Price)
                         FROM Supplies s
                         JOIN Product p ON s.PID = p.PID
                         LEFT JOIN Buys b ON p.PID = b.PID
                         WHERE s.VID = ?''', (vid,))
            sales, revenue = c.fetchone()
            sales = sales if sales else 0
            revenue = revenue if revenue else 0.0
            
            c.execute('''SELECT p.PID, p.Name, COUNT(b.PID) as purchase_count
                         FROM Supplies s
                         JOIN Product p ON s.PID = p.PID
                         LEFT JOIN Buys b ON p.PID = b.PID
                         WHERE s.VID = ?
                         GROUP BY p.PID, p.Name
                         ORDER BY purchase_count DESC
                         LIMIT 1''', (vid,))
            popular_product = c.fetchone()
            popular_product_name = popular_product[1] if popular_product and popular_product[2] > 0 else "None"
            popular_product_purchases = popular_product[2] if popular_product and popular_product[2] > 0 else 0
            
            performance = {
                'total_products': total_products,
                'total_sales': sales,
                'revenue': revenue,
                'popular_product_name': popular_product_name,
                'popular_product_purchases': popular_product_purchases
            }
        conn.commit()
        sync_to_file()
    
    search = request.args.get('search', '')
    if search:
        c.execute("SELECT * FROM Vendor WHERE Name LIKE ?", (f'%{search}%',))
    else:
        c.execute("SELECT * FROM Vendor")
    vendors = c.fetchall()
    
    conn.close()
    return render_template('vendors.html', vendors=vendors, performance=performance, vendor_name=vendor_name)

# Discounts CRUD with Category-Based Discounts and Recommendations (Admin only)
@app.route('/discounts', methods=['GET', 'POST'])
def discounts():
    if 'uid' not in session or session['user_type'] != 'Admin':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    recommendations = None
    customer_name_rec = None
    discount_message = None
    
    if request.method == 'POST':
        if 'add' in request.form:
            percentage = float(request.form['percentage'])
            type_ = request.form['type']
            c.execute("INSERT INTO Discount (Percentage, Type, CID, Category) VALUES (?, ?, NULL, NULL)", 
                     (percentage, type_))
        elif 'delete' in request.form:
            did = int(request.form['did'])
            c.execute("DELETE FROM Discount WHERE DID = ?", (did,))
        elif 'recommend' in request.form:
            cid = int(request.form['cid'])
            c.execute("SELECT Name FROM Customer WHERE CID = ?", (cid,))
            customer_name_rec = c.fetchone()[0]
            
            c.execute('''SELECT DISTINCT p.Category
                         FROM Buys b
                         JOIN Product p ON b.PID = p.PID
                         WHERE b.CID = ?''', (cid,))
            categories = [row[0] for row in c.fetchall()]
            
            if categories:
                c.execute('''SELECT p.Category, COUNT(b.PID) as purchase_count
                             FROM Buys b
                             JOIN Product p ON b.PID = p.PID
                             WHERE b.CID = ?
                             GROUP BY p.Category
                             ORDER BY purchase_count DESC''', (cid,))
                category_purchases = {row[0]: row[1] for row in c.fetchall()}
                
                c.execute('''SELECT p.PID, p.Name, p.Price, p.Category, d.Percentage
                             FROM Product p
                             LEFT JOIN Discount d ON p.Category = d.Category AND d.CID = ?
                             WHERE p.Category IN ({})
                             AND p.PID NOT IN (
                                 SELECT PID FROM Buys WHERE CID = ?
                             )'''.format(','.join('?' * len(categories))), [cid] + categories + [cid])
                recs = c.fetchall()
                
                recommendations = []
                seen_categories = set()
                for pid, name, price, category, percentage in recs:
                    if category not in seen_categories:
                        recommendations.append({
                            'PID': pid,
                            'Name': name,
                            'Price': price,
                            'Category': category,
                            'Discount': percentage if percentage else 'None',
                            'PurchaseCount': category_purchases.get(category, 0),
                            'CID': cid
                        })
                        seen_categories.add(category)
        elif 'add_discount' in request.form:
            cid = int(request.form['cid'])
            category = request.form['category']
            c.execute("SELECT Name FROM Customer WHERE CID = ?", (cid,))
            customer_name = c.fetchone()[0]
            
            # Check current discounts and assign next available tier
            c.execute('''SELECT Category, Percentage
                         FROM Discount
                         WHERE CID = ? AND Type = 'Rewards' AND Category != ?
                         ORDER BY Percentage DESC''', (cid, category))
            existing_discounts = c.fetchall()
            used_percentages = [row[1] for row in existing_discounts]
            
            # Determine next available discount tier
            available_tiers = [(15.0, 5), (10.0, 10), (5.0, 20)]  # (percentage, min_total_purchases)
            c.execute("SELECT COUNT(*) FROM Buys WHERE CID = ?", (cid,))
            total_purchases = c.fetchone()[0]
            
            discount_percentage = None
            for percentage, min_purchases in available_tiers:
                if percentage not in used_percentages and total_purchases >= min_purchases:
                    discount_percentage = percentage
                    break
            
            if discount_percentage:
                c.execute("SELECT DID FROM Discount WHERE CID = ? AND Category = ? AND Type = 'Rewards'", (cid, category))
                if not c.fetchone():
                    c.execute("INSERT INTO Discount (Percentage, Type, CID, Category) VALUES (?, 'Rewards', ?, ?)", 
                             (discount_percentage, cid, category))
                    discount_message = f"Added {discount_percentage}% discount on {category} products for {customer_name} (CID: {cid})."
                else:
                    discount_message = f"Discount already exists for {category} for {customer_name} (CID: {cid})."
            else:
                discount_message = f"No eligible discount tier available for {customer_name} (CID: {cid}). Total purchases: {total_purchases}."
        
        conn.commit()
        sync_to_file()
    
    c.execute('''SELECT d.DID, d.Percentage, d.Type, d.Category, c.CID, c.Name AS CustomerName
                 FROM Discount d
                 LEFT JOIN Customer c ON d.CID = c.CID''')
    discounts = c.fetchall()
    c.execute("SELECT CID, Name FROM Customer")
    customers = c.fetchall()
    
    conn.close()
    return render_template('discounts.html', discounts=discounts, customers=customers,
                         recommendations=recommendations, customer_name_rec=customer_name_rec,
                         discount_message=discount_message)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
