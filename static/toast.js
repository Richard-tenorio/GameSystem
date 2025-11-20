// Toast notification system
class Toast {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            background: linear-gradient(135deg, #1e1e2f 0%, #2a2a3e 100%);
            color: #ffffff;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            border: 2px solid #007bff;
            box-shadow: 0 4px 20px rgba(0, 123, 255, 0.3);
            pointer-events: auto;
            cursor: pointer;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            max-width: 300px;
            word-wrap: break-word;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;

        // Set border color based on type
        switch(type) {
            case 'success':
                toast.style.borderColor = '#28a745';
                break;
            case 'error':
                toast.style.borderColor = '#dc3545';
                break;
            case 'warning':
                toast.style.borderColor = '#ffc107';
                break;
            default:
                toast.style.borderColor = '#007bff';
        }

        toast.textContent = message;
        this.container.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 10);

        // Auto remove
        const removeToast = () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        };

        // Click to dismiss
        toast.addEventListener('click', removeToast);

        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(removeToast, duration);
        }
    }
}

// Global toast function
const toast = new Toast();
window.showToast = (message, type, duration) => toast.show(message, type, duration);

// Flash messages from Flask
document.addEventListener('DOMContentLoaded', function() {
    // Convert flash messages to toasts
    const flashMessages = document.querySelectorAll('.alert, .success, .error');
    flashMessages.forEach(msg => {
        const type = msg.classList.contains('success') ? 'success' :
                    msg.classList.contains('error') ? 'error' : 'info';
        showToast(msg.textContent.trim(), type);
        msg.style.display = 'none'; // Hide the original flash message
    });
});
