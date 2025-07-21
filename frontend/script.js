// Global state
let userLocation = { lat: null, lon: null };
let fcmToken = null;
let userId = null;
let messaging = null;

// API Configuration - Change this to your deployed backend URL
const API_BASE = 'http://localhost:8000';

// Firebase Configuration - Replace with your actual Firebase config
const firebaseConfig = {
    apiKey: "AIzaSyC0FtrfPcZBntyxlcWAObtuge_QMIAsrAA",
    authDomain: "aurora-notification-e4168.firebaseapp.com",
    projectId: "aurora-notification-e4168",
    storageBucket: "aurora-notification-e4168.firebasestorage.app",
    messagingSenderId: "264603811899",
    appId: "1:264603811899:web:10fc6e44af796713611c1e",
    measurementId: "G-8JRX821C7L"
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    console.log('Aurora Alert App initialized');
    initializeFirebase();
    checkExistingUser();
    initializeSliders();
    checkAPIHealth();
});

// Firebase initialization
function initializeFirebase() {
    try {
        if (typeof firebase !== 'undefined') {
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
            }
            
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/firebase-messaging-sw.js')
                    .then((registration) => {
                        console.log('Service Worker registered:', registration);
                        messaging = firebase.messaging();
                        // The useServiceWorker method is deprecated in newer Firebase versions
                        // The service worker is automatically used when registered
                    })
                    .catch((error) => {
                        console.warn('Service Worker registration failed:', error);
                        // Continue without service worker for basic functionality
                        messaging = firebase.messaging();
                    });
            } else {
                messaging = firebase.messaging();
            }
        } else {
            console.warn('Firebase SDK not loaded. Notifications will use browser fallback.');
        }
    } catch (error) {
        console.error('Firebase initialization error:', error);
    }
}

// Navigation functions
function showWelcome() {
    hideAllSections();
    document.getElementById('welcome').classList.remove('hidden');
}

function showSetupForm() {
    hideAllSections();
    document.getElementById('setup').classList.remove('hidden');
}

function showWelcome() {
    console.log('👋 Showing welcome screen...');
    hideAllSections();
    document.getElementById('welcome').classList.remove('hidden');
}

function showDashboard() {
    hideAllSections();
    document.getElementById('dashboard').classList.remove('hidden');
    loadDashboardData();
}

function showSettings() {
    showSetupForm();
    loadUserSettings();
}

function hideAllSections() {
    const sections = ['welcome', 'setup', 'dashboard'];
    sections.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.classList.add('hidden');
    });
}

// Location functions
async function getCurrentLocation() {
    if (!navigator.geolocation) {
        showError('Geolocation is not supported by this browser');
        return;
    }

    try {
        showLoading(true, 'Getting your location...');
        
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000 // 5 minutes
            });
        });

        userLocation.lat = position.coords.latitude;
        userLocation.lon = position.coords.longitude;

        // Update UI
        document.getElementById('lat').textContent = userLocation.lat.toFixed(4);
        document.getElementById('lon').textContent = userLocation.lon.toFixed(4);
        document.getElementById('locationCoords').classList.remove('hidden');

        // Reverse geocode to get location name
        try {
            const locationName = await reverseGeocode(userLocation.lat, userLocation.lon);
            document.getElementById('location').value = locationName;
        } catch (error) {
            console.warn('Reverse geocoding failed:', error);
            document.getElementById('location').value = `${userLocation.lat.toFixed(4)}, ${userLocation.lon.toFixed(4)}`;
        }

        validateForm();
        showLoading(false);

    } catch (error) {
        showLoading(false);
        console.error('Error getting location:', error);
        showError('Unable to get your current location. Please enter it manually.');
    }
}

async function reverseGeocode(lat, lon) {
    try {
        const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`);
        const data = await response.json();
        
        if (data.city && data.countryName) {
            return `${data.city}, ${data.countryName}`;
        } else if (data.locality && data.countryName) {
            return `${data.locality}, ${data.countryName}`;
        } else {
            return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
        }
    } catch (error) {
        console.warn('Reverse geocoding failed:', error);
        return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
    }
}

// Notification functions
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        showError('This browser does not support notifications');
        return;
    }

    try {
        showLoading(true, 'Setting up notifications...');
        
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            // Try to get FCM token if Firebase is available
            if (messaging) {
                try {
                    // Add timeout to prevent hanging
                    const tokenPromise = messaging.getToken({
                        vapidKey: 'BLgUUf2qVM3NdNgXvOBGb4iiDubEm21A6oi2OQ0Xy3HA_uPZ6ft-gfSa6vDdqg3OcoWXGjIal1YpSOIa94DLCXY' // Replace with your VAPID key
                    });
                    
                    const timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('FCM token timeout')), 5000)
                    );
                    
                    fcmToken = await Promise.race([tokenPromise, timeoutPromise]);
                    console.log('FCM Token:', fcmToken);
                } catch (error) {
                    console.warn('Failed to get FCM token:', error);
                    // Fallback to a mock token for development
                    fcmToken = 'browser_notification_' + Date.now();
                }
            } else {
                // Fallback for browsers without Firebase
                fcmToken = 'browser_notification_' + Date.now();
            }
            
            updateNotificationStatus(true);
            validateForm();
        } else {
            showError('Notification permission denied. You won\'t receive aurora alerts.');
        }
        
        showLoading(false);
        
    } catch (error) {
        showLoading(false);
        console.error('Error requesting notification permission:', error);
        showError('Error setting up notifications');
    }
}

function updateNotificationStatus(granted) {
    const statusElement = document.getElementById('notificationStatus');
    const statusText = statusElement.querySelector('.status-text');
    const button = statusElement.querySelector('button');

    if (granted) {
        statusElement.classList.add('granted');
        statusText.textContent = 'Push notifications enabled';
        button.style.display = 'none';
    } else {
        statusElement.classList.remove('granted');
        statusText.textContent = 'Click to enable push notifications';
        button.style.display = 'block';
    }
}

// Form functions
function initializeSliders() {
    updateSliderValue('radius', 'radiusValue', ' km');
    updateSliderValue('threshold', 'thresholdValue', '%');
}

function updateSliderValue(sliderId, valueId, suffix) {
    const slider = document.getElementById(sliderId);
    const valueDisplay = document.getElementById(valueId);
    if (slider && valueDisplay) {
        valueDisplay.textContent = slider.value + suffix;
    }
}

function validateForm() {
    const submitButton = document.getElementById('submitButton');
    if (submitButton) {
        const hasLocation = userLocation.lat && userLocation.lon;
        const hasNotification = fcmToken;
        
        submitButton.disabled = !(hasLocation && hasNotification);
    }
}

// API functions
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(`API error: ${response.status} - ${errorData.detail || response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Form submission
document.getElementById('setupForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    showLoading(true, 'Setting up your aurora alerts...');
    
    try {
        const formData = {
            lat: userLocation.lat,
            lon: userLocation.lon,
            radius_km: parseInt(document.getElementById('radius').value),
            threshold: parseInt(document.getElementById('threshold').value),
            token: fcmToken  // This matches the backend API schema
        };

        console.log('Subscribing user:', formData);
        
        const response = await apiCall('/subscribe', 'POST', formData);
        
        userId = response.user_id;
        localStorage.setItem('aurora_user_id', userId);
        localStorage.setItem('aurora_fcm_token', fcmToken);
        localStorage.setItem('aurora_user_data', JSON.stringify(formData));
        
        showLoading(false);
        showDashboard();
        
        console.log('User subscribed successfully:', response);
        
    } catch (error) {
        showLoading(false);
        console.error('Subscription failed:', error);
        showError(`Failed to set up aurora alerts: ${error.message}`);
    }
});

// Dashboard functions
async function loadDashboardData() {
    console.log('📊 Loading dashboard data...');
    try {
        // Load user location
        const userData = JSON.parse(localStorage.getItem('aurora_user_data') || '{}');
        console.log('🗺️ User location data:', userData);
        
        if (userData.lat && userData.lon) {
            console.log('🌍 Reverse geocoding location...');
            showLoading(true, 'Loading your location...');
            const locationName = await reverseGeocode(userData.lat, userData.lon);
            showLoading(false);
            console.log('📍 Location name:', locationName);
            
            const locationElement = document.getElementById('userLocation');
            if (locationElement) {
                locationElement.textContent = `Location: ${locationName}`;
            }
        }

        // Check API status for aurora data
        try {
            const status = await apiCall('/status');
            const maxProbElement = document.getElementById('maxProb');
            const lastUpdateElement = document.getElementById('lastUpdate');
            
            if (maxProbElement) maxProbElement.textContent = 'API Connected';
            if (lastUpdateElement) lastUpdateElement.textContent = 'Just now';
        } catch (error) {
            console.warn('Could not load current aurora data:', error);
            const maxProbElement = document.getElementById('maxProb');
            if (maxProbElement) maxProbElement.textContent = 'Loading...';
        }

    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

async function testNotification() {
    if (!fcmToken) {
        showError('Notifications not enabled');
        return;
    }

    try {
        // Show a browser notification for testing
        if (Notification.permission === 'granted') {
            new Notification('Aurora Alert Test', {
                body: 'This is how you\'ll receive aurora notifications! 🌌',
                icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🌌</text></svg>',
                tag: 'aurora-test',
                requireInteraction: false
            });
        }

        console.log('Test notification sent');
        
    } catch (error) {
        console.error('Test notification failed:', error);
        showError('Test notification failed');
    }
}

async function unsubscribe() {
    if (!confirm('Are you sure you want to stop receiving aurora alerts?')) {
        return;
    }

    try {
        showLoading(true, 'Unsubscribing...');
        
        const token = localStorage.getItem('aurora_fcm_token');
        if (token) {
            await apiCall('/unsubscribe', 'DELETE', { token });
        }
        
        // Clear local data
        localStorage.removeItem('aurora_user_id');
        localStorage.removeItem('aurora_fcm_token');
        localStorage.removeItem('aurora_user_data');
        
        userId = null;
        fcmToken = null;
        userLocation = { lat: null, lon: null };
        
        showLoading(false);
        showWelcome();
        
        console.log('Unsubscribed successfully');
        
    } catch (error) {
        showLoading(false);
        console.error('Unsubscribe failed:', error);
        showError('Failed to unsubscribe. Please try again.');
    }
}

function loadUserSettings() {
    const userData = JSON.parse(localStorage.getItem('aurora_user_data') || '{}');
    
    if (userData.lat && userData.lon) {
        userLocation.lat = userData.lat;
        userLocation.lon = userData.lon;
        
        document.getElementById('lat').textContent = userData.lat.toFixed(4);
        document.getElementById('lon').textContent = userData.lon.toFixed(4);
        document.getElementById('locationCoords').classList.remove('hidden');
        
        reverseGeocode(userData.lat, userData.lon).then(name => {
            document.getElementById('location').value = name;
        });
    }
    
    if (userData.radius_km) {
        document.getElementById('radius').value = userData.radius_km;
        updateSliderValue('radius', 'radiusValue', ' km');
    }
    
    if (userData.threshold) {
        document.getElementById('threshold').value = userData.threshold;
        updateSliderValue('threshold', 'thresholdValue', '%');
    }
    
    // Restore FCM token
    fcmToken = localStorage.getItem('aurora_fcm_token');
    if (fcmToken) {
        updateNotificationStatus(true);
        validateForm();
    }
}

function checkExistingUser() {
    console.log('🔍 Checking for existing user...');
    const existingUserId = localStorage.getItem('aurora_user_id');
    const existingUserData = localStorage.getItem('aurora_user_data');
    
    console.log('📦 Found localStorage data:', {
        userId: existingUserId,
        userData: existingUserData,
        token: localStorage.getItem('aurora_fcm_token')
    });
    
    if (existingUserId && existingUserData) {
        console.log('✅ Existing user found, showing dashboard...');
        userId = existingUserId;
        fcmToken = localStorage.getItem('aurora_fcm_token');
        showDashboard();
    } else {
        console.log('👋 New user, showing welcome screen...');
        showWelcome();
    }
}

// UI Helper functions
function showLoading(show, message = 'Loading...') {
    // Loading overlay removed - function disabled
    console.log('Loading:', show, message);
}

function showError(message) {
    const errorToast = document.getElementById('errorToast');
    const errorMessage = document.getElementById('errorMessage');
    
    if (errorToast && errorMessage) {
        errorMessage.textContent = message;
        errorToast.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideError();
        }, 5000);
    } else {
        // Fallback to alert if error toast elements are missing
        alert(message);
    }
}

function hideError() {
    const errorToast = document.getElementById('errorToast');
    if (errorToast) {
        errorToast.classList.add('hidden');
    }
}

// Health check
async function checkAPIHealth() {
    try {
        const response = await apiCall('/status');
        console.log('API Health: OK', response);
        return true;
    } catch (error) {
        console.warn('API Health check failed:', error);
        showError('Backend API is not responding. Some features may not work.');
        return false;
    }
}