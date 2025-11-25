// Add any JavaScript functionality here

function toggleNotifications() {
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationDropdown) {
        notificationDropdown.style.display = notificationDropdown.style.display === 'block' ? 'none' : 'block';
        if (notificationDropdown.style.display === 'block') {
            loadNotifications();
        }
    } else {
        // Create notification dropdown if it doesn't exist
        createNotificationDropdown();
    }
}

function createNotificationDropdown() {
    const headerNav = document.querySelector('.header-nav');
    const notificationLink = document.querySelector('.notification-link');

    const dropdown = document.createElement('div');
    dropdown.id = 'notificationDropdown';
    dropdown.className = 'notification-dropdown';
    dropdown.innerHTML = `
        <div class="notification-header">
            <h4>Notifications</h4>
            <button onclick="closeNotifications()">×</button>
        </div>
        <div id="notificationList" class="notification-list">
            <p>Loading...</p>
        </div>
    `;
    headerNav.appendChild(dropdown);
    dropdown.style.display = 'block';
    loadNotifications();
}

function closeNotifications() {
    const dropdown = document.getElementById('notificationDropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

function loadNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayNotifications(data.notifications);
            } else {
                displayNotifications([]);
            }
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
            displayNotifications([]);
        });
}

function displayNotifications(notifications) {
    const notificationList = document.getElementById('notificationList');
    if (!notificationList) return;

    if (notifications.length === 0) {
        notificationList.innerHTML = '<p>No new notifications</p>';
        return;
    }

    notificationList.innerHTML = notifications.map(notification => `
        <div class="notification-item" data-id="${notification.id}">
            <p>${notification.message}</p>
            <small>${new Date(notification.date_created).toLocaleString()}</small>
            <button onclick="markAsRead(${notification.id})" class="mark-read-btn">Mark as Read</button>
        </div>
    `).join('');
}

function markAsRead(notificationId) {
    fetch(`/api/notifications/mark_read/${notificationId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove the notification from the list
            const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.remove();
            }
            // Reload notifications to update the list
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function openModal(element) {
    const title = element.getAttribute('data-title');
    const platform = element.getAttribute('data-platform');
    const genre = element.getAttribute('data-genre');
    const quantity = element.getAttribute('data-quantity');
    const price = element.getAttribute('data-price');
    const image = element.getAttribute('data-image');
    const buyUrl = element.getAttribute('data-buy-url');
    const sellUrl = element.getAttribute('data-sell-url');
    const rateUrl = element.getAttribute('data-rate-url');
    const editUrl = element.getAttribute('data-edit-url');
    const canBuy = element.getAttribute('data-can-buy');
    const gameId = element.getAttribute('data-game-id');

    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalPlatform').textContent = platform;
    document.getElementById('modalGenre').textContent = genre;
    document.getElementById('modalStatus').textContent = quantity;
    document.getElementById('modalPrice').textContent = '₱' + price;

    const modalImage = document.getElementById('modalImage');
    if (image) {
        modalImage.src = '/static/uploads/' + image;
    } else {
        modalImage.src = '/static/logo.png';
    }

    const buyLink = document.getElementById('modalBuyLink');
    const sellLink = document.getElementById('modalSellLink');
    const rateLink = document.getElementById('modalRateLink');
    const editLink = document.getElementById('modalEditLink');

    if (buyLink) {
        if (canBuy === 'True' || canBuy === 'true') {
            buyLink.href = buyUrl;
            buyLink.style.display = 'inline-block';
        } else {
            buyLink.style.display = 'none';
        }
    }

    if (sellLink) {
        if (sellUrl && sellUrl !== '') {
            sellLink.href = sellUrl;
            sellLink.style.display = 'inline-block';
        } else {
            sellLink.style.display = 'none';
        }
    }

    if (rateLink) {
        if (rateUrl && rateUrl !== '') {
            rateLink.href = rateUrl;
            rateLink.style.display = 'inline-block';
        } else {
            rateLink.style.display = 'none';
        }
    }

    if (editLink) {
        if (editUrl && editUrl !== '') {
            editLink.href = editUrl;
            editLink.style.display = 'inline-block';
        } else {
            editLink.style.display = 'none';
        }
    }

    // Load ratings
    loadGameRatings(gameId);

    document.getElementById('gameModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('gameModal').style.display = 'none';
}

function loadGameRatings(gameId) {
    fetch('/api/game_ratings/' + gameId)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRatings(data);
            }
        })
        .catch(error => console.error('Error loading ratings:', error));
}

function displayRatings(data) {
    const ratingDisplay = document.getElementById('modalRatingDisplay');
    const reviewsContainer = document.getElementById('modalReviews');

    if (data.average_rating > 0) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= Math.round(data.average_rating)) {
                stars += '★';
            } else {
                stars += '☆';
            }
        }

        ratingDisplay.innerHTML = `
            <div class="rating-summary">
                <div class="stars">${stars}</div>
                <div class="rating-info">
                    <div class="average-rating">${data.average_rating.toFixed(1)}</div>
                    <div class="total-ratings">(${data.total_ratings} reviews)</div>
                </div>
            </div>
        `;

        reviewsContainer.innerHTML = data.ratings.map(rating => `
            <div class="review-item">
                <div class="review-header">
                    <span class="reviewer">${rating.username}</span>
                    <span class="review-date">${new Date(rating.date).toLocaleDateString()}</span>
                </div>
                <div class="review-rating">${'★'.repeat(rating.rating)}${'☆'.repeat(5-rating.rating)}</div>
                <div class="review-text">${rating.review || 'No review text'}</div>
            </div>
        `).join('');
    } else {
        ratingDisplay.innerHTML = '<p>No ratings yet.</p>';
        reviewsContainer.innerHTML = '';
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('gameModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}
