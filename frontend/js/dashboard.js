// Dashboard functionality

document.addEventListener('DOMContentLoaded', function() {
    
    // Check if user is authenticated
    checkAuthentication();
    
    // Add logout functionality
    addLogoutButton();
});

async function checkAuthentication() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    
    if (!token || !user) {
        // Redirect to login if not authenticated
        window.location.href = 'login.html';
        return;
    }
    
    try {
        // Verify token with backend
        const response = await fetch('http://localhost:5000/auth/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: token })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.valid) {
            // Token is invalid, clear storage and redirect
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = 'login.html';
            return;
        }
        
        // Update user info if needed
        if (data.user) {
            localStorage.setItem('user', JSON.stringify(data.user));
        }
        
        // Display user info
        displayUserInfo(data.user);
        
        // Load balance data
        loadBalanceData();
        
        // Load groups data
        loadGroupsData();
        
    } catch (error) {
        console.error('Authentication check failed:', error);
        // On network error, allow user to stay but show warning
        const userData = JSON.parse(user);
        displayUserInfo(userData);
        // Try to load balance data even if auth check failed
        loadBalanceData();
    }
}

function displayUserInfo(user) {
    // Update any user-specific elements on the dashboard
    const userElements = document.querySelectorAll('.user-name');
    userElements.forEach(element => {
        element.textContent = user.name;
    });
    
    // Update email if needed
    const userEmailElements = document.querySelectorAll('.user-email');
    userEmailElements.forEach(element => {
        element.textContent = user.email;
    });
}

async function loadBalanceData() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.error('No authentication token available');
        displayBalanceError();
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/balance', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error Response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const balanceData = await response.json();
        displayBalanceData(balanceData);
        
    } catch (error) {
        console.error('Failed to load balance data:', error);
        // Show error message or fallback to placeholder data
        displayBalanceError();
    }
}

function displayBalanceData(balanceData) {
    // Update main balance
    const balanceAmount = document.querySelector('.balance-amount');
    
    if (balanceAmount) {
        const netBalance = balanceData.net_balance;
        
        // Format the balance text
        if (netBalance > 0) {
            balanceAmount.textContent = `+$${netBalance.toFixed(2)}`;
        } else if (netBalance < 0) {
            balanceAmount.textContent = `-$${Math.abs(netBalance).toFixed(2)}`;
        } else {
            balanceAmount.textContent = `$${netBalance.toFixed(2)}`;
        }
        
        // Update CSS class and inline styles to match breakdown card colors
        balanceAmount.className = 'balance-amount';
        balanceAmount.style.color = '';
        balanceAmount.style.fontWeight = '';
        
        if (netBalance < 0) {
            // Red color to match breakdown-card.owe
            balanceAmount.style.color = '#8b0000'; // --error-dark
            balanceAmount.style.fontWeight = '800';
        } else if (netBalance > 0) {
            // Green color to match breakdown-card.owed
            balanceAmount.style.color = '#2d5a2d'; // --success-dark
            balanceAmount.style.fontWeight = '800';
        } else {
            // Gray color for zero balance
            balanceAmount.style.color = '#555555'; // --gray
            balanceAmount.style.fontWeight = '700';
        }
    }
    
    // Update breakdown cards
    const oweAmount = document.querySelector('.breakdown-card.owe .amount');
    if (oweAmount) {
        oweAmount.textContent = `$${balanceData.owed_by_me.toFixed(2)}`;
    }
    
    const owedAmount = document.querySelector('.breakdown-card.owed .amount');
    if (owedAmount) {
        owedAmount.textContent = `$${balanceData.owed_to_me.toFixed(2)}`;
    }
}

function displayBalanceError() {
    // Show error state or keep placeholder data
    // The HTML already has placeholder values, so we don't need to change anything
}

async function loadGroupsData() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.error('No authentication token available');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/groups', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error Response:', errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const groupsData = await response.json();
        populateGroupDropdowns(groupsData.groups);
        
    } catch (error) {
        console.error('Failed to load groups data:', error);
        // Use placeholder data
        populateGroupDropdowns([]);
    }
}

function populateGroupDropdowns(groups) {
    // Populate expense group dropdown
    const expenseGroupSelect = document.getElementById('expenseGroup');
    if (expenseGroupSelect) {
        expenseGroupSelect.innerHTML = '<option value="">Select group</option>';
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.group_id;
            option.textContent = group.group_name;
            expenseGroupSelect.appendChild(option);
        });
    }
    
    // Populate settle group dropdown
    const settleGroupSelect = document.getElementById('settleGroup');
    if (settleGroupSelect) {
        settleGroupSelect.innerHTML = '<option value="">Select group</option>';
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.group_id;
            option.textContent = group.group_name;
            settleGroupSelect.appendChild(option);
        });
    }
}

function addLogoutButton() {
    // Find the header container to add logout button
    const headerContainer = document.getElementById('header-container');
    if (headerContainer) {
        // Create logout button
        const logoutButton = document.createElement('button');
        logoutButton.textContent = 'Logout';
        logoutButton.className = 'btn btn-outline';
        logoutButton.style.marginLeft = 'auto';
        logoutButton.onclick = logout;
        
        // Add to header (you may need to adjust this based on your header structure)
        headerContainer.appendChild(logoutButton);
    }
}

function logout() {
    // Clear stored authentication data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Redirect to login page
    window.location.href = 'login.html';
}

// Modal functionality
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        
        // Set today's date as default
        const today = new Date().toISOString().split('T')[0];
        const dateInputs = modal.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            if (!input.value) {
                input.value = today;
            }
        });
        
        // Populate participants and groups (placeholder data for now)
        populateModalData(modalId);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore scrolling
        
        // Reset form
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

function populateModalData(modalId) {
    // This would normally fetch data from the backend
    // For now, using placeholder data
    
    if (modalId === 'addExpenseModal') {
        // Populate participants
        const participantsContainer = document.querySelector('#addExpenseModal .participants-container');
        if (participantsContainer) {
            const participants = ['Alice', 'Bob', 'Charlie', 'Diana'];
            participants.forEach((name, index) => {
                const participantItem = document.createElement('div');
                participantItem.className = 'participant-item';
                participantItem.innerHTML = `
                    <input type="checkbox" id="participant-${index}" value="${name}">
                    <label for="participant-${index}">${name}</label>
                `;
                participantsContainer.appendChild(participantItem);
            });
        }
        
        // Add split method change handler
        const splitMethod = document.getElementById('expenseSplitMethod');
        if (splitMethod) {
            splitMethod.addEventListener('change', handleSplitMethodChange);
        }
    } else if (modalId === 'settleExpenseModal') {
        // Populate payer/payee options
        const members = ['Me', 'Alice', 'Bob', 'Charlie', 'Diana'];
        
        const payerSelect = document.getElementById('settlePayer');
        const payeeSelect = document.getElementById('settlePayee');
        
        if (payerSelect) {
            payerSelect.innerHTML = '<option value="">Select payer</option>';
            members.forEach(member => {
                const option = document.createElement('option');
                option.value = member.toLowerCase();
                option.textContent = member;
                payerSelect.appendChild(option);
            });
        }
        
        if (payeeSelect) {
            payeeSelect.innerHTML = '<option value="">Select payee</option>';
            members.forEach(member => {
                const option = document.createElement('option');
                option.value = member.toLowerCase();
                option.textContent = member;
                payeeSelect.appendChild(option);
            });
        }
    }
}

function handleSplitMethodChange() {
    const splitMethod = document.getElementById('expenseSplitMethod');
    const splitDetails = document.getElementById('splitDetails');
    const participants = document.querySelectorAll('#addExpenseModal .participant-item input[type="checkbox"]:checked');
    
    if (!splitMethod || !splitDetails) return;
    
    // Clear previous content
    splitDetails.innerHTML = '';
    splitDetails.style.display = 'none';
    
    if (splitMethod.value === 'equal') {
        // Equal split - no additional details needed
        return;
    }
    
    splitDetails.style.display = 'block';
    splitDetails.innerHTML = '<h4>Split Details</h4>';
    
    participants.forEach((checkbox, index) => {
        const label = checkbox.nextElementSibling.textContent;
        const splitItem = document.createElement('div');
        splitItem.className = 'split-item';
        
        if (splitMethod.value === 'shares') {
            splitItem.innerHTML = `
                <label>${label}</label>
                <input type="number" min="1" value="1" placeholder="Shares">
            `;
        } else if (splitMethod.value === 'percentage') {
            splitItem.innerHTML = `
                <label>${label}</label>
                <input type="number" min="0" max="100" step="0.01" placeholder="%" class="percentage-input">
            `;
        } else if (splitMethod.value === 'exact') {
            splitItem.innerHTML = `
                <label>${label}</label>
                <input type="number" min="0" step="0.01" placeholder="0.00" class="exact-amount-input">
            `;
        }
        
        splitDetails.appendChild(splitItem);
    });
    
    // Add validation for percentage inputs
    if (splitMethod.value === 'percentage') {
        const percentageInputs = splitDetails.querySelectorAll('.percentage-input');
        percentageInputs.forEach(input => {
            input.addEventListener('input', validatePercentages);
        });
    }
}

function validatePercentages() {
    const percentageInputs = document.querySelectorAll('.percentage-input');
    const total = Array.from(percentageInputs).reduce((sum, input) => sum + (parseFloat(input.value) || 0), 0);
    
    if (total > 100) {
        // Show warning or adjust values
        console.warn('Total percentage exceeds 100%');
    }
}

// Add expense functionality
function addExpense() {
    openModal('addExpenseModal');
}

function settleExpense() {
    openModal('settleExpenseModal');
}

// Form submission handlers
document.addEventListener('DOMContentLoaded', function() {
    // Add expense form submission
    const addExpenseForm = document.getElementById('addExpenseForm');
    if (addExpenseForm) {
        addExpenseForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleAddExpense();
        });
    }
    
    // Settle expense form submission
    const settleExpenseForm = document.getElementById('settleExpenseForm');
    if (settleExpenseForm) {
        settleExpenseForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleSettleExpense();
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
});

async function handleAddExpense() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please log in to add expenses');
        return;
    }
    
    const expenseData = {
        amount: parseFloat(document.getElementById('expenseAmount').value),
        description: document.getElementById('expenseDescription').value,
        group_id: parseInt(document.getElementById('expenseGroup').value)
    };
    
    // Validate required fields
    if (!expenseData.amount || !expenseData.description || !expenseData.group_id) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/expenses', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(expenseData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeModal('addExpenseModal');
            alert('Expense added successfully!');
            // Reload balance data to reflect the new expense
            loadBalanceData();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Failed to add expense:', error);
        alert('Failed to add expense. Please try again.');
    }
}

async function handleSettleExpense() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        alert('Please log in to record payments');
        return;
    }
    
    const settleData = {
        amount: parseFloat(document.getElementById('settleAmount').value),
        paid_to: parseInt(document.getElementById('settlePayee').value)
    };
    
    // Validate required fields
    if (!settleData.amount || !settleData.paid_to) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/payments', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settleData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeModal('settleExpenseModal');
            alert('Payment recorded successfully!');
            // Reload balance data to reflect the payment
            loadBalanceData();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Failed to record payment:', error);
        alert('Failed to record payment. Please try again.');
    }
}

// Make functions globally available
window.addExpense = addExpense;
window.settleExpense = settleExpense;
window.openModal = openModal;
window.closeModal = closeModal;