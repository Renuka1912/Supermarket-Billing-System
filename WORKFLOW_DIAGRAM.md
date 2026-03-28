# Customer Billing Flow Diagram

## Complete Sales Transaction Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              STAFF BILLING PAGE - SALES MODE                   │
└─────────────────────────────────────────────────────────────────┘

         ┌──────────────────────────┐
         │   Add Products to Cart   │
         │  (Search/Scan Barcode)   │
         └──────────────────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
    ┌────┤  Customer Lookup (OPT)   │◄─────┐
    │    │  - Search by name/phone  │      │
    │    │  - Show all customers    │      │
    │    └──────────────────────────┘      │
    │                 │                     │
    │   ┌─────────────┴─────────────┐      │
    │   │                           │      │
    │   ▼ (Select Customer)         │      │
    │  ✓ Auto-populate Contact    Exit   (Skip)
    │   │   - Get from customer DB  │      │
    │   │   - Allow edit/override   │      │
    │   │                          │      │
    │   └─────────────┬────────────┘      │
    │                 │                    │
    ├─────────────────┴────────────────────┤
    │                                       │
    ▼                                       ▼
┌───────────────────────────┐  ┌──────────────────────────┐
│ REGISTERED CUSTOMER MODE  │  │   WALK-IN CUSTOMER MODE  │
├───────────────────────────┤  ├──────────────────────────┤
│ • Customer ID: [123]      │  │ • Customer ID: NULL      │
│ • Name: [Auto-filled]     │  │ • Name: Walk-in Customer │
│ • Contact: [Auto-filled]  │  │ • Contact: [Manual Entry]│
│   (editable)              │  │   (REQUIRED)             │
├───────────────────────────┤  ├──────────────────────────┤
│ Select Payment Mode       │  │ Select Payment Mode      │
│ (Cash/Card/UPI)           │  │ (Cash/Card/UPI)          │
└───────────┬───────────────┘  └──────────────┬───────────┘
            │                                 │
            └─────────────────┬───────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │ VALIDATION REQUIRED: │
                    │ Contact Number OK? ✓ │
                    └──────────────────────┘
                      │              │
                ┌─────┘              └─────┐
                │ YES                      │ NO
                ▼                          ▼
         ┌─────────────┐         [Show Error Toast]
         │  Complete   │         "Enter contact number"
         │   Transaction
         └──────┬──────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ INSERT INTO sales TABLE:      │
    ├───────────────────────────────┤
    │ • invoice_number: INV-...     │
    │ • customer_id: [123 or NULL]  │
    │ • customer_name: [Name]       │
    │ • customer_phone: [Contact]   │
    │ • subtotal, gst, total        │
    │ • payment_mode                │
    │ • user_id (cashier)           │
    │ • sale_date: CURRENT_TIME     │
    └───────────┬───────────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ INSERT INTO sale_items:       │
    │ (Products from cart)          │
    └───────────┬───────────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ UPDATE products stock:        │
    │ (Decrease quantity)           │
    └───────────┬───────────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ LOG stock change              │
    └───────────┬───────────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ IF registered customer:       │
    │ Update loyalty points         │
    └───────────┬───────────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ GENERATE RECEIPT:             │
    │ - Shop name & address         │
    │ - Invoice number              │
    │ - Customer: [Name]            │
    │ - Contact: [Phone] ← NEW!     │
    │ - Item details                │
    │ - Total with GST              │
    │ - Payment mode                │
    └───────────┬───────────────────┘
                │
                ▼
    ┌───────────────────────────────┐
    │ PRINT RECEIPT                 │
    │ CLEAR CART & FORM             │
    └───────────────────────────────┘
```

## Sales History Display

```
┌─────────────────────────────────────────────────────┐
│            SALES HISTORY PAGE                       │
├──────┬────────┬─────────────┬──────────┬────────────┤
│ Inv  │ Date   │ Customer    │ Contact  │ Amount     │
├──────┼────────┼─────────────┼──────────┼────────────┤
│ INV- │ 04-Mar │ Renuka      │ 9876543  │ ₹276.50    │
│ 2026 │ 21:41  │ 📞 9876543  │ 210 (UPI)│            │
├──────┼────────┼─────────────┼──────────┼────────────┤
│ INV- │ 04-Mar │ Walk-in     │ 8765432  │ ₹62.72     │
│ 2026 │ 17:54  │ 📞 8765432  │ 110 (CASH)           │
├──────┼────────┼─────────────┼──────────┼────────────┤
│ INV- │ 03-Mar │ Pooja       │ 9988776  │ ₹40.00     │
│ 2026 │ 09:31  │ 📞 9988776  │ 655 (CASH)           │
└──────┴────────┴─────────────┴──────────┴────────────┘

Click "View" to see:
- Full item list
- Customer: [Name]
- Contact: [Phone]
- All transaction details
```

## Key Data Points Stored

```
For Each Sale:
│
├─ invoice_number      (e.g., "INV-20260304215959")
├─ customer_id         (e.g., 5 or NULL for walk-in)
├─ customer_name       (e.g., "Renuka" or "Walk-in Customer")
├─ customer_phone      (e.g., "9876543210") ← KEY ADDITION
├─ user_id             (cashier who did the sale)
├─ subtotal, gst, discount, total
├─ payment_mode        (cash/card/upi)
└─ sale_date           (timestamp)

Connected:
└─ sale_items
   ├─ product_id
   ├─ quantity
   ├─ unit_price
   └─ gst_amount
```
