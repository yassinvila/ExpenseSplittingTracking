#!/usr/bin/env python3
"""
Quick test script for the new Flask endpoints
Run this after starting the Flask server to test the new functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_signup_and_login():
    """Test user signup and login to get a token"""
    print("Testing signup and login...")
    
    # Test signup
    signup_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    if response.status_code == 201:
        print("✅ Signup successful")
        token = response.json()['token']
        user_id = response.json()['user']['id']
        return token, user_id
    elif response.status_code == 409:
        print("ℹ️ User already exists, trying login...")
        # Try login instead
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
            token = response.json()['token']
            user_id = response.json()['user']['id']
            return token, user_id
        else:
            print(f"❌ Login failed: {response.text}")
            return None, None
    else:
        print(f"❌ Signup failed: {response.text}")
        return None, None

def test_create_group(token):
    """Test creating a group"""
    print("\nTesting group creation...")
    
    group_data = {
        "group_name": "Test Group",
        "group_description": "A test group for expenses"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/groups", json=group_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Group created successfully - Join code: {data['join_code']}")
        group_id = data['group_id']
        return group_id, data['join_code']
    else:
        print(f"❌ Group creation failed: {response.text}")
        return None, None

def test_get_groups(token):
    """Test getting user groups"""
    print("\nTesting get groups...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/groups", headers=headers)
    
    if response.status_code == 200:
        groups = response.json()['groups']
        print(f"✅ Retrieved {len(groups)} groups")
        for group in groups:
            print(f"  - {group['group_name']} (ID: {group['group_id']}, Code: {group['join_code']})")
        return groups
    else:
        print(f"❌ Get groups failed: {response.text}")
        return []

def test_add_expense(token, group_id):
    """Test adding an expense"""
    print("\nTesting add expense...")
    
    expense_data = {
        "amount": 25.50,
        "description": "Test dinner",
        "group_id": group_id
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/expenses", json=expense_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Expense added successfully")
        expense_id = response.json()['expense_id']
        return expense_id
    else:
        print(f"❌ Add expense failed: {response.text}")
        return None

def test_get_balance(token):
    """Test getting user balance"""
    print("\nTesting get balance...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/balance", headers=headers)
    
    if response.status_code == 200:
        balance = response.json()
        print(f"✅ Balance retrieved: Net: ${balance['net_balance']}, Owed by me: ${balance['owed_by_me']}, Owed to me: ${balance['owed_to_me']}")
        return balance
    else:
        print(f"❌ Get balance failed: {response.text}")
        return None

def test_get_activity(token):
    """Test getting recent activity"""
    print("\nTesting get activity...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/activity", headers=headers)
    
    if response.status_code == 200:
        activity = response.json()
        print(f"✅ Activity retrieved: {len(activity['activities'])} activities")
        for act in activity['activities'][:3]:  # Show first 3
            print(f"  - {act['type']}: {act['description']} (${act['amount']})")
        return activity
    else:
        print(f"❌ Get activity failed: {response.text}")
        return None

def test_join_group(token, join_code):
    """Test joining a group with join code"""
    print(f"\nTesting join group with code: {join_code}...")
    
    join_data = {
        "join_code": join_code
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/groups/join", json=join_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Successfully joined group: {data['group_name']}")
        return True
    else:
        print(f"❌ Join group failed: {response.text}")
        return False

def main():
    print("🧪 Testing new Flask endpoints...")
    print("=" * 50)
    
    # Test authentication
    token, user_id = test_signup_and_login()
    if not token:
        print("❌ Authentication failed, cannot continue tests")
        return
    
    # Test group creation
    group_id, join_code = test_create_group(token)
    if not group_id:
        print("❌ Group creation failed, cannot continue tests")
        return
    
    # Test getting groups
    groups = test_get_groups(token)
    
    # Test adding expense
    expense_id = test_add_expense(token, group_id)
    
    # Test getting balance
    balance = test_get_balance(token)
    
    # Test getting activity
    activity = test_get_activity(token)
    
    # Test join group (this will fail since user is already a member)
    print(f"\nNote: Testing join group with existing group code (will show 'already a member' error):")
    test_join_group(token, join_code)
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Start the Flask server: python app.py")
    print("2. Open frontend/dashboard.html in browser")
    print("3. Login with test@example.com / testpass123")
    print("4. Try adding expenses and settling payments!")

if __name__ == "__main__":
    main()
