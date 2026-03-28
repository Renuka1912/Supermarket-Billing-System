# Technical Implementation Guide

## Database Schema Changes

### New Columns Added to `sales` Table

```sql
ALTER TABLE sales ADD COLUMN customer_phone TEXT;
ALTER TABLE sales ADD COLUMN customer_name TEXT;
```

**Note:** These migrations run automatically on first API call. No manual SQL execution needed.

### Updated Schema

```sql
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE,
    customer_id INTEGER REFERENCES customers(id),
    user_id INTEGER REFERENCES users(id),
    subtotal REAL DEFAULT 0,
    gst_amount REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    total REAL DEFAULT 0,
    payment_mode TEXT DEFAULT 'cash',
    customer_phone TEXT,           -- NEW: Contact number
    customer_name TEXT,            -- NEW: Customer name for records
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### POST /api/sales - Create Sale

**Request Body:**
```json
{
    "items": [
        {
            "product_id": 1,
            "qty": 2,
            "unit_price": 50.00,
            "gst_percent": 5
        }
    ],
    "customer_id": 5,                    // NULL for walk-in
    "customer_name": "Renuka",           // NEW: Stored in sales table
    "customer_contact": "9876543210",    // NEW: Contact for this sale
    "discount": 0.00,
    "payment_mode": "cash"
}
```

**Response:**
```json
{
    "message": "Sale completed",
    "id": 42,
    "invoice_number": "INV-20260304215959",
    "total": 265.50,
    "subtotal": 250.00,
    "gst_amount": 15.50,
    "discount": 0,
    "settings": { ... }
}
```

**Backend Logic (app.py):**
```python
# Priority: Use contact from request (most authoritative)
if data.get('customer_contact'):
    customer_phone = data.get('customer_contact').strip()
    customer_name = data.get('customer_name', 'Customer')

# If customer_id is provided, get/verify customer details
if data.get('customer_id'):
    customer = query_db("SELECT name, phone FROM customers WHERE id = ?", 
                        [data.get('customer_id')], one=True)
    if customer:
        customer_name = customer.get('name')
        # Only override phone if not explicitly provided
        if not data.get('customer_contact'):
            customer_phone = customer.get('phone')

# Default to walk-in customer
if not customer_name:
    customer_name = 'Walk-in Customer'

# Insert with both customer_phone and customer_name
execute_db(
    """INSERT INTO sales (..., customer_phone, customer_name) 
       VALUES (..., ?, ?)""",
    [..., customer_phone, customer_name]
)
```

### GET /api/sales - Retrieve Sales

**Query Parameters:**
```
?date_from=2026-03-01&date_to=2026-03-04
```

**Response:**
```json
[
    {
        "id": 42,
        "invoice_number": "INV-20260304215959",
        "customer_id": 5,
        "customer_name": "Renuka",          // NEW: From sales table
        "customer_phone": "9876543210",     // NEW: From sales table
        "cashier_name": "John Doe",
        "subtotal": 250.00,
        "gst_amount": 15.50,
        "discount": 0,
        "total": 265.50,
        "payment_mode": "cash",
        "sale_date": "2026-03-04 21:59:14"
    }
]
```

**Backend Query (app.py):**
```python
# Uses COALESCE for robust fallback
query = """
    SELECT s.*, u.full_name as cashier_name, 
           COALESCE(s.customer_name, c.name) as customer_name, 
           COALESCE(s.customer_phone, c.phone) as customer_phone
    FROM sales s 
    LEFT JOIN users u ON s.user_id = u.id
    LEFT JOIN customers c ON s.customer_id = c.id 
    WHERE s.user_id = ? AND s.sale_date >= ? AND s.sale_date <= ?
    ORDER BY s.sale_date DESC
"""
```

---

## Frontend Implementation

### HTML Changes (billing.html)

**Customer Section:**
```html
<div class="card mb-2" style="overflow: visible;">
    <div class="card-title mb-1">
        <i class="fas fa-user"></i> Customer Information
    </div>
    
    <!-- Search Input -->
    <input type="text" class="form-control" id="customerSearch"
        placeholder="Search customer by name/phone (or leave empty for walk-in)..."
        oninput="searchCustomers()" autocomplete="off">
    
    <!-- Contact Input - REQUIRED -->
    <input type="text" class="form-control" id="customerContactInput"
        placeholder="Customer contact number (important for sales record)..."
        autocomplete="off" style="border: 2px solid #ffc107;">
    
    <!-- Selected Customer Display -->
    <div id="selectedCustomerInfo" style="display:none; background:#e8f5e9;">
        <div id="customerName"></div>
        <div id="customerPhone"></div>
        <button onclick="clearCustomer()">Clear</button>
    </div>
</div>
```

### JavaScript Changes (billing.js)

**selectCustomer Function:**
```javascript
function selectCustomer(id, name, phone) {
    document.getElementById('selectedCustomerId').value = id;
    document.getElementById('customerName').textContent = name;
    
    // Auto-populate contact field
    document.getElementById('customerContactInput').value = phone || '';
    
    // Display confirmation
    document.getElementById('selectedCustomerInfo').style.display = 'block';
    document.getElementById('customerSearch').value = name;
    document.getElementById('customerResults').classList.remove('active');
}
```

**completeSale Function with Validation:**
```javascript
async function completeSale() {
    // VALIDATION: Contact number required
    const customerContact = document.getElementById('customerContactInput')
        .value.trim();
    
    if (!customerContact) {
        showToast('Please enter customer contact number', 'warning');
        return;
    }
    
    // Prepare request data
    const data = {
        items: [...],
        customer_id: customerId || null,
        customer_name: customerName || 'Walk-in Customer',
        customer_contact: customerContact,  // Sent to backend
        payment_mode: paymentMode
    };
    
    // API call
    const result = await apiCall('/api/sales', { 
        method: 'POST', 
        body: data 
    });
}
```

**Receipt Generation:**
```javascript
function generateSaleReceipt(result, saleData) {
    // Include customer section in receipt
    const receiptHTML = `
        <div class="receipt-header">
            <h2>${settings.shop_name}</h2>
        </div>
        
        <!-- NEW: Customer info section -->
        <div style="border-bottom: 1px solid #000; padding: 3mm 0;">
            <p><strong>Customer:</strong> ${saleData.customer_name}</p>
            ${saleData.customer_contact ? 
                `<p><strong>Contact:</strong> ${saleData.customer_contact}</p>` 
                : ''}
        </div>
        
        <!-- Items table -->
        <table>...</table>
        
        <!-- Totals -->
        <div>...</div>
    `;
}
```

---

## Data Flow Diagram (Technical)

```
Frontend (billing.html/billing.js)
         │
         ├─ User searches customer
         ├─ User selects from dropdown
         ├─ JavaScript triggers selectCustomer()
         │  └─ Auto-populates phone in contactInput
         │
         ├─ User reviews/edits phone number
         ├─ User clicks "Complete Sale & Print"
         ├─ JavaScript validates contact field
         │  └─ Shows error if empty
         │
         ├─ JavaScript calls completeSale()
         │  └─ Prepares JSON request with:
         │     - customer_id (or null)
         │     - customer_name
         │     - customer_contact ← IMPORTANT
         │     - items, payment_mode, etc.
         │
         └─ POST /api/sales with JSON
                    │
                    ▼
Backend (app.py)
         │
         ├─ Receives POST request
         ├─ Migrations run (if needed)
         │  ├─ ADD COLUMN customer_phone
         │  └─ ADD COLUMN customer_name
         │
         ├─ Get customer_contact from request
         ├─ If customer_id exists, get customer from DB
         ├─ Determine final customer_name and customer_phone
         │
         ├─ INSERT INTO sales
         │  ├─ invoice_number: generated
         │  ├─ customer_id: from request or NULL
         │  ├─ customer_name: determined from logic
         │  ├─ customer_phone: from request or DB
         │  ├─ other fields: subtotal, gst, total, etc.
         │
         ├─ INSERT INTO sale_items (for each item)
         ├─ UPDATE products stock
         ├─ INSERT INTO stock_logs
         │
         └─ Return JSON response
                    │
                    ▼
Frontend (billing.js)
         │
         ├─ Receive response
         ├─ Generate receipt HTML
         ├─ Include customer and contact info
         ├─ Trigger window.print()
         ├─ Clear cart and form
         └─ Show success message
                    │
                    ▼
Sales History (sales_history.html)
         │
         ├─ User navigates to Sales History
         ├─ JavaScript calls GET /api/sales
         ├─ Backend returns sales with customer_name and customer_phone
         ├─ Template loops through results:
         │  └─ Display in table rows with name and contact
         │
         └─ User can click "View" to see full details
                    │
                    ▼
Modal Details View
         │
         ├─ Shows complete sale information
         ├─ Displays customer name and contact
         └─ Lists all items with prices and GST
```

---

## Error Handling

### Client-Side Validation (billing.js)

```javascript
async function completeSale() {
    const contact = document.getElementById('customerContactInput').value.trim();
    
    if (!contact) {
        showToast('Please enter customer contact number (or select from existing customers)', 'warning');
        return;  // Exit early
    }
    
    // ... rest of function
}
```

### User Feedback

```javascript
showToast('Please enter customer contact number', 'warning');
// Displays: Yellow banner with warning icon
```

---

## Backward Compatibility

### Existing Sales (Before Update)

Sales created before this update will have:
- `customer_phone`: NULL
- `customer_name`: NULL

### Query Handling

```sql
SELECT s.*, 
       COALESCE(s.customer_name, c.name) as customer_name,
       COALESCE(s.customer_phone, c.phone) as customer_phone
```

- `COALESCE()` returns first non-NULL value
- If `s.customer_name` is NULL, falls back to `c.name`
- Gracefully handles pre-update sales

### Display

```javascript
// In sales history template
<td>${sale.customer_name || 'Walk-in Customer'}</td>
<td>${sale.customer_phone || 'N/A'}</td>
```

- Shows "Walk-in Customer" if no name
- Shows "N/A" if no phone

---

## Testing Checklist (Dev)

```javascript
// Test 1: Registered customer flow
POST /api/sales {
    customer_id: 5,
    customer_name: "Renuka",
    customer_contact: "9876543210"
}
// Expected: Both customer_name and customer_phone saved

// Test 2: Walk-in customer flow
POST /api/sales {
    customer_id: null,
    customer_name: "Walk-in Customer",
    customer_contact: "8765432109"
}
// Expected: customer_id=NULL, contact saved

// Test 3: Missing contact
POST /api/sales {
    customer_id: 5,
    customer_contact: ""  // Empty
}
// Expected: Validation error in frontend

// Test 4: Retrieve with COALESCE
GET /api/sales?date_from=2026-03-01&date_to=2026-03-04
// Expected: Returns sales with populated customer_name and customer_phone

// Test 5: Receipt includes contact
POST /api/sales {
    customer_name: "Renuka",
    customer_contact: "9876543210"
}
// Expected: Receipt JSON includes these fields
```

---

## Performance Considerations

- `customer_phone` and `customer_name` are simple TEXT fields
- No indexes needed (not frequently filtered)
- `COALESCE()` in SELECT is minimal overhead
- Join with customers table still efficient

---

## Security Notes

- Validate contact number format on frontend (optional)
- Backend doesn't validate format (accepts any string)
- Phone numbers stored in plain text (as per existing design)
- No PII encryption applied

---

## Future Enhancements

1. **Phone Validation:** Regex to validate Indian phone format
2. **Contact History:** Track multiple phone numbers per customer
3. **SMS Integration:** Send receipts/notifications to customer contact
4. **CRM Integration:** Sync customer contact with external CRM
5. **Analytics:** Reports by most common contact numbers

---

**Last Updated:** 2026-03-04
**Version:** 1.0

