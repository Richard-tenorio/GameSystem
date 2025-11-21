document.addEventListener("DOMContentLoaded", function() {
    // Confirm before removing a game (Admin page)
    document.querySelectorAll(".remove-link").forEach(link => {
        link.addEventListener("click", e => {
            if (!confirm("Are you sure you want to remove this game from the inventory?")) {
                e.preventDefault();
            }
        });
    });

    // Confirm before buying a game
    document.querySelectorAll(".buy-link").forEach(link => {
        link.addEventListener("click", e => {
            if (!confirm("Confirm purchase of this game?")) {
                e.preventDefault();
            }
        });
    });
});
