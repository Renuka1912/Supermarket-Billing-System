# Billing System Updates - Customer Contact & Sales History Integration

## Overview
Implemented a complete flow to capture customer contact information during billing and display it in the sales history.

## Changes Made

### 1. Frontend - Billing Page (`templates/billing.html`)
**Updated Customer Section:**
- Changed the customer input section header to "Customer Information" (was "Customer (Optional)")
- Added a prominent yellow-bordered contact number field with "Required" indicator
- Improved UI by styling the selected customer info with green background and checkmark
- Reorganized form layout for better UX flow:
  1. Search for existing customer
  2. Auto-populated contact field
  3. Selected customer confirmation display

### 2. Frontend - Billing JavaScript (`static/js/billing.js`)

**Updated `selectCustomer()` Function:**
- When a customer is selected from the list, their phone number is now **automatically populated** in the contact field (instead of clearing it)
- This enables staff to quickly confirm or override the contact number for the billing
- Display is updated to show the selected customer with their contact

**Updated `clearCustomer()` Function:**
- Now clears all customer-related fields:
  - Customer ID
  - Customer search box
  - Contact input field
  - Selected customer info display
- Provides a clean slate for the next sale

**Updated `completeSale()` Function:**
- Added **validation** to require contact number before completing sale
- Displays warning toast if contact number is missing
- This ensures every sale record has customer contact information
- Contact number is sent to backend as `customer_contact` in the request

**Updated `generateSaleReceipt()` Function:**
- Now includes customer name and contact number on the printed receipt
- Customer info displayed in a separated section between header and item list
- Format: "Customer: [Name]" and "Contact: [Phone]"

### 3. Backend - Flask API (`app.py`)

**POST /api/sales Endpoint Updates:**
- Added migration to create `customer_name` column in sales table (if not exists)
- Updated INSERT logic to store both `customer_phone` and `customer_name` in sales table
- Improved customer data handling with priority system:
  1. Use contact from frontend request (most recent/accurate)
  2. Fall back to database if pre-selected customer
  3. Default to "Walk-in Customer" if none provided

**GET /api/sales Endpoint Updates:**
- Updated SELECT queries to use `COALESCE()` for robust data retrieval:
  - `COALESCE(s.customer_name, c.name)` - Uses stored customer name, falls back to customers table
  - `COALESCE(s.customer_phone, c.phone)` - Uses stored phone, falls back to customers table
- Ensures both admin and staff users see consistent customer information

### 4. Sales History Template (`templates/sales_history.html`)
- Already had "Contact Number" column in table header
- Already displays customer name from database
- Already displays customer phone number
- **No changes needed** - template was already aligned with the new data structure

## Data Flow

### For Registered Customers:
1. Staff searches for customer by name/phone on billing page
2. Customer is selected from dropdown
3. Customer's phone number is **auto-populated** in the contact field
4. Staff can view/edit if needed
5. Upon billing completion:
   - `customer_id` is stored (links to customers table)
   - `customer_phone` is stored (use-case: registered customers may update phone)
   - `customer_name` is stored (for historical records)

### For Walk-in Customers:
1. No customer selected
2. Staff manually enters contact number in the contact field
3. Upon billing completion:
   - `customer_id` remains NULL (no customer record created)
   - `customer_phone` is stored (contact info for sales record)
   - `customer_name` defaults to "Walk-in Customer"

### Sales History Display:
1. Customer name displayed in table from `sales.customer_name`
2. Customer phone displayed in dedicated "Contact Number" column
3. Receipt/details modal shows both name and contact
4. Consistent data across all views

## Database Migrations

### New Columns Created:
1. **`sales.customer_phone`** - Stores contact number for every sale
2. **`sales.customer_name`** - Stores customer name for historical records

These are created automatically when the /api/sales endpoint is first accessed.

## Benefits

✅ **Complete Data Capture:** Every sale now has customer contact information
✅ **Better UX:** Auto-population reduces manual entry
✅ **Walk-in Support:** Non-registered customers can still be tracked by phone
✅ **Historical Records:** Customer info is stored permanently with the sale
✅ **Easy Lookup:** Sales can be searched/filtered by customer and contact
✅ **Receipt Quality:** Receipts now include customer identification
✅ **Reporting:** Better analytics possible with customer contact data

## Testing Checklist

- [ ] Registered customer selection auto-populates phone
- [ ] Phone field can be edited before completing sale
- [ ] Walk-in customer sales work without selection
- [ ] Contact number is required before completing sale
- [ ] Sales record appears in history with customer name and phone
- [ ] Receipt includes customer information
- [ ] Date filters in sales history work correctly
- [ ] Admin can view all staff member's sales with customer info

## Files Modified

1. `templates/billing.html` - Customer section UI
2. `static/js/billing.js` - Client-side logic
3. `app.py` - Backend API logic
4. `templates/sales_history.html` - (No changes, already compatible)

## Notes

- Contact number entry is now **required** for all sales (walk-in or registered)
- Existing sales records without customer_name/customer_phone will have NULL values
- NULL values are handled gracefully with fallbacks in SQL queries
- The system is backward compatible with existing sales data
