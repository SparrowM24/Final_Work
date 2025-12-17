document.addEventListener('DOMContentLoaded', function() {
    let currentPage = 1;
    let totalPages = parseInt(document.getElementById('total-pages').textContent) || 1;
    const productsContainer = document.getElementById('products-container');
    const loadMoreBtn = document.getElementById('load-more-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const noMoreProducts = document.getElementById('no-more-products');
    const currentPageSpan = document.getElementById('current-page');
    const shownProductsSpan = document.getElementById('shown-products');
    let totalShownProducts = parseInt(document.querySelectorAll('.product-card').length);
    
    // Инициализация показанного количества товаров
    updateShownProductsCount();
    
    // Обработчик кнопки "Загрузить еще"
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', loadMoreProducts);
    }
    
    // Функция обновления счетчика показанных товаров
    function updateShownProductsCount() {
        if (shownProductsSpan) {
            shownProductsSpan.textContent = totalShownProducts;
        }
    }
    
    // Функция загрузки следующих товаров
    function loadMoreProducts() {
        if (currentPage >= totalPages) {
            if (loadMoreBtn) loadMoreBtn.style.display = 'none';
            if (noMoreProducts) noMoreProducts.style.display = 'block';
            return;
        }
        
        currentPage++;
        
        if (loadMoreBtn) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = 'Загрузка...';
        }
        
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
        
        fetch(`/load_more_products?page=${currentPage}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.products && data.products.length > 0) {
                    // Добавляем новые товары в контейнер
                    data.products.forEach(product => {
                        const isAvailable = product.quantity > 0;
                        const productCard = createProductCard(product, isAvailable);
                        productsContainer.insertAdjacentHTML('beforeend', productCard);
                        totalShownProducts++;
                    });
                    
                    // Обновляем счетчики
                    if (currentPageSpan) {
                        currentPageSpan.textContent = currentPage;
                    }
                    
                    updateShownProductsCount();
                    
                    // Если больше нет товаров, скрываем кнопку
                    if (!data.has_more) {
                        if (loadMoreBtn) loadMoreBtn.style.display = 'none';
                        if (noMoreProducts) noMoreProducts.style.display = 'block';
                    }
                    
                    // Добавляем обработчики событий к новым формам
                    addEventListenersToNewForms();
                } else if (data.products && data.products.length === 0) {
                    // Нет больше товаров
                    if (loadMoreBtn) loadMoreBtn.style.display = 'none';
                    if (noMoreProducts) noMoreProducts.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке товаров:', error);
                alert('Ошибка при загрузке товаров. Пожалуйста, попробуйте снова.');
            })
            .finally(() => {
                if (loadMoreBtn) {
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.textContent = 'Загрузить еще товары';
                }
                if (loadingIndicator) {
                    loadingIndicator.style.display = 'none';
                }
            });
    }
    
    // Функция создания HTML карточки товара
    function createProductCard(product, isAvailable) {
        return `
            <div class="product-card" data-product-id="${product.id}">
                <h3>${escapeHtml(product.name)}</h3>
                <p><strong>Артикул:</strong> ${escapeHtml(product.article)}</p>
                <p><strong>Количество:</strong> <span class="product-quantity">${product.quantity}</span> шт.</p>
                
                ${isAvailable ? 
                    `<form class="add-to-cart-form">
                        <input type="hidden" name="product_id" value="${product.id}">
                        <div class="quantity-control">
                            <label for="quantity_${product.id}">Количество:</label>
                            <input type="number" name="quantity" id="quantity_${product.id}" 
                                   value="1" min="1" max="${product.quantity}" required>
                        </div>
                        <button type="submit" class="btn btn-primary">В корзину</button>
                    </form>` : 
                    `<p class="out-of-stock">Нет в наличии</p>`
                }
                
                <form method="POST" action="/delete_product/${product.id}" 
                      onsubmit="return confirm('Удалить товар ${escapeHtml(product.name)}?');" class="delete-form">
                    <button type="submit" class="btn btn-danger">Удалить</button>
                </form>
            </div>`;
    }
    
    // Функция экранирования HTML
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    // Добавление товара в корзину
    async function addToCart(productId, quantity) {
        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('quantity', quantity);
        
        try {
            const response = await fetch('/add_to_cart', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Ошибка:', error);
            return { error: 'Ошибка при добавлении в корзину' };
        }
    }
    
    // Добавление обработчиков событий к формам добавления в корзину
    function addEventListenersToForms() {
        const forms = document.querySelectorAll('.add-to-cart-form');
        forms.forEach(form => {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const productId = this.querySelector('input[name="product_id"]').value;
                const quantityInput = this.querySelector('input[name="quantity"]');
                const quantity = parseInt(quantityInput.value);
                const maxQuantity = parseInt(quantityInput.max);
                
                // Проверка максимального количества
                if (quantity > maxQuantity) {
                    alert(`Нельзя добавить больше ${maxQuantity} шт.`);
                    return;
                }
                
                if (quantity <= 0) {
                    alert('Количество должно быть положительным');
                    return;
                }
                
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Добавляем...';
                submitBtn.disabled = true;
                
                try {
                    const result = await addToCart(productId, quantity);
                    
                    if (result.success) {
                        // Обновляем счетчик корзины
                        const cartCountElement = document.getElementById('cart-count');
                        if (cartCountElement) {
                            cartCountElement.textContent = result.cart_total;
                        }
                        
                        // Обновляем количество товара на складе в интерфейсе
                        const productCard = document.querySelector(`.product-card[data-product-id="${productId}"]`);
                        if (productCard) {
                            const quantityElement = productCard.querySelector('.product-quantity');
                            const inputElement = productCard.querySelector('input[name="quantity"]');
                            
                            if (quantityElement && inputElement) {
                                const newQuantity = parseInt(quantityElement.textContent) - quantity;
                                quantityElement.textContent = newQuantity;
                                inputElement.max = newQuantity;
                                
                                if (newQuantity <= 0) {
                                    const formElement = productCard.querySelector('.add-to-cart-form');
                                    if (formElement) {
                                        formElement.outerHTML = '<p class="out-of-stock">Нет в наличии</p>';
                                    }
                                }
                            }
                        }
                        
                        alert(`Товар "${result.product_name}" добавлен в корзину!`);
                        
                        // Сбрасываем значение в форме
                        quantityInput.value = 1;
                    } else {
                        alert(result.error || 'Ошибка при добавлении в корзину');
                    }
                } catch (error) {
                    console.error('Ошибка:', error);
                    alert('Произошла ошибка при добавлении товара в корзину');
                } finally {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            });
        });
    }
    
    // Добавление обработчиков к новым формам (для динамически загруженных товаров)
    function addEventListenersToNewForms() {
        const newForms = document.querySelectorAll('.product-card:not(.initialized) .add-to-cart-form');
        newForms.forEach(form => {
            form.closest('.product-card').classList.add('initialized');
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const productId = this.querySelector('input[name="product_id"]').value;
                const quantityInput = this.querySelector('input[name="quantity"]');
                const quantity = parseInt(quantityInput.value);
                const maxQuantity = parseInt(quantityInput.max);
                
                if (quantity > maxQuantity) {
                    alert(`Нельзя добавить больше ${maxQuantity} шт.`);
                    return;
                }
                
                if (quantity <= 0) {
                    alert('Количество должно быть положительным');
                    return;
                }
                
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Добавляем...';
                submitBtn.disabled = true;
                
                try {
                    const result = await addToCart(productId, quantity);
                    
                    if (result.success) {
                        const cartCountElement = document.getElementById('cart-count');
                        if (cartCountElement) {
                            cartCountElement.textContent = result.cart_total;
                        }
                        
                        const productCard = this.closest('.product-card');
                        const quantityElement = productCard.querySelector('.product-quantity');
                        const inputElement = productCard.querySelector('input[name="quantity"]');
                        
                        if (quantityElement && inputElement) {
                            const newQuantity = parseInt(quantityElement.textContent) - quantity;
                            quantityElement.textContent = newQuantity;
                            inputElement.max = newQuantity;
                            
                            if (newQuantity <= 0) {
                                this.outerHTML = '<p class="out-of-stock">Нет в наличии</p>';
                            }
                        }
                        
                        alert(`Товар "${result.product_name}" добавлен в корзину!`);
                        quantityInput.value = 1;
                    } else {
                        alert(result.error || 'Ошибка при добавлении в корзину');
                    }
                } catch (error) {
                    console.error('Ошибка:', error);
                    alert('Произошла ошибка при добавлении товара в корзину');
                } finally {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            });
        });
    }
    
    // Инициализация обработчиков событий
    addEventListenersToForms();
    
    // Автоматически скрываем кнопку "Загрузить еще", если все товары уже показаны
    if (currentPage >= totalPages && loadMoreBtn) {
        loadMoreBtn.style.display = 'none';
        if (noMoreProducts) noMoreProducts.style.display = 'block';
    }
});