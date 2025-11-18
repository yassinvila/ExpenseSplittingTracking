// Activity page functionality
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
        
        // Load activity data
        loadActivityData();
        
    } catch (error) {
        console.error('Authentication check failed:', error);
        // On network error, allow user to stay but show warning
        console.warn('Could not verify authentication, proceeding with cached data');
        const userData = JSON.parse(user);
        displayUserInfo(userData);
        // Try to load activity data even if auth check failed
        loadActivityData();
    }
}

function displayUserInfo(user) {
    // Update any user-specific elements on the activity page
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

async function loadActivityData() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.error('No authentication token available');
        displayActivityError();
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/activity', {
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
        
        const activityData = await response.json();
        displayActivityData(activityData);
        
    } catch (error) {
        console.error('Failed to load activity data:', error);
        displayActivityError();
    }
}

function displayActivityData(activityData) {
    const activityList = document.getElementById('activity-list');
    const emptyState = document.getElementById('empty-state');
    
    if (!activityList) {
        console.error('Activity list element not found');
        return;
    }
    
    
    if (activityData.activities.length === 0) {
        // Show empty state
        activityList.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    // Hide empty state and show activity list
    emptyState.style.display = 'none';
    activityList.style.display = 'block';
    
    // Clear loading state
    activityList.innerHTML = '';
    
    // Render activities
    activityData.activities.forEach((activity, index) => {
        const activityElement = createActivityElement(activity);
        activityList.appendChild(activityElement);
    });
}

function getCategoryImagePath(category) {
    // Map category values to image file names
    const categoryMap = {
        'food': 'foodCategory.png',
        'transport': 'transportationCategory.png',
        'entertainment': 'entertainmentCategory.png',
        'utilities': 'utilitiesCategory.png',
        'shopping': 'shoppingCategory.png',
        'travel': 'travelCategory.png',
        'other': 'customCategory.png'
    };
    
    // Default to customCategory if category is empty or not found
    const imageName = categoryMap[category] || 'customCategory.png';
    return `images/${imageName}`;
}

function createActivityElement(activity) {
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.setAttribute('data-type', activity.type);
    
    
    // Create icon - use category image for expenses with category, payment.png for payments, $ for expenses without category
    const icon = document.createElement('div');
    icon.className = `activity-icon ${activity.type}`;
    
    if (activity.type === 'expense' && activity.category && activity.category.trim() !== '') {
        // Create image element for expense category
        const img = document.createElement('img');
        img.src = getCategoryImagePath(activity.category);
        img.alt = activity.category || 'expense';
        img.style.width = '80%';
        img.style.height = '80%';
        img.style.objectFit = 'contain';
        // Make icon container square instead of circle for images
        icon.style.borderRadius = '4px';
        icon.appendChild(img);
    } else if (activity.type === 'payment') {
        // Use payment.png image for payments
        const img = document.createElement('img');
        img.src = 'images/payment.png';
        img.alt = 'payment';
        img.style.width = '80%';
        img.style.height = '80%';
        img.style.objectFit = 'contain';
        // Make icon container square instead of circle for images
        icon.style.borderRadius = '4px';
        icon.appendChild(img);
    } else {
        // Use $ sign for expenses without category
        icon.textContent = '$';
    }
    
    // Create content
    const content = document.createElement('div');
    content.className = 'activity-content';
    
    // Description
    const description = document.createElement('div');
    description.className = 'activity-description';
    
    if (activity.type === 'expense') {
        description.textContent = `${activity.paid_by} paid ${activity.description}`;
    } else {
        description.textContent = `${activity.paid_by} paid ${activity.paid_to}`;
    }
    
    // Meta information
    const meta = document.createElement('div');
    meta.className = 'activity-meta';
    
    if (activity.type === 'expense') {
        meta.innerHTML = `
            <span>in "${activity.group_name}"</span>
        `;
    } else {
        meta.innerHTML = `
            <span>in "${activity.group_name || 'General'}"</span>
        `;
    }
    
    content.appendChild(description);
    content.appendChild(meta);
    
    // Status and amount
    const rightSection = document.createElement('div');
    rightSection.style.display = 'flex';
    rightSection.style.flexDirection = 'column';
    rightSection.style.alignItems = 'flex-end';
    rightSection.style.marginLeft = 'auto';
    rightSection.style.gap = '2px';
    
    // Status
    const status = document.createElement('div');
    status.className = 'activity-status';
    
    if (activity.type === 'expense') {
        if (activity.is_my_expense) {
            status.textContent = 'you paid';
        } else if (activity.is_involved) {
            status.textContent = 'they paid';
        } else {
            status.textContent = 'not involved';
        }
    } else {
        if (activity.is_my_payment) {
            status.textContent = 'you paid';
        } else if (activity.is_paid_to_me) {
            status.textContent = 'you were paid';
        } else {
            status.textContent = 'not involved';
        }
    }
    
    // Amount
    const amount = document.createElement('div');
    amount.className = 'activity-amount';
    amount.textContent = `$${activity.amount.toFixed(2)}`;
    
    // Add color based on whether it's user's activity
    if (activity.type === 'expense') {
        if (activity.is_my_expense) {
            amount.classList.add('negative'); // User paid, so it's money out (red)
        } else if (activity.is_involved) {
            amount.classList.add('negative'); // User owes money, so it's money out (red)
        } else {
            amount.classList.add('positive'); // Someone else paid, so it's money in (green)
        }
    } else {
        if (activity.is_my_payment) {
            amount.classList.add('negative'); // User paid, so it's money out (red)
        } else if (activity.is_paid_to_me) {
            amount.classList.add('positive'); // User received payment, so it's money in (green)
        } else {
            amount.classList.add('positive'); // Not directly involved
        }
    }
    
    rightSection.appendChild(status);
    rightSection.appendChild(amount);
    
    activityItem.appendChild(icon);
    activityItem.appendChild(content);
    activityItem.appendChild(rightSection);
    
    return activityItem;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
        return 'Just now';
    } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 48) {
        return 'Yesterday';
    } else if (diffInHours < 168) { // 7 days
        return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function displayActivityError() {
    console.warn('Using error state due to API error');
    const activityList = document.getElementById('activity-list');
    const emptyState = document.getElementById('empty-state');
    
    if (activityList) {
        activityList.innerHTML = `
            <div class="loading-state">
                <p>Error loading activity. Please try again later.</p>
            </div>
        `;
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
