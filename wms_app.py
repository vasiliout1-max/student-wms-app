import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, date   # χρειαζόμαστε και date

# Ρύθμιση σελίδας
st.set_page_config(
    page_title="WMS Μαθητών",
    page_icon="📦",
    layout="wide"
)

class StudentWMS:
    def __init__(self):
        self.init_master_db()
    
    def init_master_db(self):
        os.makedirs('student_dbs', exist_ok=True)
        conn = sqlite3.connect('master.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT,
                class_name TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def register_student(self, student_id, full_name, class_name):
        try:
            conn = sqlite3.connect('master.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO students (student_id, full_name, class_name) VALUES (?, ?, ?)",
                (student_id, full_name, class_name)
            )
            conn.commit()
            conn.close()
            
            # Δημιουργία προσωπικής βάσης
            self.create_student_database(student_id)
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            st.error(f"Σφάλμα: {e}")
            return False
    
    def create_student_database(self, student_id):
        conn = sqlite3.connect(f'student_dbs/{student_id}.db')
        cursor = conn.cursor()
        
        # Προϊόντα
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                barcode TEXT,
                quantity INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Θέσεις Αποθήκης
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_code TEXT UNIQUE NOT NULL,
                zone TEXT,
                description TEXT
            )
        ''')
        
        # Συναλλαγές
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                product_id INTEGER,
                location_id INTEGER,
                quantity INTEGER,
                notes TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Πίνακας παραστατικών (Τιμολόγιο - Δελτίο Αποστολής)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_number TEXT,
                doc_type TEXT,
                doc_date TEXT,
                customer_name TEXT,
                afm TEXT,
                address TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Γραμμές παραστατικών
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')

        # Προμηθευτές
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                afm TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_student_db_connection(self, student_id):
        return sqlite3.connect(f'student_dbs/{student_id}.db')

def main():
    st.title("🎓 Εκπαιδευτικό WMS για Μαθητές")
    
    # Αρχικοποίηση συστήματος
    if 'wms' not in st.session_state:
        st.session_state.wms = StudentWMS()
    
    # Σύνδεση/Εγγραφή
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_register()
    else:
        show_main_app()

def show_login_register():
    """Οθόνη σύνδεσης/εγγραφής"""
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Εγγραφή Νέου Μαθητή")
        with st.form("register_form"):
            student_id = st.text_input("Student ID* (π.χ. m2023001)")
            full_name = st.text_input("Ονοματεπώνυμο*")
            class_name = st.text_input("Τάξη* (π.χ. Β1)")
            
            submitted = st.form_submit_button("📋 Εγγραφή Μαθητή")
            if submitted:
                if student_id and full_name and class_name:
                    if st.session_state.wms.register_student(student_id, full_name, class_name):
                        st.success(f"✅ Εγγράφηκες επιτυχώς! ID: {student_id}")
                    else:
                        st.error("❌ Το Student ID υπάρχει ήδη")
                else:
                    st.error("❌ Συμπλήρωσε όλα τα πεδία")
    
    with col2:
        st.subheader("🔐 Σύνδεση Μαθητή")
        with st.form("login_form"):
            student_id = st.text_input("Student ID")
            
            submitted = st.form_submit_button("🚀 Σύνδεση")
            if submitted:
                if os.path.exists(f'student_dbs/{student_id}.db'):
                    st.session_state.logged_in = True
                    st.session_state.student_id = student_id
                    st.rerun()
                else:
                    st.error("❌ Δεν βρέθηκε μαθητής με αυτό το ID")

def show_main_app():
    """Κύρια εφαρμογή αφού συνδεθεί ο μαθητής"""
    student_id = st.session_state.student_id
    student_db = st.session_state.wms.get_student_db_connection(student_id)
    
    st.success(f"✅ Συνδεμένος ως: **{student_id}**")
    
    if st.button("🚪 Αποσύνδεση"):
        st.session_state.logged_in = False
        st.session_state.student_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Menu
    menu = st.selectbox(
        "Επιλογή Ενότητας",
        [
            "🏠 Αρχική",
            "📋 Προϊόντα",
            "📍 Θέσεις Αποθήκης",
            "🔄 Συναλλαγές",
            "🏭 Προμηθευτές",
            "📄 Τιμολόγια - Δ.Α.",
            "📊 Αποθήκη"
        ]
    )

    if menu == "🏠 Αρχική":
        show_dashboard(student_db, student_id)
    elif menu == "📋 Προϊόντα":
        manage_products(student_db)
    elif menu == "📍 Θέσεις Αποθήκης":
        manage_locations(student_db)
    elif menu == "🔄 Συναλλαγές":
        manage_transactions(student_db)
    elif menu == "🏭 Προμηθευτές":
        manage_suppliers(student_db)
    elif menu == "📄 Τιμολόγια - Δ.Α.":
        manage_invoices(student_db)
    elif menu == "📊 Αποθήκη":
        show_inventory(student_db)


def show_dashboard(db, student_id):
    st.header("🏠 Πίνακας Ελέγχου")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        products_count = pd.read_sql("SELECT COUNT(*) as count FROM products", db)['count'].iloc[0]
        st.metric("📦 Προϊόντα", products_count)
    
    with col2:
        locations_count = pd.read_sql("SELECT COUNT(*) as count FROM locations", db)['count'].iloc[0]
        st.metric("📍 Θέσεις", locations_count)
    
    with col3:
        total_qty = pd.read_sql("SELECT SUM(quantity) as total FROM products", db)['total'].iloc[0] or 0
        st.metric("📊 Συνολικό Απόθεμα", total_qty)
    
    st.markdown("---")
    st.subheader("Πρόσφατα Προϊόντα")
    products = pd.read_sql("SELECT * FROM products ORDER BY created_date DESC LIMIT 5", db)
    if not products.empty:
        st.dataframe(products)
    else:
        st.info("Δεν υπάρχουν προϊόντα ακόμη. Πρόσθεσε κάποια από το μενού 'Προϊόντα'")

def manage_products(db):
    st.header("📋 Διαχείριση Προϊόντων")
    
    tab1, tab2 = st.tabs(["➕ Προσθήκη Προϊόντος", "📋 Λίστα Προϊόντων"])
    
    with tab1:
        with st.form("add_product"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Όνομα Προϊόντος*")
                category = st.selectbox("Κατηγορία", ["ΗΛΕΚΤΡΟΝΙΚΑ", "ΒΙΒΛΙΑ", "ΕΠΙΠΛΑ", "ΕΠΙΤΗΔΕΥΜΑΤΑ", "ΑΛΛΟ"])
            with col2:
                barcode = st.text_input("Barcode")
                quantity = st.number_input("Ποσότητα", min_value=0, value=0)
            
            description = st.text_area("Περιγραφή")
            
            if st.form_submit_button("💾 Αποθήκευση Προϊόντος"):
                if name:
                    cursor = db.cursor()
                    cursor.execute(
                        "INSERT INTO products (name, description, category, barcode, quantity) VALUES (?, ?, ?, ?, ?)",
                        (name, description, category, barcode, quantity)
                    )
                    db.commit()
                    st.success("✅ Προϊόν προστέθηκε επιτυχώς!")
                else:
                    st.error("❌ Το όνομα προϊόντος είναι υποχρεωτικό")
    
    with tab2:
        products = pd.read_sql("SELECT * FROM products ORDER BY name", db)
        if not products.empty:
            st.dataframe(products)
            
            # Διαγραφή προϊόντος
            st.subheader("Διαγραφή Προϊόντος")
            product_names = products['name'].tolist()
            delete_product = st.selectbox("Επιλογή προϊόντος για διαγραφή", product_names)
            if st.button("🗑️ Διαγραφή"):
                cursor = db.cursor()
                cursor.execute("DELETE FROM products WHERE name = ?", (delete_product,))
                db.commit()
                st.success("✅ Προϊόν διαγράφηκε!")
                st.rerun()
        else:
            st.info("Δεν υπάρχουν προϊόντα ακόμη")

def manage_locations(db):
    st.header("📍 Διαχείριση Θέσεων Αποθήκης")
    
    tab1, tab2 = st.tabs(["➕ Προσθήκη Θέσης", "📋 Λίστα Θέσεων"])
    
    with tab1:
        with st.form("add_location"):
            col1, col2 = st.columns(2)
            with col1:
                location_code = st.text_input("Κωδικός Θέσης* (π.χ. A-01-01)")
                zone = st.selectbox("Ζώνη", ["Α", "Β", "Γ", "Δ"])
            with col2:
                description = st.text_area("Περιγραφή Θέσης")
            
            if st.form_submit_button("💾 Αποθήκευση Θέσης"):
                if location_code:
                    try:
                        cursor = db.cursor()
                        cursor.execute(
                            "INSERT INTO locations (location_code, zone, description) VALUES (?, ?, ?)",
                            (location_code, zone, description)
                        )
                        db.commit()
                        st.success("✅ Θέση προστέθηκε επιτυχώς!")
                    except sqlite3.IntegrityError:
                        st.error("❌ Ο κωδικός θέσης υπάρχει ήδη")
                else:
                    st.error("❌ Ο κωδικός θέσης είναι υποχρεωτικός")
    
    with tab2:
        locations = pd.read_sql("SELECT * FROM locations ORDER BY location_code", db)
        if not locations.empty:
            st.dataframe(locations)
        else:
            st.info("Δεν υπάρχουν θέσεις ακόμη")

def manage_transactions(db):
    st.header("🔄 Διαχείριση Συναλλαγών")
    st.info("🚧 Αυτή η ενότητα θα προστεθεί σύντομα...")
    
    # Εδώ θα προστεθεί κώδικας για συναλλαγές
    st.write("Εισαγωγές, Εξαγωγές, Μεταφορές")

def manage_suppliers(db):
    st.header("🏭 Διαχείριση Προμηθευτών")
    
    tab1, tab2 = st.tabs(["➕ Προσθήκη Προμηθευτή", "📋 Λίστα Προμηθευτών"])
    
    # --- Προσθήκη προμηθευτή ---
    with tab1:
        with st.form("add_supplier"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Επωνυμία Προμηθευτή*")
                afm = st.text_input("Α.Φ.Μ.")
                phone = st.text_input("Τηλέφωνο")
            
            with col2:
                address = st.text_input("Διεύθυνση")
                email = st.text_input("Email")
            
            submitted = st.form_submit_button("💾 Αποθήκευση Προμηθευτή")
            
            if submitted:
                if name:
                    cursor = db.cursor()
                    cursor.execute(
                        "INSERT INTO suppliers (name, afm, address, phone, email) VALUES (?, ?, ?, ?, ?)",
                        (name, afm, address, phone, email)
                    )
                    db.commit()
                    st.success("✅ Ο προμηθευτής αποθηκεύτηκε επιτυχώς!")
                else:
                    st.error("❌ Η επωνυμία προμηθευτή είναι υποχρεωτική")
    
    # --- Λίστα προμηθευτών ---
    with tab2:
        suppliers = pd.read_sql("SELECT * FROM suppliers ORDER BY name", db)
        
        if suppliers.empty:
            st.info("Δεν υπάρχουν προμηθευτές ακόμη.")
        else:
            st.dataframe(suppliers)
            
            st.subheader("🗑️ Διαγραφή Προμηθευτή")
            supplier_names = suppliers['name'].tolist()
            selected_supplier = st.selectbox("Επίλεξε προμηθευτή για διαγραφή", supplier_names)
            
            if st.button("🗑️ Διαγραφή Προμηθευτή"):
                cursor = db.cursor()
                cursor.execute("DELETE FROM suppliers WHERE name = ?", (selected_supplier,))
                db.commit()
                st.success("✅ Ο προμηθευτής διαγράφηκε!")
                st.rerun()

def manage_invoices(db):
    st.header("📄 Τιμολόγια - Δελτία Αποστολής")
    
    tab1, tab2 = st.tabs(["➕ Δημιουργία Παραστατικού", "📋 Λίστα Παραστατικών"])
    
    # --- Δημιουργία νέου παραστατικού ---
    with tab1:
        with st.form("create_invoice"):
            col1, col2 = st.columns(2)
            with col1:
                doc_number = st.text_input("Αριθμός Παραστατικού*")
                doc_date = st.date_input("Ημερομηνία", value=date.today())
            with col2:
                doc_type = st.selectbox("Είδος Παραστατικού", ["Τιμολόγιο - Δελτίο Αποστολής"])
            
            st.subheader("Στοιχεία Πελάτη")
            customer_name = st.text_input("Επωνυμία Πελάτη*")
            afm = st.text_input("Α.Φ.Μ.")
            address = st.text_input("Διεύθυνση")
            
            st.markdown("---")
            st.subheader("Γραμμές Παραστατικού (Προϊόντα)")
            
            products = pd.read_sql("SELECT id, name, quantity FROM products WHERE quantity > 0", db)
            qty_inputs = {}

            if products.empty:
                st.info("Δεν υπάρχουν διαθέσιμα προϊόντα με απόθεμα. Πρόσθεσε προϊόντα ή αύξησε τα αποθέματα.")
            else:
                for _, row in products.iterrows():
                    max_qty = int(row['quantity']) if row['quantity'] is not None else 0
                    qty = st.number_input(
                        f"{row['name']} (διαθέσιμα: {max_qty})",
                        min_value=0,
                        max_value=max_qty,
                        value=0,
                        key=f"inv_qty_{row['id']}"
                    )
                    if qty > 0:
                        qty_inputs[row['id']] = qty
            
            submitted = st.form_submit_button("💾 Αποθήκευση Παραστατικού")
            
            if submitted:
                if not doc_number or not customer_name:
                    st.error("❌ Συμπλήρωσε τουλάχιστον **αριθμό παραστατικού** και **επωνυμία πελάτη**.")
                elif not qty_inputs:
                    st.error("❌ Επέλεξε τουλάχιστον **ένα προϊόν** με ποσότητα > 0.")
                else:
                    try:
                        cursor = db.cursor()
                        # Εισαγωγή header παραστατικού
                        cursor.execute(
                            """
                            INSERT INTO invoices (doc_number, doc_type, doc_date, customer_name, afm, address)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (doc_number, doc_type, doc_date.isoformat(), customer_name, afm, address)
                        )
                        invoice_id = cursor.lastrowid
                        
                        # Εισαγωγή γραμμών & ενημέρωση αποθήκης
                        for pid, q in qty_inputs.items():
                            cursor.execute(
                                "INSERT INTO invoice_lines (invoice_id, product_id, quantity) VALUES (?, ?, ?)",
                                (invoice_id, pid, q)
                            )
                            cursor.execute(
                                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                                (q, pid)
                            )
                        
                        db.commit()
                        st.success("✅ Το παραστατικό αποθηκεύτηκε επιτυχώς και τα αποθέματα ενημερώθηκαν!")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Σφάλμα κατά την αποθήκευση παραστατικού: {e}")
    
    # --- Λίστα παραστατικών ---
    with tab2:
        invoices = pd.read_sql(
            "SELECT id, doc_number, doc_type, doc_date, customer_name FROM invoices ORDER BY doc_date DESC, id DESC",
            db
        )
        
        if invoices.empty:
            st.info("Δεν υπάρχουν παραστατικά ακόμη.")
        else:
            st.subheader("Όλα τα Παραστατικά")
            st.dataframe(invoices)
            
            st.markdown("---")
            st.subheader("Προβολή Αναλυτικού Παραστατικού")
            doc_numbers = invoices['doc_number'].tolist()
            selected_doc = st.selectbox("Επίλεξε παραστατικό", doc_numbers)
            
            if selected_doc:
                inv_row = invoices[invoices['doc_number'] == selected_doc].iloc[0]
                
                st.write(f"**Αρ. Παραστατικού:** {inv_row['doc_number']}")
                st.write(f"**Είδος:** {inv_row['doc_type']}")
                st.write(f"**Ημερομηνία:** {inv_row['doc_date']}")
                st.write(f"**Πελάτης:** {inv_row['customer_name']}")
                
                # Γραμμές παραστατικού
                lines = pd.read_sql(
                    """
                    SELECT p.name AS Προϊόν, il.quantity AS Ποσότητα
                    FROM invoice_lines il
                    JOIN products p ON p.id = il.product_id
                    WHERE il.invoice_id = ?
                    """,
                    db,
                    params=(int(inv_row['id']),)
                )
                
                if not lines.empty:
                    st.table(lines)
                else:
                    st.info("Δεν βρέθηκαν γραμμές για το συγκεκριμένο παραστατικό.")

def show_inventory(db):
    st.header("📊 Κατάσταση Αποθήκης")
    
    # Σύνολο αποθέματος
    inventory = pd.read_sql("""
        SELECT p.name, p.category, p.quantity, p.description 
        FROM products p 
        WHERE p.quantity > 0
        ORDER BY p.quantity DESC
    """, db)
    
    if not inventory.empty:
        st.dataframe(inventory)
        
        # Γράφημα
        st.subheader("Απόθεμα ανά Κατηγορία")
        category_sum = inventory.groupby('category')['quantity'].sum()
        st.bar_chart(category_sum)
    else:
        st.info("Η αποθήκη είναι άδεια")

if __name__ == "__main__":
    main()
