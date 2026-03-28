"""
Supermarket Billing System - Main Flask Application
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, g, Response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
import io
import json
import shutil
from datetime import datetime, timedelta
import barcode
from barcode.writer import SVGWriter

import config
from database import get_db, close_db, init_db, query_db, execute_db

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

app.teardown_appcontext(close_db)

# Ensure upload folder exists
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

# ─── Auth Decorators ──────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login_page'))
        if session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('dashboard_page'))
        return f(*args, **kwargs)
    return decorated


# ─── Page Routes ──────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/products')
@login_required
def products_page():
    return render_template('products.html')

@app.route('/categories')
@login_required
def categories_page():
    return render_template('categories.html')

@app.route('/suppliers')
@admin_required
def suppliers_page():
    return render_template('suppliers.html')

@app.route('/purchases')
@admin_required
def purchases_page():
    return render_template('purchases.html')

@app.route('/billing')
@login_required
def billing_page():
    return render_template('billing.html')

@app.route('/customers')
@login_required
def customers_page():
    return render_template('customers.html')

@app.route('/sales-history')
@login_required
def sales_history_page():
    # Redirect admin to admin sales history
    if session.get('role') == 'admin':
        return redirect(url_for('admin_sales_history_page'))
    return render_template('sales_history.html')

@app.route('/admin/sales-history')
@admin_required
def admin_sales_history_page():
    return render_template('admin_sales_history.html')

@app.route('/reports')
@admin_required
def reports_page():
    return render_template('reports.html')

@app.route('/stock')
@admin_required
def stock_page():
    return render_template('stock.html')

@app.route('/expenses')
@admin_required
def expenses_page():
    return render_template('expenses.html')

@app.route('/users')
@admin_required
def users_page():
    return render_template('users.html')

@app.route('/settings')
@admin_required
def settings_page():
    return render_template('settings.html')


# ═══════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════

# ─── Authentication ───────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = query_db('SELECT * FROM users WHERE username = ? AND is_active = 1', [username], one=True)
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role']
            }
        })
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout')
def api_logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/me')
@login_required
def api_me():
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'full_name': session['full_name'],
        'role': session['role']
    })

@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json()
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not old_pw or not new_pw:
        return jsonify({'error': 'Both passwords required'}), 400
    user = query_db('SELECT * FROM users WHERE id = ?', [session['user_id']], one=True)
    if not check_password_hash(user['password_hash'], old_pw):
        return jsonify({'error': 'Current password is incorrect'}), 400
    execute_db('UPDATE users SET password_hash = ? WHERE id = ?',
               [generate_password_hash(new_pw), session['user_id']])
    return jsonify({'message': 'Password changed successfully'})


# ─── Dashboard Stats ─────────────────────────────────────
@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().strftime('%Y-%m-01')
    is_admin = session.get('role') == 'admin'
    user_id = session.get('user_id')

    # For cashiers, filter sales by their own user_id
    if is_admin:
        today_sales = query_db(
            "SELECT COALESCE(SUM(total), 0) as total, COUNT(*) as count FROM sales WHERE DATE(sale_date) = ?",
            [today], one=True
        )
        monthly_revenue = query_db(
            "SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE sale_date >= ?",
            [month_start], one=True
        )
    else:
        today_sales = query_db(
            "SELECT COALESCE(SUM(total), 0) as total, COUNT(*) as count FROM sales WHERE DATE(sale_date) = ? AND user_id = ?",
            [today, user_id], one=True
        )
        monthly_revenue = query_db(
            "SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE sale_date >= ? AND user_id = ?",
            [month_start, user_id], one=True
        )

    total_products = query_db("SELECT COUNT(*) as count FROM products", one=True)
    total_categories = query_db("SELECT COUNT(*) as count FROM categories", one=True)
    low_stock = query_db(
        "SELECT COUNT(*) as count FROM products WHERE stock_qty <= min_stock", one=True
    )
    total_customers = query_db("SELECT COUNT(*) as count FROM customers", one=True)
    total_staff = query_db("SELECT COUNT(*) as count FROM users WHERE is_active = 1", one=True)
    total_suppliers = query_db("SELECT COUNT(*) as count FROM suppliers", one=True)

    # Monthly chart data (last 6 months)
    chart_data = []
    for i in range(5, -1, -1):
        d = datetime.now() - timedelta(days=i * 30)
        ms = d.strftime('%Y-%m-01')
        me = (d.replace(day=28) + timedelta(days=4)).replace(day=1).strftime('%Y-%m-%d')
        if is_admin:
            month_total = query_db(
                "SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE sale_date >= ? AND sale_date < ?",
                [ms, me], one=True
            )
        else:
            month_total = query_db(
                "SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE sale_date >= ? AND sale_date < ? AND user_id = ?",
                [ms, me, user_id], one=True
            )
        chart_data.append({
            'month': d.strftime('%b %Y'),
            'total': month_total['total']
        })

    # Low stock products
    low_stock_products = query_db(
        "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.stock_qty <= p.min_stock ORDER BY p.stock_qty ASC LIMIT 10"
    )

    # Expiring soon (within 30 days)
    expiry_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    expiring = query_db(
        "SELECT * FROM products WHERE expiry_date IS NOT NULL AND expiry_date <= ? AND expiry_date >= ? ORDER BY expiry_date ASC LIMIT 10",
        [expiry_date, today]
    )

    # Recent sales - filtered for cashiers
    if is_admin:
        recent_sales = query_db(
            "SELECT s.*, u.full_name as cashier_name FROM sales s LEFT JOIN users u ON s.user_id = u.id ORDER BY s.sale_date DESC LIMIT 5"
        )
    else:
        recent_sales = query_db(
            "SELECT s.*, u.full_name as cashier_name FROM sales s LEFT JOIN users u ON s.user_id = u.id WHERE s.user_id = ? ORDER BY s.sale_date DESC LIMIT 5",
            [user_id]
        )

    result = {
        'today_sales': today_sales['total'],
        'today_orders': today_sales['count'],
        'total_products': total_products['count'],
        'total_categories': total_categories['count'],
        'low_stock_count': low_stock['count'],
        'total_customers': total_customers['count'],
        'monthly_revenue': monthly_revenue['total'],
        'chart_data': chart_data,
        'low_stock_products': low_stock_products,
        'expiring_products': expiring,
        'recent_sales': recent_sales,
        'is_admin': is_admin
    }

    # Only include admin-specific stats for admins
    if is_admin:
        result['total_staff'] = total_staff['count']
        result['total_suppliers'] = total_suppliers['count']

    return jsonify(result)


# ─── Categories ───────────────────────────────────────────
@app.route('/api/categories', methods=['GET', 'POST'])
@login_required
def api_categories():
    if request.method == 'GET':
        cats = query_db(
            "SELECT c.*, (SELECT COUNT(*) FROM products WHERE category_id = c.id) as product_count FROM categories c ORDER BY c.name"
        )
        return jsonify(cats)

    # Restrict POST (add category) to admin only
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    name = data.get('name', '').strip()
    desc = data.get('description', '').strip()
    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    try:
        cid = execute_db("INSERT INTO categories (name, description) VALUES (?, ?)", [name, desc])
        return jsonify({'message': 'Category added', 'id': cid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Category already exists'}), 400

@app.route('/api/categories/<int:cid>', methods=['PUT', 'DELETE'])
@login_required
def api_category(cid):
    # Restrict PUT/DELETE to admin only
    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    if request.method == 'PUT':
        data = request.get_json()
        name = data.get('name', '').strip()
        desc = data.get('description', '').strip()
        if not name:
            return jsonify({'error': 'Category name is required'}), 400
        try:
            execute_db("UPDATE categories SET name = ?, description = ? WHERE id = ?", [name, desc, cid])
            return jsonify({'message': 'Category updated'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Category name already exists'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # DELETE
    product_count = query_db("SELECT COUNT(*) as c FROM products WHERE category_id = ?", [cid], one=True)
    if product_count['c'] > 0:
        return jsonify({'error': 'Cannot delete category with products'}), 400
    execute_db("DELETE FROM categories WHERE id = ?", [cid])
    return jsonify({'message': 'Category deleted'})


# ─── Products ─────────────────────────────────────────────
@app.route('/api/products', methods=['GET', 'POST'])
@login_required
def api_products():
    if request.method == 'GET':
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', '')
        query = """SELECT p.*, c.name as category_name
                   FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE 1=1"""
        params = []
        if search:
            query += " AND (p.name LIKE ? OR p.barcode LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        query += " ORDER BY p.name"
        return jsonify(query_db(query, params))

    data = request.get_json()
    required = ['name', 'selling_price']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    try:
        pid = execute_db(
            """INSERT INTO products (name, barcode, category_id, purchase_price, selling_price,
               stock_qty, min_stock, expiry_date, gst_percent) VALUES (?,?,?,?,?,?,?,?,?)""",
            [
                data['name'].strip(), None,
                data.get('category_id') or None, float(data.get('purchase_price', 0)),
                float(data['selling_price']), int(data.get('stock_qty', 0)),
                int(data.get('min_stock', 10)), data.get('expiry_date') or None,
                float(data.get('gst_percent', 0))
            ]
        )
        # Auto-generate barcode using product ID
        generated_barcode = f'PRD{str(pid).zfill(8)}'
        execute_db('UPDATE products SET barcode = ? WHERE id = ?', [generated_barcode, pid])
        return jsonify({'message': 'Product added', 'id': pid, 'barcode': generated_barcode}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Product could not be added'}), 400

@app.route('/api/products/<int:pid>', methods=['PUT', 'DELETE'])
@login_required
def api_product(pid):
    if request.method == 'PUT':
        data = request.get_json()
        try:
            execute_db(
                """UPDATE products SET name=?, barcode=?, category_id=?, purchase_price=?, selling_price=?,
                   stock_qty=?, min_stock=?, expiry_date=?, gst_percent=? WHERE id=?""",
                [
                    data['name'].strip(), data.get('barcode', '').strip() or None,
                    data.get('category_id') or None, float(data.get('purchase_price', 0)),
                    float(data['selling_price']), int(data.get('stock_qty', 0)),
                    int(data.get('min_stock', 10)), data.get('expiry_date') or None,
                    float(data.get('gst_percent', 0)), pid
                ]
            )
            return jsonify({'message': 'Product updated'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Barcode already exists'}), 400
    # DELETE
    try:
        # Remove related records first
        execute_db("DELETE FROM stock_logs WHERE product_id = ?", [pid])
        execute_db("DELETE FROM sale_items WHERE product_id = ?", [pid])
        execute_db("DELETE FROM purchase_items WHERE product_id = ?", [pid])
        execute_db("DELETE FROM products WHERE id = ?", [pid])
        return jsonify({'message': 'Product deleted'})
    except Exception as e:
        return jsonify({'error': f'Cannot delete product: {str(e)}'}), 400

@app.route('/api/products/barcode-image/<barcode_text>')
@login_required
def api_barcode_image(barcode_text):
    """Generate and return a barcode SVG image."""
    try:
        CODE128 = barcode.get_barcode_class('code128')
        rv = io.BytesIO()
        code = CODE128(barcode_text, writer=SVGWriter())
        code.write(rv, options={
            'module_width': 0.4,
            'module_height': 15.0,
            'font_size': 10,
            'text_distance': 5.0,
            'quiet_zone': 6.5
        })
        rv.seek(0)
        download = request.args.get('download', '')
        if download:
            return Response(
                rv.getvalue(),
                mimetype='image/svg+xml',
                headers={'Content-Disposition': f'attachment; filename=barcode_{barcode_text}.svg'}
            )
        return Response(rv.getvalue(), mimetype='image/svg+xml')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/search')
@login_required
def api_product_search():
    q = request.args.get('q', '')
    if len(q) < 1:
        return jsonify([])
    products = query_db(
        """SELECT p.*, c.name as category_name FROM products p
           LEFT JOIN categories c ON p.category_id = c.id
           WHERE (p.name LIKE ? OR p.barcode LIKE ?) AND p.stock_qty > 0
           ORDER BY p.name LIMIT 20""",
        [f'%{q}%', f'%{q}%']
    )
    return jsonify(products)


# ─── Suppliers ────────────────────────────────────────────
@app.route('/api/suppliers', methods=['GET', 'POST'])
@admin_required
def api_suppliers():
    if request.method == 'GET':
        search = request.args.get('search', '')
        if search:
            suppliers = query_db(
                "SELECT * FROM suppliers WHERE name LIKE ? OR contact LIKE ? ORDER BY name",
                [f'%{search}%', f'%{search}%']
            )
        else:
            suppliers = query_db("SELECT * FROM suppliers ORDER BY name")
        return jsonify(suppliers)
    data = request.get_json()
    if not data.get('name', '').strip():
        return jsonify({'error': 'Supplier name is required'}), 400
    sid = execute_db(
        "INSERT INTO suppliers (name, contact, address, gst_number, email) VALUES (?,?,?,?,?)",
        [data['name'].strip(), data.get('contact', ''), data.get('address', ''),
         data.get('gst_number', ''), data.get('email', '')]
    )
    return jsonify({'message': 'Supplier added', 'id': sid}), 201

@app.route('/api/suppliers/<int:sid>', methods=['PUT', 'DELETE'])
@admin_required
def api_supplier(sid):
    if request.method == 'PUT':
        data = request.get_json()
        execute_db(
            "UPDATE suppliers SET name=?, contact=?, address=?, gst_number=?, email=? WHERE id=?",
            [data['name'].strip(), data.get('contact', ''), data.get('address', ''),
             data.get('gst_number', ''), data.get('email', ''), sid]
        )
        return jsonify({'message': 'Supplier updated'})
    execute_db("DELETE FROM suppliers WHERE id = ?", [sid])
    return jsonify({'message': 'Supplier deleted'})

@app.route('/api/suppliers/<int:sid>/purchases')
@admin_required
def api_supplier_purchases(sid):
    purchases = query_db(
        "SELECT * FROM purchases WHERE supplier_id = ? ORDER BY purchase_date DESC", [sid]
    )
    return jsonify(purchases)


# ─── Purchases ────────────────────────────────────────────
@app.route('/api/purchases', methods=['GET', 'POST'])
@admin_required
def api_purchases():
    if request.method == 'GET':
        purchases = query_db(
            """SELECT p.*, s.name as supplier_name FROM purchases p
               LEFT JOIN suppliers s ON p.supplier_id = s.id
               ORDER BY p.purchase_date DESC"""
        )
        return jsonify(purchases)

    data = request.get_json()
    if not data.get('supplier_id'):
        return jsonify({'error': 'Supplier is required'}), 400
    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'At least one item is required'}), 400

    total = sum(item['qty'] * item['unit_price'] for item in data['items'])
    invoice = data.get('invoice_number', f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}")

    purchase_id = execute_db(
        "INSERT INTO purchases (supplier_id, total_amount, invoice_number) VALUES (?,?,?)",
        [data['supplier_id'], total, invoice]
    )

    for item in data['items']:
        execute_db(
            "INSERT INTO purchase_items (purchase_id, product_id, qty, unit_price) VALUES (?,?,?,?)",
            [purchase_id, item['product_id'], item['qty'], item['unit_price']]
        )
        # Update stock
        execute_db("UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?",
                    [item['qty'], item['product_id']])
        # Log stock change
        execute_db(
            "INSERT INTO stock_logs (product_id, change_qty, reason) VALUES (?,?,?)",
            [item['product_id'], item['qty'], f'Purchase #{purchase_id}']
        )

    # include shop settings in response so JS can style receipt
    settings = {}
    for row in query_db("SELECT key, value FROM settings"):
        settings[row['key']] = row['value']

    return jsonify({'message': 'Purchase recorded', 'id': purchase_id, 'invoice': invoice, 'settings': settings}), 201

@app.route('/api/purchases/<int:pid>/items')
@admin_required
def api_purchase_items(pid):
    items = query_db(
        """SELECT pi.*, p.name as product_name, p.barcode
           FROM purchase_items pi JOIN products p ON pi.product_id = p.id
           WHERE pi.purchase_id = ?""", [pid]
    )
    return jsonify(items)


# ─── Sales / Billing ─────────────────────────────────────
@app.route('/api/sales', methods=['GET', 'POST'])
@login_required
def api_sales():
    # Add customer_phone column if it doesn't exist (migration)
    try:
        execute_db("ALTER TABLE sales ADD COLUMN customer_phone TEXT")
        print("Added customer_phone column to sales table")
    except:
        pass  # Column already exists
    
    # Add customer_name column if it doesn't exist (migration)
    try:
        execute_db("ALTER TABLE sales ADD COLUMN customer_name TEXT")
        print("Added customer_name column to sales table")
    except:
        pass  # Column already exists
    
    if request.method == 'GET':
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Debug logging
        print(f"API Sales - Date From: {date_from}, Date To: {date_to}")
        print(f"Current user role: {session.get('role')}")
        print(f"Current user ID: {session.get('user_id')}")
        
        # For staff users, only show their own sales
        if session.get('role') != 'admin':
            query = """SELECT s.*, u.full_name as cashier_name, 
                       COALESCE(s.customer_name, c.name) as customer_name, 
                       COALESCE(s.customer_phone, c.phone) as customer_phone
                       FROM sales s LEFT JOIN users u ON s.user_id = u.id
                       LEFT JOIN customers c ON s.customer_id = c.id 
                       WHERE s.user_id = ?"""
            params = [session.get('user_id')]
            
            if date_from:
                query += " AND s.sale_date >= ?"
                params.append(date_from + ' 00:00:00')
                print(f"Added date_from filter: {date_from}")
            if date_to:
                query += " AND s.sale_date <= ?"
                params.append(date_to + ' 23:59:59')
                print(f"Added date_to filter: {date_to}")
        else:
            # For admin users, show all sales
            query = """SELECT s.*, u.full_name as cashier_name, 
                       COALESCE(s.customer_name, c.name) as customer_name, 
                       COALESCE(s.customer_phone, c.phone) as customer_phone
                       FROM sales s LEFT JOIN users u ON s.user_id = u.id
                       LEFT JOIN customers c ON s.customer_id = c.id WHERE 1=1"""
            params = []
            
            if date_from:
                query += " AND s.sale_date >= ?"
                params.append(date_from + ' 00:00:00')
                print(f"Added date_from filter: {date_from}")
            if date_to:
                query += " AND s.sale_date <= ?"
                params.append(date_to + ' 23:59:59')
                print(f"Added date_to filter: {date_to}")
                
        query += " ORDER BY s.sale_date DESC LIMIT 200"
        
        print(f"Final query: {query}")
        print(f"Params: {params}")
        
        result = query_db(query, params)
        print(f"Query result count: {len(result)}")
        
        # Fetch items for each sale
        for sale in result:
            items = query_db("""SELECT si.*, p.name as product_name FROM sale_items si 
                              LEFT JOIN products p ON si.product_id = p.id 
                              WHERE si.sale_id = ?""", [sale['id']])
            sale['items'] = items
        
        return jsonify(result)

    data = request.get_json()
    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'No items in cart'}), 400

    # Calculate totals
    subtotal = 0
    gst_total = 0
    for item in items:
        item_total = item['qty'] * item['unit_price']
        item_gst = item_total * item.get('gst_percent', 0) / 100
        subtotal += item_total
        gst_total += item_gst
        item['gst_amount'] = round(item_gst, 2)

    discount = float(data.get('discount', 0))
    total = round(subtotal + gst_total - discount, 2)

    # Generate invoice number
    invoice = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Get customer phone number and name
    customer_phone = None
    customer_name = None
    
    # Priority: Use the contact provided in the request (from frontend form)
    if data.get('customer_contact'):
        customer_phone = data.get('customer_contact').strip()
        customer_name = data.get('customer_name', 'Customer')
    
    # If customer_id is provided, get/verify customer details
    if data.get('customer_id'):
        customer = query_db("SELECT name, phone FROM customers WHERE id = ?", [data.get('customer_id')], one=True)
        if customer:
            customer_name = customer.get('name')
            # Only override phone if not explicitly provided in contact field
            if not data.get('customer_contact'):
                customer_phone = customer.get('phone')
    
    # Default to walk-in customer if not specified
    if not customer_name:
        customer_name = 'Walk-in Customer'

    sale_id = execute_db(
        """INSERT INTO sales (invoice_number, customer_id, user_id, subtotal, gst_amount,
           discount, total, payment_mode, customer_phone, customer_name) VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [invoice, data.get('customer_id') or None, session['user_id'],
         round(subtotal, 2), round(gst_total, 2), discount, total,
         data.get('payment_mode', 'cash'), customer_phone, customer_name]
    )

    for item in items:
        execute_db(
            "INSERT INTO sale_items (sale_id, product_id, qty, unit_price, gst_amount) VALUES (?,?,?,?,?)",
            [sale_id, item['product_id'], item['qty'], item['unit_price'], item['gst_amount']]
        )
        # Decrease stock
        execute_db("UPDATE products SET stock_qty = stock_qty - ? WHERE id = ?",
                    [item['qty'], item['product_id']])
        # Log stock change
        execute_db(
            "INSERT INTO stock_logs (product_id, change_qty, reason) VALUES (?,?,?)",
            [item['product_id'], -item['qty'], f'Sale #{sale_id}']
        )

    # Update customer loyalty points
    if data.get('customer_id'):
        points = int(total // 100)
        execute_db("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?",
                    [points, data['customer_id']])

    # Get shop settings for receipt
    settings = {}
    for row in query_db("SELECT key, value FROM settings"):
        settings[row['key']] = row['value']

    return jsonify({
        'message': 'Sale completed',
        'id': sale_id,
        'invoice_number': invoice,
        'total': total,
        'subtotal': round(subtotal, 2),
        'gst_amount': round(gst_total, 2),
        'discount': discount,
        'settings': settings
    }), 201

@app.route('/api/sales/<int:sid>/receipt')
@login_required
def api_sale_receipt(sid):
    """Generate and return a printable receipt for a sale."""
    # Get sale details
    sale = query_db("SELECT * FROM sales WHERE id = ?", [sid], one=True)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    
    # Get sale items
    items = query_db(
        """SELECT si.*, p.name as product_name, p.barcode
           FROM sale_items si JOIN products p ON si.product_id = p.id
           WHERE si.sale_id = ?""", [sid]
    )
    
    # Get customer info if available
    customer = None
    if sale['customer_id']:
        customer = query_db("SELECT * FROM customers WHERE id = ?", [sale['customer_id']], one=True)
    
    # Get shop settings
    settings = {}
    for row in query_db("SELECT key, value FROM settings"):
        settings[row['key']] = row['value']
    
    # Generate receipt HTML
    receipt_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Receipt - {sale['invoice_number']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .receipt {{ max-width: 400px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .header h2 {{ margin: 0; }}
            .header p {{ margin: 5px 0; color: #666; }}
            .info {{ margin-bottom: 20px; }}
            .info-row {{ display: flex; justify-content: space-between; margin: 5px 0; }}
            .items {{ margin-bottom: 20px; }}
            .item {{ display: flex; justify-content: space-between; margin: 5px 0; }}
            .total {{ border-top: 2px solid #000; padding-top: 10px; }}
            .total-row {{ display: flex; justify-content: space-between; margin: 5px 0; font-weight: bold; }}
            @media print {{ body {{ margin: 10px; }} }}
        </style>
    </head>
    <body>
        <div class="receipt">
            <div class="header">
                <h2>{settings.get('shop_name', 'SuperMart')}</h2>
                <p>{settings.get('address', '')}</p>
                <p>Tel: {settings.get('phone', '')}</p>
                <hr>
            </div>
            
            <div class="info">
                <div class="info-row">
                    <span>Invoice:</span>
                    <span>{sale['invoice_number']}</span>
                </div>
                <div class="info-row">
                    <span>Date:</span>
                    <span>{sale['sale_date']}</span>
                </div>
                <div class="info-row">
                    <span>Customer:</span>
                    <span>{customer['name'] if customer else 'Walk-in Customer'}</span>
                </div>
                <div class="info-row">
                    <span>Payment:</span>
                    <span>{sale.get('payment_mode', 'Cash').title()}</span>
                </div>
            </div>
            
            <div class="items">
                <h4>Items</h4>
    """
    
    for item in items:
        receipt_html += f"""
                <div class="item">
                    <span>{item['product_name']} x{item['qty']}</span>
                    <span>₹{item['qty'] * item['unit_price']:.2f}</span>
                </div>
        """
    
    receipt_html += f"""
            </div>
            
            <div class="total">
                <div class="total-row">
                    <span>Subtotal:</span>
                    <span>₹{sale['subtotal']:.2f}</span>
                </div>
                <div class="total-row">
                    <span>GST:</span>
                    <span>₹{sale['gst_amount']:.2f}</span>
                </div>
                <div class="total-row">
                    <span>Discount:</span>
                    <span>₹{sale['discount']:.2f}</span>
                </div>
                <div class="total-row" style="font-size: 18px;">
                    <span>TOTAL:</span>
                    <span>₹{sale['total']:.2f}</span>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #666;">
                <p>Thank you for your purchase!</p>
                <p>Visit again</p>
            </div>
        </div>
        
        <script>
            window.onload = function() {{
                window.print();
            }}
            window.onafterprint = function() {{
                window.close();
            }}
            // Fallback for browsers that don't support onafterprint or if cancelled
            setTimeout(function() {{
                // Only close if the print dialog is likely finished
            }}, 3000);
        </script>
    </body>
    </html>
    """
    
    return Response(receipt_html, mimetype='text/html')

@app.route('/api/sales/<int:sid>')
@login_required
def api_sale(sid):
    """Get sale details by ID"""
    sale = query_db("SELECT * FROM sales WHERE id = ?", [sid], one=True)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    return jsonify(sale)

@app.route('/api/sales/<int:sid>/items')
@login_required
def api_sale_items(sid):
    items = query_db(
        """SELECT si.*, p.name as product_name, p.barcode
           FROM sale_items si JOIN products p ON si.product_id = p.id
           WHERE si.sale_id = ?""", [sid]
    )
    sale = query_db("SELECT * FROM sales WHERE id = ?", [sid], one=True)
    settings = {}
    for row in query_db("SELECT key, value FROM settings"):
        settings[row['key']] = row['value']
    return jsonify({'items': items, 'sale': sale, 'settings': settings})



# ─── Customers ────────────────────────────────────────────
@app.route('/api/customers', methods=['GET', 'POST'])
@login_required
def api_customers():
    if request.method == 'GET':
        search = request.args.get('search', '')
        if search:
            customers = query_db(
                "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
                [f'%{search}%', f'%{search}%']
            )
        else:
            customers = query_db("SELECT * FROM customers ORDER BY name")
        return jsonify(customers)
    data = request.get_json()
    if not data.get('name', '').strip():
        return jsonify({'error': 'Customer name is required'}), 400
    try:
        cid = execute_db(
            "INSERT INTO customers (name, phone, address) VALUES (?,?,?)",
            [data['name'].strip(), data.get('phone', ''), data.get('address', '')]
        )
        return jsonify({'message': 'Customer added', 'id': cid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Phone number already exists'}), 400

@app.route('/api/customers/<int:cid>', methods=['PUT', 'DELETE'])
@login_required
def api_customer(cid):
    if request.method == 'PUT':
        data = request.get_json()
        try:
            execute_db(
                "UPDATE customers SET name=?, phone=?, address=? WHERE id=?",
                [data['name'].strip(), data.get('phone', ''), data.get('address', ''), cid]
            )
            return jsonify({'message': 'Customer updated'})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Phone number already exists'}), 400
    execute_db("DELETE FROM customers WHERE id = ?", [cid])
    return jsonify({'message': 'Customer deleted'})

@app.route('/api/customers/<int:cid>/history')
@login_required
def api_customer_history(cid):
    sales = query_db(
        "SELECT * FROM sales WHERE customer_id = ? ORDER BY sale_date DESC", [cid]
    )
    return jsonify(sales)


# ─── Reports ──────────────────────────────────────────────
@app.route('/api/reports/<report_type>')
@admin_required
def api_reports(report_type):
    date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    if report_type == 'daily_sales':
        data = query_db(
            """SELECT DATE(sale_date) as date, COUNT(*) as orders, SUM(subtotal) as subtotal,
               SUM(gst_amount) as gst, SUM(discount) as discount, SUM(total) as total
               FROM sales WHERE DATE(sale_date) BETWEEN ? AND ?
               GROUP BY DATE(sale_date) ORDER BY date DESC""",
            [date_from, date_to]
        )
    elif report_type == 'monthly_sales':
        data = query_db(
            """SELECT strftime('%Y-%m', sale_date) as month, COUNT(*) as orders,
               SUM(subtotal) as subtotal, SUM(gst_amount) as gst,
               SUM(discount) as discount, SUM(total) as total
               FROM sales GROUP BY strftime('%Y-%m', sale_date) ORDER BY month DESC"""
        )
    elif report_type == 'product_sales':
        data = query_db(
            """SELECT p.name, p.barcode, SUM(si.qty) as total_qty,
               SUM(si.qty * si.unit_price) as total_amount
               FROM sale_items si JOIN products p ON si.product_id = p.id
               JOIN sales s ON si.sale_id = s.id
               WHERE DATE(s.sale_date) BETWEEN ? AND ?
               GROUP BY si.product_id ORDER BY total_qty DESC""",
            [date_from, date_to]
        )
    elif report_type == 'profit':
        data = query_db(
            """SELECT p.name, SUM(si.qty) as qty_sold,
               SUM(si.qty * si.unit_price) as revenue,
               SUM(si.qty * p.purchase_price) as cost,
               SUM(si.qty * (si.unit_price - p.purchase_price)) as profit
               FROM sale_items si JOIN products p ON si.product_id = p.id
               JOIN sales s ON si.sale_id = s.id
               WHERE DATE(s.sale_date) BETWEEN ? AND ?
               GROUP BY si.product_id ORDER BY profit DESC""",
            [date_from, date_to]
        )
    elif report_type == 'gst':
        data = query_db(
            """SELECT DATE(sale_date) as date, SUM(subtotal) as taxable,
               SUM(gst_amount) as gst_collected, SUM(total) as total
               FROM sales WHERE DATE(sale_date) BETWEEN ? AND ?
               GROUP BY DATE(sale_date) ORDER BY date DESC""",
            [date_from, date_to]
        )
    elif report_type == 'purchase':
        data = query_db(
            """SELECT p.*, s.name as supplier_name FROM purchases p
               LEFT JOIN suppliers s ON p.supplier_id = s.id
               WHERE DATE(p.purchase_date) BETWEEN ? AND ?
               ORDER BY p.purchase_date DESC""",
            [date_from, date_to]
        )
    elif report_type == 'stock':
        data = query_db(
            """SELECT p.*, c.name as category_name,
               (p.stock_qty * p.purchase_price) as stock_value
               FROM products p LEFT JOIN categories c ON p.category_id = c.id
               ORDER BY p.name"""
        )
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    # Summary
    summary = {}
    if data:
        if report_type in ['daily_sales', 'monthly_sales']:
            summary['total_orders'] = sum(d.get('orders', 0) for d in data)
            summary['total_revenue'] = round(sum(d.get('total', 0) for d in data), 2)
            summary['total_gst'] = round(sum(d.get('gst', 0) for d in data), 2)
        elif report_type == 'profit':
            summary['total_revenue'] = round(sum(d.get('revenue', 0) for d in data), 2)
            summary['total_cost'] = round(sum(d.get('cost', 0) for d in data), 2)
            summary['total_profit'] = round(sum(d.get('profit', 0) for d in data), 2)
        elif report_type == 'stock':
            summary['total_products'] = len(data)
            summary['total_stock_value'] = round(sum(d.get('stock_value', 0) for d in data), 2)
            summary['low_stock'] = sum(1 for d in data if d['stock_qty'] <= d['min_stock'])

    return jsonify({'data': data, 'summary': summary})


# ─── Stock Management ────────────────────────────────────
@app.route('/api/stock', methods=['GET'])
@admin_required
def api_stock():
    products = query_db(
        """SELECT p.*, c.name as category_name FROM products p
           LEFT JOIN categories c ON p.category_id = c.id ORDER BY p.name"""
    )
    return jsonify(products)

@app.route('/api/stock/adjust', methods=['POST'])
@admin_required
def api_stock_adjust():
    data = request.get_json()
    product_id = data.get('product_id')
    change_qty = int(data.get('change_qty', 0))
    reason = data.get('reason', 'Manual adjustment')

    if not product_id or change_qty == 0:
        return jsonify({'error': 'Product and quantity required'}), 400

    execute_db("UPDATE products SET stock_qty = stock_qty + ? WHERE id = ?",
               [change_qty, product_id])
    execute_db(
        "INSERT INTO stock_logs (product_id, change_qty, reason) VALUES (?,?,?)",
        [product_id, change_qty, reason]
    )
    return jsonify({'message': 'Stock adjusted'})

@app.route('/api/stock/logs')
@admin_required
def api_stock_logs():
    product_id = request.args.get('product_id', '')
    query = """SELECT sl.*, p.name as product_name FROM stock_logs sl
               JOIN products p ON sl.product_id = p.id"""
    params = []
    if product_id:
        query += " WHERE sl.product_id = ?"
        params.append(product_id)
    query += " ORDER BY sl.created_at DESC LIMIT 100"
    return jsonify(query_db(query, params))


# ─── Sales statistics for admin (daily or monthly)
@app.route('/api/sales/stats')
@admin_required
@login_required
def api_sales_stats():
    period = request.args.get('period', 'daily')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    user_id = request.args.get('user_id', '')

    params = []
    where = "WHERE 1=1"
    if date_from:
        where += " AND date(s.sale_date) >= ?"
        params.append(date_from)
    if date_to:
        where += " AND date(s.sale_date) <= ?"
        params.append(date_to)
    if user_id:
        where += " AND s.user_id = ?"
        params.append(user_id)

    if period == 'monthly':
        grp = "strftime('%Y-%m', s.sale_date)"
    else:
        grp = "date(s.sale_date)"

    query = f"""
        SELECT u.full_name as cashier, p.name as product,
               {grp} as period,
               SUM(si.qty) as total_qty,
               SUM(si.qty * si.unit_price) as total_amount
        FROM sales s
        JOIN sale_items si ON s.id = si.sale_id
        JOIN products p ON si.product_id = p.id
        JOIN users u ON s.user_id = u.id
        {where}
        GROUP BY u.id, p.id, period
        ORDER BY u.full_name, period, product
    """
    stats = query_db(query, params)
    return jsonify(stats)

# ─── Expenses ─────────────────────────────────────────────
@app.route('/api/expenses', methods=['GET', 'POST'])
@admin_required
def api_expenses():
    if request.method == 'GET':
        month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        expenses = query_db(
            "SELECT * FROM expenses WHERE strftime('%Y-%m', expense_date) = ? ORDER BY expense_date DESC",
            [month]
        )
        summary = query_db(
            """SELECT category, SUM(amount) as total FROM expenses
               WHERE strftime('%Y-%m', expense_date) = ? GROUP BY category""",
            [month]
        )
        total = sum(s['total'] for s in summary) if summary else 0
        return jsonify({'expenses': expenses, 'summary': summary, 'total': total})

    data = request.get_json()
    if not data.get('category') or not data.get('amount'):
        return jsonify({'error': 'Category and amount are required'}), 400
    eid = execute_db(
        "INSERT INTO expenses (category, description, amount, expense_date) VALUES (?,?,?,?)",
        [data['category'], data.get('description', ''), float(data['amount']),
         data.get('expense_date', datetime.now().strftime('%Y-%m-%d'))]
    )
    return jsonify({'message': 'Expense added', 'id': eid}), 201

@app.route('/api/expenses/<int:eid>', methods=['PUT', 'DELETE'])
@admin_required
def api_expense(eid):
    if request.method == 'PUT':
        data = request.get_json()
        execute_db(
            "UPDATE expenses SET category=?, description=?, amount=?, expense_date=? WHERE id=?",
            [data['category'], data.get('description', ''), float(data['amount']),
             data.get('expense_date', ''), eid]
        )
        return jsonify({'message': 'Expense updated'})
    execute_db("DELETE FROM expenses WHERE id = ?", [eid])
    return jsonify({'message': 'Expense deleted'})


# ─── User Management (Admin Only) ────────────────────────
@app.route('/api/users', methods=['GET', 'POST'])
@admin_required
def api_users():
    if request.method == 'GET':
        users = query_db(
            "SELECT id, username, full_name, role, phone, email, is_active, created_at FROM users ORDER BY full_name"
        )
        return jsonify(users)
    data = request.get_json()
    required = ['username', 'password', 'full_name', 'role']
    for field in required:
        if not data.get(field, '').strip():
            return jsonify({'error': f'{field} is required'}), 400
    if data['role'] not in ('admin', 'cashier'):
        return jsonify({'error': 'Invalid role'}), 400
    try:
        uid = execute_db(
            "INSERT INTO users (username, password_hash, full_name, role, phone, email) VALUES (?,?,?,?,?,?)",
            [data['username'].strip(), generate_password_hash(data['password']),
             data['full_name'].strip(), data['role'],
             data.get('phone', ''), data.get('email', '')]
        )
        return jsonify({'message': 'User created', 'id': uid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/api/users/<int:uid>', methods=['PUT', 'DELETE'])
@admin_required
def api_user(uid):
    if request.method == 'DELETE':
        # Prevent deletion of the current logged-in admin
        if uid == session.get('user_id'):
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Delete the user directly (faster - no need to check existence first)
        cursor = get_db().cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", [uid])
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
            
        get_db().commit()
        return jsonify({'message': 'User deleted successfully'})
    
    data = request.get_json()
    if data.get('password'):
        execute_db("UPDATE users SET password_hash = ? WHERE id = ?",
                    [generate_password_hash(data['password']), uid])
    execute_db(
        "UPDATE users SET full_name=?, role=?, phone=?, email=?, is_active=? WHERE id=?",
        [data.get('full_name', ''), data.get('role', 'cashier'),
         data.get('phone', ''), data.get('email', ''),
         1 if data.get('is_active', True) else 0, uid]
    )
    return jsonify({'message': 'User updated'})


# ─── Settings ─────────────────────────────────────────────
@app.route('/api/settings', methods=['GET', 'POST'])
@admin_required
def api_settings():
    if request.method == 'GET':
        settings = {}
        for row in query_db("SELECT key, value FROM settings"):
            settings[row['key']] = row['value']
        return jsonify(settings)
    data = request.get_json()
    for key, value in data.items():
        execute_db("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", [key, value])
    return jsonify({'message': 'Settings saved'})

@app.route('/api/settings/logo', methods=['POST'])
@admin_required
def api_upload_logo():
    if 'logo' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['logo']
    if file.filename:
        filename = 'shop_logo.png'
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        execute_db("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ['logo_path', f'/static/uploads/{filename}'])
        return jsonify({'message': 'Logo uploaded', 'path': f'/static/uploads/{filename}'})
    return jsonify({'error': 'No file selected'}), 400


# ─── Backup & Restore ────────────────────────────────────
@app.route('/api/backup')
@admin_required
def api_backup():
    backup_path = os.path.join(config.BASE_DIR, 'backup',
                               f"supermarket_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(config.DATABASE, backup_path)
    return send_file(backup_path, as_attachment=True)

@app.route('/api/restore', methods=['POST'])
@admin_required
def api_restore():
    if 'backup' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['backup']
    if file.filename:
        file.save(config.DATABASE)
        return jsonify({'message': 'Database restored successfully'})
    return jsonify({'error': 'No file selected'}), 400


# ─── Initialize and Run ──────────────────────────────────
if __name__ == '__main__':
    if not os.path.exists(config.DATABASE):
        init_db()
        print("Database initialized. Run 'python seed.py' to add sample data.")
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000)
