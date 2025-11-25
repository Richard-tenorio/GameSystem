// Search functionality for games
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const gamesContainer = document.getElementById('games-container');
    const platformFilter = document.getElementById('platform-filter');
    const genreFilter = document.getElementById('genre-filter');
    const sortSelect = document.getElementById('sort-select');

    if (!searchInput || !gamesContainer) return; // Not on marketplace page

    let searchTimeout;

    // Function to perform search
    function performSearch() {
        const query = searchInput.value.trim();
        const platform = platformFilter ? platformFilter.value : '';
        const genre = genreFilter ? genreFilter.value : '';
        const sort = sortSelect ? sortSelect.value : 'title';

        // Show loading
        gamesContainer.innerHTML = '<div class="loading">Searching games...</div>';

        // AJAX request
        fetch('/api/search_games', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                platform: platform,
                genre: genre,
                sort: sort
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayGames(data.games);
            } else {
                gamesContainer.innerHTML = '<div class="error">Search failed: ' + data.message + '</div>';
            }
        })
        .catch(error => {
            console.error('Search error:', error);
            gamesContainer.innerHTML = '<div class="error">An error occurred during search</div>';
        });
    }

    // Function to display games
    function displayGames(games) {
        if (games.length === 0) {
            gamesContainer.innerHTML = '<div class="no-results">No games found matching your criteria</div>';
            return;
        }

        let html = '';
        games.forEach(game => {
            html += `
                <div class="game-card">
                    <div class="game-image">
                        ${game.image ? `<img src="/static/uploads/${game.image}" alt="${game.title}">` : '<div class="no-image">No Image</div>'}
                    </div>
                    <div class="game-info">
                        <h3>${game.title}</h3>
                        <p class="platform">${game.platform}</p>
                        <p class="genre">${game.genre || 'N/A'}</p>
                        <p class="price">$${game.price.toFixed(2)}</p>
                        <div class="game-actions">
                            <button class="btn btn-primary add-to-cart" data-game-id="${game.id}">Add to Cart</button>
                            <a href="/game/${game.id}" class="btn btn-secondary">View Details</a>
                        </div>
                    </div>
                </div>
            `;
        });
        gamesContainer.innerHTML = html;

        // Re-attach event listeners for add to cart buttons
        attachCartListeners();
    }

    // Attach event listeners for add to cart
    function attachCartListeners() {
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', function() {
                const gameId = this.getAttribute('data-game-id');
                addToCart(gameId);
            });
        });
    }

    // Add to cart function
    function addToCart(gameId) {
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ game_id: parseInt(gameId) })
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
            console.error('Cart error:', error);
            showToast('An error occurred', 'error');
        });
    }

    // Update cart count
    function updateCartCount() {
        fetch('/api/cart/count')
        .then(response => response.json())
        .then(data => {
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = data.count || 0;
            }
        })
        .catch(error => console.error('Cart count error:', error));
    }

    // Event listeners
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 300); // Debounce search
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', performSearch);
    }

    if (platformFilter) {
        platformFilter.addEventListener('change', performSearch);
    }

    if (genreFilter) {
        genreFilter.addEventListener('change', performSearch);
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', performSearch);
    }

    // Initial load
    performSearch();
    updateCartCount();
});
