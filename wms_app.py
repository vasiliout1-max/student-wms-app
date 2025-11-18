import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, date   # ΝΕΟ: εισάγουμε και date

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

        # Προμηθευτές  🔹 ΝΕΟ – σωστό σημείο!
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                afm TEXT,
                address TEXT,
                phone TEXT,
