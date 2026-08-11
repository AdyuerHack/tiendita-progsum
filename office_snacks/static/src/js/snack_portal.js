function initSnackPortal() {
    function showToast(message, type) {
        var bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        var toastHtml = `
            <div class="toast align-items-center text-white ${bgClass} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close" onclick="this.closest('.toast').remove()"></button>
                </div>
            </div>
        `;
        var container = document.getElementById('snack_toast_container');
        if (!container) return; // Prevent errors if not on the catalog page
        container.insertAdjacentHTML('beforeend', toastHtml);
        var toast = container.lastElementChild;
        setTimeout(function () {
            toast.remove();
        }, 3000);
    }

    document.querySelectorAll('.js_buy_snack').forEach(function(btn) {
        // Evitar adjuntar múltiples veces si se ejecuta de nuevo
        if (btn.dataset.listenerAttached) return;
        btn.dataset.listenerAttached = 'true';

        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var productId = this.getAttribute('data-product-id');
            var qtyInput = this.closest('.card-body').querySelector('.snack-qty');
            var quantity = qtyInput ? parseInt(qtyInput.value) : 1;
            
            var csrfInput = document.querySelector('input[name="csrf_token"]');
            var csrfToken = csrfInput ? csrfInput.value : '';
            
            this.disabled = true;
            var originalText = this.innerText;
            this.innerText = 'Procesando...';

            fetch('/snacks/buy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        product_id: productId,
                        quantity: quantity,
                        csrf_token: csrfToken
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                var result = data.result || {};
                if (result.error) {
                    if (result.redirect) {
                        window.location.href = result.redirect;
                    } else {
                        showToast(result.error, 'error');
                        btn.disabled = false;
                        btn.innerText = originalText;
                    }
                } else if (result.success) {
                    showToast(result.message, 'success');
                    
                    // Actualizar el stock visualmente
                    var stockEl = btn.closest('.card-body').querySelector('p.small');
                    if (stockEl) {
                        var currentStock = parseInt(stockEl.innerText.replace('Disp: ', ''));
                        if (!isNaN(currentStock) && currentStock >= quantity) {
                            var newStock = currentStock - quantity;
                            stockEl.innerText = 'Disp: ' + newStock;
                            if (newStock === 0) {
                                btn.disabled = true;
                                btn.innerText = 'Agotado';
                                return;
                            }
                        }
                    }

                    // Visual Feedback in button
                    btn.innerText = '¡Comprado! ✓';
                    btn.classList.add('btn-success');
                    btn.classList.remove('btn-primary');

                    setTimeout(function () {
                        btn.disabled = false;
                        btn.innerText = originalText;
                        btn.classList.remove('btn-success');
                        btn.classList.add('btn-primary');
                    }, 1500);
                }
            })
            .catch(error => {
                showToast("Error de conexión. Intenta de nuevo.", 'error');
                btn.disabled = false;
                btn.innerText = originalText;
            });
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", initSnackPortal);
} else {
    initSnackPortal();
}
