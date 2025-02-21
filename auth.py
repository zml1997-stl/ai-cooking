import streamlit as st
import json
import os
import re
import hashlib
from datetime import datetime

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)
os.makedirs("data/recipes", exist_ok=True)

# Path to users file
USERS_FILE = "data/users.json"

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def setup_auth():
    """Initialize session state variables"""
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'name' not in st.session_state:
        st.session_state['name'] = None

def login_page():
    """Display login and registration forms"""
    st.title("AI Cooking Assistant")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        # Login Form
        st.subheader("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if not login_email or not login_password:
                st.error("Please enter both email and password")
                return
            
            users = load_users()
            if login_email not in users:
                st.error("User not found")
                return
            
            # Verify password
            hashed_password = hash_password(login_password)
            if hashed_password == users[login_email]["password_hash"]:
                st.session_state['authentication_status'] = True
                st.session_state['username'] = login_email
                st.session_state['name'] = users[login_email]["name"]
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Incorrect password")
    
    with tab2:
        # Registration Form
        st.subheader("Register")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        
        if st.button("Register"):
            # Validate inputs
            if not reg_name or not reg_email or not reg_password:
                st.error("All fields are required")
                return
            
            if reg_password != reg_confirm_password:
                st.error("Passwords do not match")
                return
            
            # Validate email format
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_pattern, reg_email):
                st.error("Please enter a valid email")
                return
            
            # Load existing users
            users = load_users()
            
            # Check if user already exists
            if reg_email in users:
                st.error("Email already registered")
                return
            
            # Hash password and save user
            hashed_password = hash_password(reg_password)
            users[reg_email] = {
                "name": reg_name,
                "password_hash": hashed_password,
                "created_at": datetime.now().isoformat()
            }
            
            save_users(users)
            st.success("Registration successful! Please login.")

def logout():
    """Handle user logout"""
    if st.sidebar.button("Logout"):
        st.session_state['authentication_status'] = None
        st.session_state['username'] = None
        st.session_state['name'] = None
        st.experimental_rerun()

def save_recipe(user_email, prompt, recipe_data):
    """Save generated recipe to user history"""
    user_dir = f"data/recipes/{user_email.replace('@', '_at_')}"
    os.makedirs(user_dir, exist_ok=True)
    
    # Create a timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user_dir}/{timestamp}.json"
    
    recipe_entry = {
        "prompt": prompt,
        "recipe_data": recipe_data,
        "created_at": datetime.now().isoformat()
    }
    
    with open(filename, 'w') as f:
        json.dump(recipe_entry, f, indent=4)

def get_user_recipes(user_email):
    """Get all recipes for a user"""
    user_dir = f"data/recipes/{user_email.replace('@', '_at_')}"
    if not os.path.exists(user_dir):
        return []
    
    recipes = []
    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(user_dir, filename)
            with open(filepath, 'r') as f:
                recipe_entry = json.load(f)
                recipes.append(recipe_entry)
    
    # Sort by created_at (newest first)
    recipes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return recipes
