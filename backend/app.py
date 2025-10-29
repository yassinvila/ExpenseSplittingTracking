from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import bcrypt
from datetime import datetime
import jwt
import random
import string
from crud import get_net_balances, get_user_balances

# instance of Flask
app = Flask(__name__)

# This is for frontend communication
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

@app.route('/ping', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Centsible API is running',
        'version': '1.0.0'
    }), 200

@app.route('/', methods=['GET'])
def home():
    """
    Root endpoint with basic API information
    """
    return jsonify({
        'message': 'Welcome to Centsible API',
        'description': 'A cost-sharing application for groups',
        'endpoints': {
            'health_check': '/ping',
            'auth': {
                'signup': '/auth/signup',
                'login': '/auth/login'
            },
            'docs': '/docs (coming soon)'
        }
    }), 200

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('test.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_token(user_id):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def generate_join_code():
    """Generate a unique 4-digit alphanumeric join code"""
    while True:
        # Generate 4-character code with uppercase letters and numbers
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # Check if code already exists
        conn = get_db_connection()
        existing = conn.execute(
            'SELECT 1 FROM groups WHERE join_code = ?', (code,)
        ).fetchone()
        conn.close()
        
        if not existing:
            return code

# Authentication routes
@app.route('/auth/signup', methods=['POST'])
def signup():
    """
    User registration endpoint
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('name', 'email', 'password')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Basic validation
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if '@' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if user already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user
        password_hash = hash_password(password)
        now = datetime.now().isoformat()
        
        cursor = conn.execute(
            'INSERT INTO users (username, email, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (name, email, password_hash, now, now)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate token
        token = generate_token(user_id)
        
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user_id,
                'name': name,
                'email': email
            },
            'token': token
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """
    User login endpoint
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Find user
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, username, email, password_hash FROM users WHERE email = ?', (email,)
        ).fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = generate_token(user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'name': user['username'],
                'email': user['email']
            },
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/verify', methods=['POST'])
def verify_token():
    """
    Verify JWT token
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        # Decode token
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
        
        # Get user info
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, username, email FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'user': {
                'id': user['id'],
                'name': user['username'],
                'email': user['email']
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """
    Get user balance information
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get user's net balance
        net_balances = get_net_balances()
        user_balance = net_balances.get(user_id, 0.0)
        
        # Get detailed balances for this user
        user_balances = get_user_balances(user_id)
        
        # Calculate amounts owed and owed to user
        owed_by_me = 0.0  # Amount I owe to others
        owed_to_me = 0.0  # Amount others owe me
        
        for lender, borrower, amount in user_balances:
            if borrower == user_id:
                owed_by_me += amount  # I owe this amount
            elif lender == user_id:
                owed_to_me += amount  # Others owe me this amount
        
        return jsonify({
            'net_balance': round(user_balance, 2),
            'owed_by_me': round(owed_by_me, 2),
            'owed_to_me': round(owed_to_me, 2),
            'user_id': user_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/activity', methods=['GET'])
def get_recent_activity():
    """
    Get recent activity for the user (expenses and payments from their groups)
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get user's groups
        conn = get_db_connection()
        user_groups = conn.execute(
            'SELECT group_id FROM members WHERE user_id = ? AND deleted_at IS NULL', (user_id,)
        ).fetchall()
        
        if not user_groups:
            conn.close()
            return jsonify({'activities': []}), 200
        
        group_ids = [group['group_id'] for group in user_groups]
        
        # Get recent expenses from user's groups
        placeholders = ','.join(['?' for _ in group_ids])
        expenses_query = f"""
            SELECT e.expense_id, e.group_id, e.description, e.amount, e.paid_by, e.created_at,
                   u.username as paid_by_name, g.group_name
            FROM expenses e
            JOIN users u ON e.paid_by = u.id
            JOIN groups g ON e.group_id = g.group_id
            WHERE e.group_id IN ({placeholders})
            ORDER BY e.created_at DESC
            LIMIT 20
        """
        
        expenses = conn.execute(expenses_query, group_ids).fetchall()
        
        # Get recent payments involving the user
        payments_query = """
            SELECT p.payment_id, p.paid_by, p.paid_to, p.amount, p.paid_at,
                   u1.username as paid_by_name, u2.username as paid_to_name
            FROM payments p
            JOIN users u1 ON p.paid_by = u1.id
            JOIN users u2 ON p.paid_to = u2.id
            WHERE p.paid_by = ? OR p.paid_to = ?
            ORDER BY p.paid_at DESC
            LIMIT 20
        """
        
        payments = conn.execute(payments_query, (user_id, user_id)).fetchall()
        
        conn.close()
        
        # Format activities
        activities = []
        
        # Add expenses
        for expense in expenses:
            activities.append({
                'id': f"expense_{expense['expense_id']}",
                'type': 'expense',
                'description': expense['description'],
                'amount': float(expense['amount']),
                'paid_by': expense['paid_by_name'],
                'paid_by_id': expense['paid_by'],
                'group_name': expense['group_name'],
                'group_id': expense['group_id'],
                'date': expense['created_at'],
                'is_my_expense': expense['paid_by'] == user_id
            })
        
        # Add payments
        for payment in payments:
            activities.append({
                'id': f"payment_{payment['payment_id']}",
                'type': 'payment',
                'description': f"Payment from {payment['paid_by_name']} to {payment['paid_to_name']}",
                'amount': float(payment['amount']),
                'paid_by': payment['paid_by_name'],
                'paid_by_id': payment['paid_by'],
                'paid_to': payment['paid_to_name'],
                'paid_to_id': payment['paid_to'],
                'date': payment['paid_at'],
                'is_my_payment': payment['paid_by'] == user_id or payment['paid_to'] == user_id
            })
        
        # Sort all activities by date (most recent first)
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        # Limit to 20 most recent activities
        activities = activities[:20]
        
        return jsonify({
            'activities': activities,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    """
    Add a new expense to a group
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'description', 'group_id']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'error': 'Missing required fields: amount, description, group_id'}), 400
        
        amount = float(data['amount'])
        description = data['description'].strip()
        group_id = int(data['group_id'])
        
        # Validate amount
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        # Check if user is member of the group
        conn = get_db_connection()
        membership = conn.execute(
            'SELECT 1 FROM members WHERE user_id = ? AND group_id = ? AND deleted_at IS NULL', 
            (user_id, group_id)
        ).fetchone()
        
        if not membership:
            conn.close()
            return jsonify({'error': 'You are not a member of this group'}), 403
        
        # Get group members
        members = conn.execute(
            'SELECT user_id FROM members WHERE group_id = ? AND deleted_at IS NULL', 
            (group_id,)
        ).fetchall()
        
        if len(members) < 2:
            conn.close()
            return jsonify({'error': 'Group must have at least 2 members to add expenses'}), 400
        
        # Add expense
        now = datetime.now().isoformat()
        cursor = conn.execute(
            'INSERT INTO expenses (group_id, description, amount, paid_by, created_at) VALUES (?, ?, ?, ?, ?)',
            (group_id, description, amount, user_id, now)
        )
        
        expense_id = cursor.lastrowid
        
        # Split expense equally among all members (excluding the payer)
        share_amount = round(amount / len(members), 2)
        
        for member in members:
            member_id = member['user_id']
            if member_id != user_id:  # Don't create balance for the person who paid
                conn.execute(
                    'INSERT INTO balances (group_id, lender, borrower, amount, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (group_id, user_id, member_id, share_amount, now, now)
                )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Expense added successfully',
            'expense_id': expense_id,
            'amount': amount,
            'description': description,
            'group_id': group_id,
            'paid_by': user_id
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid amount or group_id format'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/payments', methods=['POST'])
def record_payment():
    """
    Record a payment between users
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'paid_to']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'error': 'Missing required fields: amount, paid_to'}), 400
        
        amount = float(data['amount'])
        paid_to = int(data['paid_to'])
        
        # Validate amount
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        # Can't pay yourself
        if paid_to == user_id:
            return jsonify({'error': 'Cannot pay yourself'}), 400
        
        # Check if recipient exists
        conn = get_db_connection()
        recipient = conn.execute(
            'SELECT id FROM users WHERE id = ?', (paid_to,)
        ).fetchone()
        
        if not recipient:
            conn.close()
            return jsonify({'error': 'Recipient user not found'}), 404
        
        # Record payment
        now = datetime.now().isoformat()
        cursor = conn.execute(
            'INSERT INTO payments (paid_by, paid_to, amount, paid_at) VALUES (?, ?, ?, ?)',
            (user_id, paid_to, amount, now)
        )
        
        payment_id = cursor.lastrowid
        
        # Update balances - net out in both directions
        # Check both possible balance directions
        
        # Direction 1: Payer owes recipient (paid_to is lender, user_id is borrower)
        balance1 = conn.execute(
            'SELECT amount FROM balances WHERE lender = ? AND borrower = ?', 
            (paid_to, user_id)
        ).fetchone()
        
        # Direction 2: Recipient owes payer (user_id is lender, paid_to is borrower)
        balance2 = conn.execute(
            'SELECT amount FROM balances WHERE lender = ? AND borrower = ?', 
            (user_id, paid_to)
        ).fetchone()
        
        if balance1:
            # Payer has an existing debt to recipient
            current_amount = balance1['amount']
            new_amount = max(0, current_amount - amount)
            
            if new_amount > 0:
                conn.execute(
                    'UPDATE balances SET amount = ?, updated_at = ? WHERE lender = ? AND borrower = ?',
                    (new_amount, now, paid_to, user_id)
                )
            else:
                # Balance fully paid off
                conn.execute(
                    'DELETE FROM balances WHERE lender = ? AND borrower = ?',
                    (paid_to, user_id)
                )
        elif balance2:
            # Recipient owes the payer, payment increases this debt
            current_amount = balance2['amount']
            new_amount = current_amount + amount
            
            conn.execute(
                'UPDATE balances SET amount = ?, updated_at = ? WHERE lender = ? AND borrower = ?',
                (new_amount, now, user_id, paid_to)
            )
        else:
            # No existing balance, create one where recipient owes payer
            conn.execute(
                'INSERT INTO balances (group_id, lender, borrower, amount, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                (0, user_id, paid_to, amount, now, now)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Payment recorded successfully',
            'payment_id': payment_id,
            'amount': amount,
            'paid_by': user_id,
            'paid_to': paid_to
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid amount or user_id format'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/groups', methods=['GET'])
def get_user_groups():
    """
    Get all groups that the user is a member of
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        conn = get_db_connection()
        
        # Get user's groups with member count
        # First, get the groups the user is a member of
        # Then count the members in each of those groups
        groups_query = """
            SELECT g.group_id, g.group_name, g.group_description, g.join_code, g.created_by,
                   (SELECT COUNT(*) 
                    FROM members m2 
                    WHERE m2.group_id = g.group_id AND m2.deleted_at IS NULL) as member_count
            FROM groups g
            INNER JOIN members m ON g.group_id = m.group_id
            WHERE m.user_id = ? AND m.deleted_at IS NULL AND g.deleted_at IS NULL
            GROUP BY g.group_id, g.group_name, g.group_description, g.join_code, g.created_by
            ORDER BY g.group_name
        """
        
        groups = conn.execute(groups_query, (user_id,)).fetchall()
        
        conn.close()
        
        groups_list = []
        for group in groups:
            groups_list.append({
                'group_id': group['group_id'],
                'group_name': group['group_name'],
                'group_description': group['group_description'],
                'join_code': group['join_code'],
                'created_by': group['created_by'],
                'member_count': group['member_count']
            })
        
        return jsonify({
            'groups': groups_list,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/groups', methods=['POST'])
def create_group():
    """
    Create a new group
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('group_name'):
            return jsonify({'error': 'Group name is required'}), 400
        
        group_name = data['group_name'].strip()
        group_description = data.get('group_description', '').strip()
        
        if not group_name:
            return jsonify({'error': 'Group name cannot be empty'}), 400
        
        conn = get_db_connection()
        
        # Generate unique join code
        join_code = generate_join_code()
        
        # Create group
        now = datetime.now().isoformat()
        cursor = conn.execute(
            'INSERT INTO groups (group_name, group_description, join_code, created_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (group_name, group_description, join_code, user_id, now, now)
        )
        
        group_id = cursor.lastrowid
        
        # Add creator as member
        conn.execute(
            'INSERT INTO members (user_id, group_id, joined_at) VALUES (?, ?, ?)',
            (user_id, group_id, now)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Group created successfully',
            'group_id': group_id,
            'group_name': group_name,
            'group_description': group_description,
            'join_code': join_code,
            'created_by': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/groups/join', methods=['POST'])
def join_group():
    """
    Join a group using a join code
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('join_code'):
            return jsonify({'error': 'Join code is required'}), 400
        
        join_code = data['join_code'].strip().upper()
        
        if len(join_code) != 4:
            return jsonify({'error': 'Join code must be 4 characters'}), 400
        
        conn = get_db_connection()
        
        # Find group by join code
        group = conn.execute(
            'SELECT group_id, group_name, group_description FROM groups WHERE join_code = ? AND deleted_at IS NULL', 
            (join_code,)
        ).fetchone()
        
        if not group:
            conn.close()
            return jsonify({'error': 'Invalid join code'}), 404
        
        group_id = group['group_id']
        
        # Check if user is already a member
        existing_member = conn.execute(
            'SELECT 1 FROM members WHERE user_id = ? AND group_id = ? AND deleted_at IS NULL', 
            (user_id, group_id)
        ).fetchone()
        
        if existing_member:
            conn.close()
            return jsonify({'error': 'You are already a member of this group'}), 409
        
        # Add user to group
        now = datetime.now().isoformat()
        conn.execute(
            'INSERT INTO members (user_id, group_id, joined_at) VALUES (?, ?, ?)',
            (user_id, group_id, now)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Successfully joined group',
            'group_id': group_id,
            'group_name': group['group_name'],
            'group_description': group['group_description']
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/groups/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    """
    Get balance information for all members in a specific group
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        conn = get_db_connection()
        
        # Verify user is a member of the group
        membership = conn.execute(
            'SELECT 1 FROM members WHERE user_id = ? AND group_id = ? AND deleted_at IS NULL', 
            (user_id, group_id)
        ).fetchone()
        
        if not membership:
            conn.close()
            return jsonify({'error': 'You are not a member of this group'}), 403
        
        # Get all members of the group
        members_query = """
            SELECT m.user_id, u.username
            FROM members m
            JOIN users u ON m.user_id = u.id
            WHERE m.group_id = ? AND m.deleted_at IS NULL
            ORDER BY u.username
        """
        
        members = conn.execute(members_query, (group_id,)).fetchall()
        
        # Get all balances within this group
        balances_query = """
            SELECT b.lender, b.borrower, b.amount,
                   u1.username as lender_name, u2.username as borrower_name
            FROM balances b
            JOIN users u1 ON b.lender = u1.id
            JOIN users u2 ON b.borrower = u2.id
            WHERE b.group_id = ? AND b.amount > 0
            ORDER BY b.lender, b.borrower
        """
        
        balances = conn.execute(balances_query, (group_id,)).fetchall()
        
        conn.close()
        
        # Calculate totals for each member
        member_totals = {}
        balance_details = {}  # For detailed breakdown on hover
        
        for member in members:
            member_id = member['user_id']
            member_totals[member_id] = {
                'member_id': member_id,
                'member_name': member['username'],
                'owes': 0.0,
                'is_owed': 0.0,
                'owes_breakdown': [],  # List of {to: name, amount: X}
                'is_owed_breakdown': []  # List of {from: name, amount: X}
            }
        
        # Process balances
        balances_list = []
        for balance in balances:
            lender_id = balance['lender']
            borrower_id = balance['borrower']
            amount = float(balance['amount'])
            lender_name = balance['lender_name']
            borrower_name = balance['borrower_name']
            
            # Track in raw format for backward compatibility
            balances_list.append({
                'lender_id': lender_id,
                'lender_name': lender_name,
                'borrower_id': borrower_id,
                'borrower_name': borrower_name,
                'amount': amount
            })
            
            # Update borrower totals (they owe money)
            if borrower_id in member_totals:
                member_totals[borrower_id]['owes'] += amount
                member_totals[borrower_id]['owes_breakdown'].append({
                    'to': lender_name,
                    'amount': amount
                })
            
            # Update lender totals (they are owed money)
            if lender_id in member_totals:
                member_totals[lender_id]['is_owed'] += amount
                member_totals[lender_id]['is_owed_breakdown'].append({
                    'from': borrower_name,
                    'amount': amount
                })
        
        # Convert to list
        member_list = [member_totals[mid] for mid in member_totals]
        
        return jsonify({
            'group_id': group_id,
            'balances': balances_list,
            'members': member_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/groups/<int:group_id>/activity', methods=['GET'])
def get_group_activity(group_id):
    """
    Get recent activity for a specific group
    """
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        conn = get_db_connection()
        
        # Verify user is a member of the group
        membership = conn.execute(
            'SELECT 1 FROM members WHERE user_id = ? AND group_id = ? AND deleted_at IS NULL', 
            (user_id, group_id)
        ).fetchone()
        
        if not membership:
            conn.close()
            return jsonify({'error': 'You are not a member of this group'}), 403
        
        # Get recent expenses for this group
        expenses_query = """
            SELECT e.expense_id, e.description, e.amount, e.paid_by, e.created_at,
                   u.username as paid_by_name
            FROM expenses e
            JOIN users u ON e.paid_by = u.id
            WHERE e.group_id = ?
            ORDER BY e.created_at DESC
            LIMIT 20
        """
        
        expenses = conn.execute(expenses_query, (group_id,)).fetchall()
        
        conn.close()
        
        # Format activities
        activities = []
        
        # Add expenses
        for expense in expenses:
            activities.append({
                'id': f"expense_{expense['expense_id']}",
                'type': 'expense',
                'description': expense['description'],
                'amount': float(expense['amount']),
                'paid_by': expense['paid_by_name'],
                'paid_by_id': expense['paid_by'],
                'date': expense['created_at'],
                'is_my_expense': expense['paid_by'] == user_id
            })
        
        # Sort by date (most recent first)
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'group_id': group_id,
            'activities': activities
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the application
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode
    )
