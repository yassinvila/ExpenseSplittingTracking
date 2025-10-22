document.addEventListener('DOMContentLoaded', function () {
    // Get the auth token from localStorage
    const authToken = localStorage.getItem('token');

    // If no token, prevent further actions
    if (!authToken) {
        alert("You are not logged in.");
        return;
    }

    // Function to fetch groups
    function fetchGroups() {
        fetch('http://localhost:5000/api/groups', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                renderGroups(data.groups);
            }
        })
        .catch(error => {
            console.error('Error fetching groups:', error);
            alert('Error fetching groups.');
        });
    }

    // Function to render groups on the page
    function renderGroups(groups) {
        const groupsContainer = document.getElementById('groups-container');
        groupsContainer.innerHTML = '';  // Clear any existing groups

        if (groups.length === 0) {
            groupsContainer.innerHTML = '<p>No groups found.</p>';
            return;
        }

        groups.forEach(group => {
            const groupCard = document.createElement('div');
            groupCard.classList.add('group-card');

            groupCard.innerHTML = `
                <h3>${group.group_name}</h3>
                <p><strong>Description:</strong> ${group.group_description}</p>
                <p><strong>Created by:</strong> User ID ${group.created_by}</p>
                <p class="member-count">Members: ${group.member_count}</p>
            `;

            groupsContainer.appendChild(groupCard);
        });
    }

    // Call fetchGroups to load user groups when the page loads
    fetchGroups();
});
