// Initialize map
let map;
let floodLayer, landslideLayer, liquefactionLayer;
let currentMarker;

// Color mapping for susceptibility levels
const COLORS = {
    'LS': '#2ecc71',    // Low - Green
    'MS': '#f39c12',    // Moderate - Orange
    'HS': '#e67e22',    // High - Dark Orange
    'VHS': '#e74c3c'    // Very High - Red
};

// Initialize the map
function initMap() {
    // Center on Negros Oriental
    map = L.map('map').setView([9.3, 123.3], 9);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Initialize layer groups
    floodLayer = L.layerGroup().addTo(map);
    landslideLayer = L.layerGroup().addTo(map);
    liquefactionLayer = L.layerGroup().addTo(map);
    
    // Load initial data
    loadHazardData();
    
    // Map click event
    map.on('click', onMapClick);
}

// Load hazard data from API
async function loadHazardData() {
    try {
        // Load flood data
        const floodResponse = await fetch('/api/flood-data/');
        if (floodResponse.ok) {
            const floodData = await floodResponse.json();
            addGeoJSONLayer(floodData, floodLayer, 'flood');
        }
        
        // Load landslide data
        const landslideResponse = await fetch('/api/landslide-data/');
        if (landslideResponse.ok) {
            const landslideData = await landslideResponse.json();
            addGeoJSONLayer(landslideData, landslideLayer, 'landslide');
        }
        
        // Load liquefaction data
        const liquefactionResponse = await fetch('/api/liquefaction-data/');
        if (liquefactionResponse.ok) {
            const liquefactionData = await liquefactionResponse.json();
            addGeoJSONLayer(liquefactionData, liquefactionLayer, 'liquefaction');
        }
        
    } catch (error) {
        console.error('Error loading hazard data:', error);
    }
}

// Add GeoJSON layer to map
function addGeoJSONLayer(geojsonData, layerGroup, hazardType) {
    L.geoJSON(geojsonData, {
        style: function(feature) {
            const susceptibility = feature.properties.susceptibility;
            return {
                fillColor: COLORS[susceptibility] || '#95a5a6',
                weight: 1,
                opacity: 0.8,
                color: 'white',
                fillOpacity: 0.6
            };
        },
        onEachFeature: function(feature, layer) {
            // Add popup
            const popupContent = `
                <strong>${hazardType.charAt(0).toUpperCase() + hazardType.slice(1)} Susceptibility</strong><br>
                Level: ${feature.properties.susceptibility}<br>
                Original Code: ${feature.properties.original_code}
                ${feature.properties.shape_area ? `<br>Area: ${feature.properties.shape_area.toLocaleString()} sq units` : ''}
            `;
            layer.bindPopup(popupContent);
            
            // Add to layer group
            layer.addTo(layerGroup);
        }
    });
}

// Handle map click events
function onMapClick(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;
    
    // Remove existing marker
    if (currentMarker) {
        map.removeLayer(currentMarker);
    }
    
    // Add new marker
    currentMarker = L.marker([lat, lng]).addTo(map);
    
    // Show sidebar with location info
    showLocationInfo(lat, lng);
}

// Show location information in sidebar
function showLocationInfo(lat, lng) {
    const sidebar = document.getElementById('sidebar');
    const locationInfo = document.getElementById('location-info');
    const hazardDetails = document.getElementById('hazard-details');
    
    // Show sidebar
    sidebar.classList.remove('hidden');
    
    // Update location info
    locationInfo.innerHTML = `
        <strong>Selected Location</strong><br>
        Latitude: ${lat.toFixed(6)}<br>
        Longitude: ${lng.toFixed(6)}
    `;
    
    // Get hazard information for this location
    getHazardInfoForLocation(lat, lng, hazardDetails);
}

// Get hazard information for specific location
async function getHazardInfoForLocation(lat, lng, container) {
    container.innerHTML = '<p>Analyzing hazard levels...</p>';
    
    try {
        // This is a simplified version - in a real implementation,
        // you would query the PostGIS database for point-in-polygon queries
        const hazardInfo = [];
        
        // For now, we'll show general information
        hazardInfo.push('<div class="hazard-item">');
        hazardInfo.push('<strong>Flood Susceptibility:</strong> <span class="analyzing">Analyzing...</span><br>');
        hazardInfo.push('<strong>Landslide Susceptibility:</strong> <span class="analyzing">Analyzing...</span><br>');
        hazardInfo.push('<strong>Liquefaction Susceptibility:</strong> <span class="analyzing">Analyzing...</span>');
        hazardInfo.push('</div>');
        
        hazardInfo.push('<div class="note">');
        hazardInfo.push('<small><em>Note: Click on colored areas for detailed information</em></small>');
        hazardInfo.push('</div>');
        
        container.innerHTML = hazardInfo.join('');
        
    } catch (error) {
        container.innerHTML = '<p>Error retrieving hazard information</p>';
        console.error('Error getting hazard info:', error);
    }
}

// Layer toggle functionality
function setupLayerToggles() {
    document.getElementById('flood-toggle').addEventListener('change', function(e) {
        if (e.target.checked) {
            map.addLayer(floodLayer);
        } else {
            map.removeLayer(floodLayer);
        }
    });
    
    document.getElementById('landslide-toggle').addEventListener('change', function(e) {
        if (e.target.checked) {
            map.addLayer(landslideLayer);
        } else {
            map.removeLayer(landslideLayer);
        }
    });
    
    document.getElementById('liquefaction-toggle').addEventListener('change', function(e) {
        if (e.target.checked) {
            map.addLayer(liquefactionLayer);
        } else {
            map.removeLayer(liquefactionLayer);
        }
    });
}

// Upload modal functionality
function setupUploadModal() {
    const uploadBtn = document.getElementById('upload-btn');
    const modal = document.getElementById('upload-modal');
    const closeBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-upload');
    const uploadForm = document.getElementById('upload-form');
    
    uploadBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
    });
    
    closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        resetUploadForm();
    });
    
    cancelBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        resetUploadForm();
    });
    
    uploadForm.addEventListener('submit', handleFileUpload);
}

// Handle file upload
async function handleFileUpload(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById('shapefile-input');
    const datasetType = document.getElementById('dataset-type').value;
    
    if (!fileInput.files[0]) {
        alert('Please select a shapefile to upload');
        return;
    }
    
    if (!datasetType) {
        alert('Please select a dataset type');
        return;
    }
    
    formData.append('shapefile', fileInput.files[0]);
    formData.append('dataset_type', datasetType);
    
    // Show progress
    showUploadProgress();
    
    try {
        const response = await fetch('/api/upload-shapefile/', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showUploadResult(true, `Successfully processed ${result.records_created} records`);
            // Reload the map data
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showUploadResult(false, result.error || 'Upload failed');
        }
        
    } catch (error) {
        showUploadResult(false, 'Network error occurred');
        console.error('Upload error:', error);
    }
}

// Show upload progress
function showUploadProgress() {
    document.getElementById('upload-form').classList.add('hidden');
    document.getElementById('upload-progress').classList.remove('hidden');
}

// Show upload result
function showUploadResult(success, message) {
    document.getElementById('upload-progress').classList.add('hidden');
    const resultDiv = document.getElementById('upload-result');
    const messageDiv = document.getElementById('result-message');
    
    resultDiv.classList.remove('hidden');
    messageDiv.innerHTML = `
        <div class="${success ? 'success' : 'error'}">
            ${message}
        </div>
    `;
    
    // Add styles for success/error messages
    if (success) {
        messageDiv.style.color = '#27ae60';
        messageDiv.style.backgroundColor = '#d5f4e6';
    } else {
        messageDiv.style.color = '#e74c3c';
        messageDiv.style.backgroundColor = '#fadbd8';
    }
    messageDiv.style.padding = '1rem';
    messageDiv.style.borderRadius = '5px';
    messageDiv.style.marginTop = '1rem';
}

// Reset upload form
function resetUploadForm() {
    document.getElementById('upload-form').classList.remove('hidden');
    document.getElementById('upload-progress').classList.add('hidden');
    document.getElementById('upload-result').classList.add('hidden');
    document.getElementById('upload-form').reset();
}

// Search functionality (basic implementation)
function setupSearch() {
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('location-search');
    
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// Perform location search (basic implementation)
function performSearch() {
    const searchTerm = document.getElementById('location-search').value.trim();
    
    if (!searchTerm) {
        alert('Please enter a location to search');
        return;
    }
    
    // This is a basic implementation - you can integrate with a geocoding service
    // For now, we'll just show an alert
    alert(`Search functionality is basic in this demo. Searched for: "${searchTerm}"`);
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    setupLayerToggles();
    setupUploadModal();
    setupSearch();
});