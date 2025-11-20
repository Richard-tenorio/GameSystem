// JavaScript for GameSystem

// Confirmation dialogs
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}

// Toast notifications (basic implementation)
function showToast(message, type) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + (type || 'info');
    toast.textContent = message;

    // Add to page
    document.body.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// Cart functionality
function addToCart(gameId) {
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ game_id: gameId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Game added to cart!', 'success');
            updateCartCount();
        } else {
            showToast(data.message || 'Failed to add to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred', 'error');
    });
}

function updateCartCount() {
    fetch('/api/cart/count')
    .then(response => response.json())
    .then(data => {
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
            cartCount.textContent = data.count || 0;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Attach event listeners to add-to-cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const gameId = this.getAttribute('data-game-id');
            addToCart(gameId);
        });
    });

    // Attach event listeners to delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmDelete('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Attach event listeners to action buttons
    document.querySelectorAll('.action-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirmAction('Are you sure you want to proceed?')) {
                e.preventDefault();
            }
        });
    });

    // Update cart count on page load
    updateCartCount();
});
