// Firebase Messaging Service Worker
// This file handles background push notifications

// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Firebase configuration - Replace with your actual config
const firebaseConfig = {

    apiKey: "AIzaSyC0FtrfPcZBntyxlcWAObtuge_QMIAsrAA",
  
    authDomain: "aurora-notification-e4168.firebaseapp.com",
  
    projectId: "aurora-notification-e4168",
  
    storageBucket: "aurora-notification-e4168.firebasestorage.app",
  
    messagingSenderId: "264603811899",
  
    appId: "1:264603811899:web:10fc6e44af796713611c1e",
  
    measurementId: "G-8JRX821C7L"
  
  };
  

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Firebase Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('Received background message:', payload);
    
    const notificationTitle = payload.notification?.title || 'Aurora Alert!';
    const notificationOptions = {
        body: payload.notification?.body || 'Aurora activity detected in your area!',
        icon: '/favicon.ico',
        badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🌌</text></svg>',
        tag: 'aurora-alert',
        requireInteraction: true,
        actions: [
            {
                action: 'view',
                title: 'View Details'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ],
        data: payload.data || {}
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'view') {
        // Open the app when notification is clicked
        event.waitUntil(
            clients.openWindow('/')
        );
    }
    // 'dismiss' action or no action defaults to just closing the notification
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
    console.log('Notification closed:', event);
});

console.log('Firebase Messaging Service Worker initialized'); 