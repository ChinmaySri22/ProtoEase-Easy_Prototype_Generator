// Product Data
const products = [
    {
        id: 1,
        name: "Elegant Watch",
        price: 150,
        image: "https://images.unsplash.com/photo-1524592094714-0f0654e2031a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHdhdGNofGVufDB8fDB8fHww&auto=format&fit=crop&w=500&q=60",
        altText: "Image of an Elegant Watch"
    },
    {
        id: 2,
        name: "Stylish Sunglasses",
        price: 75,
        image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8c3VuZ2xhc3Nlc3xlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=500&q=60",
        altText: "Image of Stylish Sunglasses"
    },
    {
        id: 3,
        name: "Cozy Sweater",
        price: 90,
        image: "https://images.unsplash.com/photo-1603252180296-86f488b349ca?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NXx8c3dlYXRlcnxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=500&q=60",
        altText: "Image of Cozy Sweater"
    },
    {
        id: 4,
        name: "Leather Jacket",
        price: 220,
        image: "https://images.unsplash.com/photo-1588674944944-469eb9039542?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8bGVhdGhlciUyMGphY2tldHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=500&q=60",
        altText: "Image of a Leather Jacket"
    },
    {
        id: 5,
        name: "Denim Jeans",
        price: 65,
        image: "https://images.unsplash.com/photo-1581655353564-df123a1eb820?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8OHx8d29tZW5zJTIwamVhbnN8ZW58MHx8MHx8fDA%3D&auto=format&fit=crop&w=500&q=60",
        altText: "Image of Denim Jeans"
    }
];

// Cart
let cart = {};

// DOM Elements
const productGrid = document.getElementById('product-grid');
const cartIcon = document.getElementById('cart-icon');
const cartCount = document.getElementById('cart-count');
const cartModal = document.getElementById('cart-modal');
const cartItemsContainer = document.getElementById('cart-items');
const cartTotalElement = document.getElementById('cart-total');
const closeModalButton = document.getElementById('close-modal');
const errorMessage = document.getElementById('error-message');

// --- Utility Functions ---

function showErrorMessage(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
    setTimeout(() => {
        errorMessage.hidden = true;
    }, 3000); // Hide after 3 seconds
}

// --- Rendering Functions --- 

function renderProducts() {
    productGrid.innerHTML = '';
    products.forEach(product => {
        const productCard = document.createElement('article');
        productCard.classList.add('product-card');

        productCard.innerHTML = `
            <img src="${product.image}" alt="${product.altText}">
            <div class="product-card-content">
                <h3>${product.name}</h3>
                <p class="price">$${product.price.toFixed(2)}</p>
                <button class="add-to-cart" data-id="${product.id}" aria-label="Add ${product.name} to cart">Add to Cart</button>
            </div>
        `;
        productGrid.appendChild(productCard);
    });
}

function updateCartIcon() {
    let totalItems = Object.values(cart).reduce((acc, curr) => acc + curr, 0);
    cartCount.textContent = totalItems;
}

function renderCart() {
    cartItemsContainer.innerHTML = '';
    let subtotal = 0;

    if (Object.keys(cart).length === 0) {
        cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
        cartTotalElement.textContent = '$0.00';
        return;
    }

    for (const productId in cart) {
        const product = products.find(p => p.id === parseInt(productId));
        const quantity = cart[productId];

        if (product) {
            const cartItem = document.createElement('div');
            cartItem.classList.add('cart-item');

            cartItem.innerHTML = `
                <img src="${product.image}" alt="${product.altText}">
                <div class="cart-item-details">
                    <p>${product.name} (${quantity})</p>
                    <p>$${(product.price * quantity).toFixed(2)}</p>
                </div>
                <button class="remove-from-cart" data-id="${product.id}" aria-label="Remove ${product.name} from cart">Remove</button>
            `;
            cartItemsContainer.appendChild(cartItem);
            subtotal += product.price * quantity;
        }
    }

    cartTotalElement.textContent = `$${subtotal.toFixed(2)}`;
}

// --- Cart Manipulation Functions --- 

function addToCart(productId) {
    const product = products.find(p => p.id === productId);

    if (!product) {
        console.error("Product not found");
        showErrorMessage("Product not found.");
        return;
    }

    cart[productId] = (cart[productId] || 0) + 1;
    updateCartIcon();
    renderCart();
}

function removeFromCart(productId) {
    delete cart[productId];
    updateCartIcon();
    renderCart();
}

// --- Modal Functions --- 

function openCartModal() {
    cartModal.classList.add('open');
    cartModal.setAttribute('aria-hidden', 'false');
    cartIcon.setAttribute('aria-expanded', 'true');
    closeModalButton.focus(); // Set focus to close button on open
    trapFocus(cartModal);
}

function closeCartModal() {
    cartModal.classList.remove('open');
    cartModal.setAttribute('aria-hidden', 'true');
    cartIcon.setAttribute('aria-expanded', 'false');
    cartIcon.focus(); // Return focus to cart icon
}

function trapFocus(element) {
    const focusableEls = element.querySelectorAll('a[href]:not([disabled]), button:not([disabled]), textarea:not([disabled]), input[type="text"]:not([disabled]), input[type="radio"]:not([disabled]), input[type="checkbox"]:not([disabled]), select:not([disabled])');
    const firstFocusableEl = focusableEls[0];
    const lastFocusableEl = focusableEls[focusableEls.length - 1];
    const KEYCODE_TAB = 9;

    element.addEventListener('keydown', function(e) {
      const isTabPressed = (e.key === 'Tab' || e.keyCode === KEYCODE_TAB);

      if (!isTabPressed) {
        return;
      }

      if (e.shiftKey) {
        if (document.activeElement === firstFocusableEl) {
          lastFocusableEl.focus();
            e.preventDefault();
        }
      } else {
        if (document.activeElement === lastFocusableEl) {
          firstFocusableEl.focus();
            e.preventDefault();
        }
      }
    });
  }

// --- Event Listeners --- 

productGrid.addEventListener('click', function(event) {
    if (event.target.classList.contains('add-to-cart')) {
        const productId = parseInt(event.target.dataset.id);
        addToCart(productId);
    }
});

cartItemsContainer.addEventListener('click', function(event) {
    if (event.target.classList.contains('remove-from-cart')) {
        const productId = parseInt(event.target.dataset.id);
        removeFromCart(productId);
    }
});

cartIcon.addEventListener('click', openCartModal);
closeModalButton.addEventListener('click', closeCartModal);

cartModal.addEventListener('click', function(event) {
    if (event.target === cartModal) {
        closeCartModal();
    }
});

// --- Initialization --- 

renderProducts();
updateCartIcon();