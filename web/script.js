// Animación de aparición para las cards
const cards = document.querySelectorAll('.news-card, .discount-card');
const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    },
    { threshold: 0.1 }
);

cards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
});

// Manejador de eventos para los botones
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function() {
        // Solo mostrar alerta si el botón no es un enlace
        if (!this.getAttribute('href')) {
            alert('Esta función estará disponible próximamente');
        }
    });
});

// Funcionalidad del mapa
const modal = document.getElementById('mapModal');
const mapBtn = document.getElementById('showMapBtn');
const closeBtn = document.querySelector('.close');
let map = null;

if (mapBtn) {
    mapBtn.addEventListener('click', () => {
        modal.style.display = 'block';
        if (!map) {
            // Initialize map
            map = L.map('map').setView([43.4623, -3.8099], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            // Add markers for each event
            document.querySelectorAll('.news-card').forEach(card => {
                const location = card.dataset.location;
                if (location) {
                    const [lat, lng] = location.split(',').map(coord => parseFloat(coord.trim()));
                    const title = card.querySelector('h3').textContent;
                    const priority = card.querySelector('.priority-tag').textContent;
                    
                    L.marker([lat, lng])
                        .addTo(map)
                        .bindPopup(`<strong>${title}</strong><br>Prioridad: ${priority}`);
                }
            });
        }
        // Trigger a resize to ensure the map renders correctly
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    });
}

if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

// Close modal when clicking outside
window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}); 