/**
 * Community Help Connect - Client JavaScript
 * Interactive helpers, form safety checks, and auto-dismiss alerts
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss flash alert messages after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                // If already closed manually
            }
        }, 6000);
    });

    // 2. Minimum Date Restriction (Prevent setting deadlines/expiry in the past)
    const today = new Date().toISOString().split('T')[0];
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function (input) {
        if (!input.getAttribute('min')) {
            input.setAttribute('min', today);
        }
    });

    // 3. Category change helper for Surplus Food Sharing
    const categorySelect = document.getElementById('category');
    const expiryDateField = document.getElementById('expiry_date');
    if (categorySelect && expiryDateField) {
        const toggleExpiryHighlight = function () {
            const isFood = categorySelect.value.toLowerCase().includes('food');
            const parentGroup = expiryDateField.closest('.mb-3') || expiryDateField.parentElement;
            if (isFood) {
                if (parentGroup) parentGroup.classList.add('border', 'border-warning', 'p-2', 'rounded', 'bg-warning', 'bg-opacity-10');
            } else {
                if (parentGroup) parentGroup.classList.remove('border', 'border-warning', 'p-2', 'rounded', 'bg-warning', 'bg-opacity-10');
            }
        };
        categorySelect.addEventListener('change', toggleExpiryHighlight);
        toggleExpiryHighlight();
    }

    // 4. Form Submission Confirmation Dialogs
    const confirmForms = document.querySelectorAll('form[data-confirm]');
    confirmForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const message = form.getAttribute('data-confirm') || 'Are you sure you want to proceed with this action?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 5. Tooltip Initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
