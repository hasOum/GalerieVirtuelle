/**
 * Script global pour GalerieVirtuelle
 * Gère le panier localStorage, les notifications, etc.
 */

// ===== CART MANAGEMENT =====
function updateCartBadge() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  const badge = document.getElementById('cart-badge');
  
  if (cart.length > 0) {
    badge.textContent = cart.length;
    badge.style.display = 'inline-block';
  } else {
    badge.style.display = 'none';
  }
}

function addToCart(id, title, price) {
  let cart = JSON.parse(localStorage.getItem('cart')) || [];
  let existingItem = cart.find(item => item.id === id);
  
  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({
      id: id,
      title: title,
      price: parseFloat(price),
      quantity: 1
    });
  }
  
  localStorage.setItem('cart', JSON.stringify(cart));
  showNotification(`"${title}" ajouté au panier!`, 'success');
  updateCartBadge();
}

function removeFromCart(itemId) {
  if (confirm('Êtes-vous sûr de vouloir supprimer cet article?')) {
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart = cart.filter(i => i.id !== itemId);
    localStorage.setItem('cart', JSON.stringify(cart));
    location.reload();
  }
}

function increaseQty(itemId) {
  let cart = JSON.parse(localStorage.getItem('cart')) || [];
  let item = cart.find(i => i.id === itemId);
  if (item) {
    item.quantity += 1;
    localStorage.setItem('cart', JSON.stringify(cart));
    location.reload();
  }
}

function decreaseQty(itemId) {
  let cart = JSON.parse(localStorage.getItem('cart')) || [];
  let item = cart.find(i => i.id === itemId);
  if (item && item.quantity > 1) {
    item.quantity -= 1;
    localStorage.setItem('cart', JSON.stringify(cart));
    location.reload();
  }
}

function clearCart() {
  if (confirm('Êtes-vous sûr de vouloir vider votre panier?')) {
    localStorage.removeItem('cart');
    location.reload();
  }
}

// ===== NOTIFICATIONS =====
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.className = `toast-notification ${type}`;
  notification.innerHTML = `
    <i class="bi bi-check-circle me-2"></i>
    ${message}
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transform = 'translateX(400px)';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
  updateCartBadge();
  
  // Update badge every second to reflect changes from other tabs
  setInterval(updateCartBadge, 1000);
});

// ===== CSRF TOKEN =====
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// ===== CHECKOUT =====
function proceedToCheckout() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];
  if (cart.length === 0) {
    showNotification('Votre panier est vide', 'error');
    return;
  }
  
  // Désactiver le bouton pour éviter les clics multiples
  const button = event.target.closest('button');
  if (button) {
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Traitement...';
  }
  
  console.log('Cart data:', cart);
  console.log('CSRF Token:', getCookie('csrftoken'));
  
  // Envoyer le panier au serveur via AJAX
  fetch('/checkout/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({
      cart: cart
    })
  })
  .then(response => {
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    return response.json().then(data => ({ status: response.status, data: data }));
  })
  .then(({ status, data }) => {
    console.log('Response data:', data);
    if (data.success) {
      // Vider le localStorage
      localStorage.removeItem('cart');
      // Rediriger vers la page de paiement
      window.location.href = data.redirect_url;
    } else {
      showNotification(data.error || 'Erreur lors du traitement', 'error');
      if (button) {
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-credit-card me-2"></i>Procéder au paiement';
      }
    }
  })
  .catch(error => {
    console.error('Fetch error:', error);
    console.error('Error message:', error.message);
    showNotification('Une erreur est survenue: ' + error.message, 'error');
    if (button) {
      button.disabled = false;
      button.innerHTML = '<i class="bi bi-credit-card me-2"></i>Procéder au paiement';
    }
  });
}

// Fonction pour récupérer le cookie CSRF
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
