#!/usr/bin/env python3
"""
Create sample SQLite databases for testing execution verification.
Since BIRD databases are restricted, we'll create representative schemas.
"""

import sqlite3
import os
from pathlib import Path

def create_sample_database(db_path: str, schema_name: str):
    """Create a sample database with realistic schema."""
    
    # Remove if exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create different schemas based on common BIRD patterns
    if schema_name == "users_orders":
        # E-commerce schema
        cursor.executescript("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT,
                country TEXT
            );
            
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT,
                price REAL,
                stock_quantity INTEGER
            );
            
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                order_date TEXT,
                total_amount REAL,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE order_items (
                order_item_id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                unit_price REAL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
            
            -- Insert sample data
            INSERT INTO users VALUES (1, 'alice', 'alice@example.com', '2024-01-15', 'USA');
            INSERT INTO users VALUES (2, 'bob', 'bob@example.com', '2024-02-20', 'Canada');
            INSERT INTO users VALUES (3, 'charlie', 'charlie@example.com', '2024-03-10', 'UK');
            
            INSERT INTO products VALUES (1, 'Laptop', 'Electronics', 999.99, 50);
            INSERT INTO products VALUES (2, 'Mouse', 'Electronics', 29.99, 200);
            INSERT INTO products VALUES (3, 'Desk Chair', 'Furniture', 199.99, 75);
            
            INSERT INTO orders VALUES (1, 1, '2024-06-01', 1029.98, 'completed');
            INSERT INTO orders VALUES (2, 2, '2024-06-05', 29.99, 'pending');
            INSERT INTO orders VALUES (3, 1, '2024-06-10', 199.99, 'completed');
            
            INSERT INTO order_items VALUES (1, 1, 1, 1, 999.99);
            INSERT INTO order_items VALUES (2, 1, 2, 1, 29.99);
            INSERT INTO order_items VALUES (3, 2, 2, 1, 29.99);
            INSERT INTO order_items VALUES (4, 3, 3, 1, 199.99);
        """)
        
    elif schema_name == "employees_departments":
        # HR schema
        cursor.executescript("""
            CREATE TABLE departments (
                dept_id INTEGER PRIMARY KEY,
                dept_name TEXT NOT NULL,
                location TEXT,
                budget REAL
            );
            
            CREATE TABLE employees (
                emp_id INTEGER PRIMARY KEY,
                emp_name TEXT NOT NULL,
                dept_id INTEGER,
                salary REAL,
                hire_date TEXT,
                manager_id INTEGER,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
                FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
            );
            
            CREATE TABLE projects (
                project_id INTEGER PRIMARY KEY,
                project_name TEXT,
                dept_id INTEGER,
                start_date TEXT,
                end_date TEXT,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
            );
            
            -- Insert sample data
            INSERT INTO departments VALUES (1, 'Engineering', 'Building A', 500000);
            INSERT INTO departments VALUES (2, 'Sales', 'Building B', 300000);
            INSERT INTO departments VALUES (3, 'HR', 'Building C', 150000);
            
            INSERT INTO employees VALUES (1, 'John Smith', 1, 85000, '2020-01-15', NULL);
            INSERT INTO employees VALUES (2, 'Jane Doe', 1, 92000, '2019-03-20', 1);
            INSERT INTO employees VALUES (3, 'Bob Johnson', 2, 75000, '2021-06-10', NULL);
            INSERT INTO employees VALUES (4, 'Alice Williams', 3, 68000, '2022-02-28', NULL);
        """)
        
    elif schema_name == "students_courses":
        # Education schema
        cursor.executescript("""
            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY,
                student_name TEXT NOT NULL,
                major TEXT,
                enrollment_year INTEGER,
                gpa REAL
            );
            
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL,
                department TEXT,
                credits INTEGER,
                difficulty TEXT
            );
            
            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_id INTEGER,
                semester TEXT,
                grade TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );
            
            CREATE TABLE professors (
                professor_id INTEGER PRIMARY KEY,
                professor_name TEXT,
                department TEXT,
                years_experience INTEGER
            );
            
            -- Insert sample data
            INSERT INTO students VALUES (1, 'Emma Brown', 'Computer Science', 2022, 3.8);
            INSERT INTO students VALUES (2, 'Liam Wilson', 'Mathematics', 2021, 3.5);
            INSERT INTO students VALUES (3, 'Olivia Davis', 'Physics', 2023, 3.9);
            
            INSERT INTO courses VALUES (1, 'Data Structures', 'CS', 4, 'Hard');
            INSERT INTO courses VALUES (2, 'Linear Algebra', 'MATH', 3, 'Medium');
            INSERT INTO courses VALUES (3, 'Quantum Mechanics', 'PHYS', 4, 'Hard');
            
            INSERT INTO enrollments VALUES (1, 1, 1, 'Fall 2024', 'A');
            INSERT INTO enrollments VALUES (2, 1, 2, 'Fall 2024', 'B+');
            INSERT INTO enrollments VALUES (3, 2, 2, 'Fall 2024', 'A-');
            INSERT INTO enrollments VALUES (4, 3, 3, 'Fall 2024', 'A');
        """)
        
    elif schema_name == "restaurants_reviews":
        # Food/Restaurant schema
        cursor.executescript("""
            CREATE TABLE restaurants (
                restaurant_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                cuisine_type TEXT,
                city TEXT,
                price_range TEXT,
                rating REAL
            );
            
            CREATE TABLE reviews (
                review_id INTEGER PRIMARY KEY,
                restaurant_id INTEGER,
                user_id INTEGER,
                rating INTEGER,
                review_text TEXT,
                review_date TEXT,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
            );
            
            CREATE TABLE dishes (
                dish_id INTEGER PRIMARY KEY,
                restaurant_id INTEGER,
                dish_name TEXT,
                price REAL,
                category TEXT,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(restaurant_id)
            );
            
            -- Insert sample data
            INSERT INTO restaurants VALUES (1, 'Pizza Palace', 'Italian', 'New York', '$$', 4.2);
            INSERT INTO restaurants VALUES (2, 'Sushi Master', 'Japanese', 'San Francisco', '$$$', 4.5);
            INSERT INTO restaurants VALUES (3, 'Burger Barn', 'American', 'Chicago', '$', 3.8);
            
            INSERT INTO reviews VALUES (1, 1, 101, 5, 'Best pizza in town!', '2024-05-15');
            INSERT INTO reviews VALUES (2, 2, 102, 4, 'Great sushi, expensive.', '2024-06-20');
            INSERT INTO reviews VALUES (3, 1, 103, 3, 'Good but crowded.', '2024-07-10');
            
            INSERT INTO dishes VALUES (1, 1, 'Margherita Pizza', 18.99, 'Pizza');
            INSERT INTO dishes VALUES (2, 1, 'Pepperoni Pizza', 21.99, 'Pizza');
            INSERT INTO dishes VALUES (3, 2, 'Salmon Roll', 12.99, 'Sushi');
        """)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created {schema_name} database: {db_path}")


def main():
    """Create all sample databases."""
    db_dir = Path("data/databases/train_databases")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample databases with different schemas
    schemas = [
        "users_orders",
        "employees_departments", 
        "students_courses",
        "restaurants_reviews"
    ]
    
    print("==========================================")
    print("Creating Sample Databases")
    print("==========================================")
    print()
    
    for schema in schemas:
        db_path = db_dir / f"{schema}.db"
        create_sample_database(str(db_path), schema)
    
    print()
    print("==========================================")
    print("Sample Databases Created")
    print("==========================================")
    print(f"Location: {db_dir}")
    print()
    print("These databases can be used for:")
    print("  - Testing execution verification")
    print("  - Schema validation")
    print("  - Development and debugging")
    print()
    print("Note: For production use, you'll need the actual BIRD databases.")
    print("      Contact bird.bench23@gmail.com for access.")


if __name__ == "__main__":
    main()
