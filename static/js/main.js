// Form state management
const STORAGE_KEY = 'replicate-ai-form';
let currentPage = 1;
let isGenerating = false;

// DOM Elements
const $form = $('#generationForm');
const $prompt = $('#prompt');
const $model = $('#model');
const $aspectRatio = $('#aspectRatio');
const $generateBtn = $('#generateBtn');
const $improveBtn = $('#improvePrompt');
const $gallery = $('#imageGallery');
const $pagination = $('#galleryPagination');
const $spinner = $('#spinnerOverlay');
const errorModal = new bootstrap.Modal('#errorModal');

// Load saved form state
function loadFormState() {
    const savedState = localStorage.getItem(STORAGE_KEY);
    if (savedState) {
        const state = JSON.parse(savedState);
        $prompt.val(state.prompt || '');
        $model.val(state.model || 'flux-pro');
        $aspectRatio.val(state.aspectRatio || '1:1');
    }
}

// Save form state
function saveFormState() {
    const state = {
        prompt: $prompt.val(),
        model: $model.val(),
        aspectRatio: $aspectRatio.val()
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

// Show error in modal
function showError(message) {
    $('#errorMessage').text(message);
    errorModal.show();
}

// Toggle loading state
function toggleLoading(show) {
    if (show) {
        $spinner.css('display', 'flex');
        $generateBtn.prop('disabled', true);
        isGenerating = true;
    } else {
        $spinner.css('display', 'none');
        $generateBtn.prop('disabled', false);
        isGenerating = false;
    }
}

// Create image card
function createImageCard(image) {
    return `
        <div class="col-md-4 col-lg-3 mb-4">
            <div class="card image-card">
                <div class="ambient-background" style="background-image: url('/images/${image.image_filename}')"></div>
                <img src="/images/${image.image_filename}" class="card-img-top" alt="Generated image">
                <div class="overlay">
                    <div class="d-flex justify-content-between">
                        <button class="btn btn-sm btn-outline-light copy-settings" data-image-id="${image.image_filename}" title="Kopírovat nastavení">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-light download-image" data-image-path="/images/${image.image_filename}" title="Stáhnout obrázek">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger delete-image" data-image-id="${image.image_filename}" title="Smazat obrázek">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Create pagination
function createPagination(totalPages) {
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage - 1}">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${currentPage + 1}">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    return html;
}

// Load gallery images
async function loadGallery(page = 1) {
    try {
        const response = await fetch(`/api/images?page=${page}`);
        const data = await response.json();
        
        if (!response.ok) throw new Error(data.error);
        
        $gallery.empty();
        data.images.forEach(image => {
            $gallery.append(createImageCard(image));
        });
        
        $pagination.html(createPagination(data.total_pages));
        currentPage = page;
        
    } catch (error) {
        showError('Chyba při načítání galerie: ' + error.message);
    }
}

// Generate image
async function generateImage(prompt, model, aspectRatio) {
    try {
        toggleLoading(true);
        
        const response = await fetch('/api/generate-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt, model, aspect_ratio: aspectRatio })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        
        // Poll for image status
        let attempts = 0;
        const maxAttempts = 12; // 2 minutes (12 * 10s)
        
        const pollInterval = setInterval(async () => {
            attempts++;
            
            if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                toggleLoading(false);
                throw new Error('Timeout při generování obrázku');
            }
            
            try {
                const statusResponse = await fetch(`/api/metadata/${data.image_id}`);
                const statusData = await statusResponse.json();
                
                if (statusResponse.ok) {
                    clearInterval(pollInterval);
                    toggleLoading(false);
                    loadGallery(1); // Reload first page
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 10000);
        
    } catch (error) {
        toggleLoading(false);
        showError('Chyba při generování obrázku: ' + error.message);
    }
}

// Improve prompt
async function improvePrompt(prompt) {
    try {
        toggleLoading(true);
        
        const response = await fetch('/api/improve-prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        
        $prompt.val(data.improved_prompt);
        saveFormState();
        
    } catch (error) {
        showError('Chyba při vylepšování promptu: ' + error.message);
    } finally {
        toggleLoading(false);
    }
}

// Delete image
async function deleteImage(imageId) {
    try {
        const response = await fetch(`/api/image/${imageId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        
        loadGallery(currentPage);
        
    } catch (error) {
        showError('Chyba při mazání obrázku: ' + error.message);
    }
}

// Event Listeners
$(document).ready(() => {
    loadFormState();
    loadGallery();
    
    // Form submission
    $form.on('submit', async (e) => {
        e.preventDefault();
        if (isGenerating) return;
        
        const prompt = $prompt.val().trim();
        const model = $model.val();
        const aspectRatio = $aspectRatio.val();
        
        if (!prompt) {
            showError('Zadejte prompt pro generování obrázku');
            return;
        }
        
        saveFormState();
        await generateImage(prompt, model, aspectRatio);
    });
    
    // Improve prompt button
    $improveBtn.on('click', async () => {
        const prompt = $prompt.val().trim();
        if (!prompt) {
            showError('Zadejte prompt pro vylepšení');
            return;
        }
        await improvePrompt(prompt);
    });
    
    // Pagination clicks
    $pagination.on('click', '.page-link', async (e) => {
        e.preventDefault();
        const page = $(e.currentTarget).data('page');
        if (page && page !== currentPage) {
            await loadGallery(page);
        }
    });
    
    // Initialize delete modal
    const deleteModal = new bootstrap.Modal('#deleteModal');
    let imageToDelete = null;

    // Delete image button click
    $gallery.on('click', '.delete-image', (e) => {
        const imageId = $(e.currentTarget).data('image-id');
        imageToDelete = imageId.replace(/\.(webp|png)$/, '');
        deleteModal.show();
    });

    // Confirm delete button click
    $('#confirmDelete').on('click', async () => {
        if (imageToDelete) {
            await deleteImage(imageToDelete);
            deleteModal.hide();
            imageToDelete = null;
        }
    });
    
    // Copy settings
    $gallery.on('click', '.copy-settings', async (e) => {
        const imageId = $(e.currentTarget).data('image-id');
        // Odstranit příponu z ID před voláním API
        const cleanImageId = imageId.replace(/\.(webp|png)$/, '');
        try {
            const response = await fetch(`/api/metadata/${cleanImageId}`);
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error);
            
            $prompt.val(data.prompt);
            $model.val(data.model);
            $aspectRatio.val(data.aspect_ratio);
            saveFormState();
            
        } catch (error) {
            showError('Chyba při načítání nastavení: ' + error.message);
        }
    });
    
    // Download image
    $gallery.on('click', '.download-image', (e) => {
        const imagePath = $(e.currentTarget).data('image-path');
        const link = document.createElement('a');
        link.href = imagePath;
        link.download = imagePath.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Image modal
    const $imageModal = $('#imageModal');
    const $modalImage = $('#modalImage');

    // Open image modal
    $gallery.on('click', '.card-img-top', function(e) {
        e.stopPropagation(); // Prevent triggering overlay buttons
        const imageSrc = $(this).attr('src');
        $modalImage.attr('src', imageSrc);
        $imageModal.css('display', 'flex');
        $('body').css('overflow', 'hidden'); // Prevent scrolling
    });

    // Close modal on background or image click
    $imageModal.on('click', function(e) {
        if (e.target === this || e.target === $modalImage[0]) {
            closeImageModal();
        }
    });

    // Close modal on X button click
    $('.modal-close').on('click', closeImageModal);

    function closeImageModal() {
        $imageModal.css('display', 'none');
        $('body').css('overflow', '');
    }

    // Form input changes
    $form.on('change', 'input, select, textarea', saveFormState);
});