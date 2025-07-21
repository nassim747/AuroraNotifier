# Aurora Alert Frontend

A modern, responsive web interface for the Aurora Alert notification system.

## Quick Setup

### 1. Firebase Configuration

You need to configure Firebase for push notifications:

1. **Go to [Firebase Console](https://console.firebase.google.com/)**
2. **Create a new project** or select existing one
3. **Add a Web app** to your project
4. **Copy the config object** you'll get

### 2. Update Configuration Files

Replace the placeholder values in these files with your actual Firebase config:

**`script.js`** (line ~13):
```javascript
const firebaseConfig = {
    apiKey: "your-actual-api-key",
    authDomain: "your-project.firebaseapp.com", 
    projectId: "your-actual-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abcdef123456"
};
```

**`firebase-messaging-sw.js`** (line ~6):
```javascript
const firebaseConfig = {
    // Same config as above
};
```

### 3. Get VAPID Key

1. **In Firebase Console** → **Project Settings** → **Cloud Messaging**
2. **Generate Web Push Certificates** (if not done)
3. **Copy the VAPID key**
4. **Update `script.js`** (line ~75):
```javascript
fcmToken = await messaging.getToken({
    vapidKey: 'your-actual-vapid-key' // Replace this
});
```

### 4. Backend API Configuration

The frontend expects your backend API at the same origin. If running locally:

- **Frontend**: `http://localhost:3000` (or any port)
- **Backend**: `http://localhost:8000` 

For production, both should be on the same domain.

## Features

### ✅ **Working Features:**
- 🎨 Modern responsive design
- 📍 Geolocation support
- 🔔 Browser push notifications
- 📱 Mobile-friendly interface
- 🎛️ Interactive settings sliders
- 💾 Local storage for preferences
- 🚨 Error handling with toast notifications
- 🔄 Loading states and feedback

### 🚧 **Requires Configuration:**
- 🔥 Firebase Cloud Messaging (follow setup above)
- 🌐 Backend API connection
- 🔑 VAPID keys for push notifications

## File Structure

```
frontend/
├── index.html              # Main HTML file
├── style.css               # All styling
├── script.js               # Main JavaScript logic
├── firebase-messaging-sw.js # Service worker for push notifications
└── README.md               # This file
```

## Development

### Local Testing

1. **Start your backend server** on port 8000
2. **Serve the frontend** (any method):
   ```bash
   # Option 1: Python simple server
   python -m http.server 3000
   
   # Option 2: Node.js http-server
   npx http-server -p 3000
   
   # Option 3: Live Server (VS Code extension)
   ```
3. **Open** `http://localhost:3000`

### Production Deployment

The frontend is static files, deploy anywhere:
- **Vercel/Netlify**: Drag & drop the `frontend/` folder
- **GitHub Pages**: Push to a repository
- **Your server**: Copy files to web directory

## API Integration

The frontend expects these backend endpoints:

- `POST /subscribe` - Subscribe to notifications
- `DELETE /unsubscribe` - Unsubscribe from notifications  
- `GET /status` - Health check
- `GET /docs` - API documentation

## Troubleshooting

### Notifications Not Working
1. **Check browser permissions** - Allow notifications for your site
2. **Verify Firebase config** - Make sure all values are correct
3. **Check service worker** - Look for errors in dev tools
4. **Test with HTTP** - Some features require HTTPS in production

### API Errors
1. **Check backend is running** - Visit `/docs` endpoint
2. **Check CORS settings** - Frontend and backend domains
3. **Verify endpoint URLs** - Match your backend API

### Location Not Working
1. **HTTPS required** - Geolocation needs secure context
2. **Check permissions** - Allow location access
3. **Fallback available** - Manual entry works without geolocation

## Browser Support

- ✅ Chrome 80+
- ✅ Firefox 80+  
- ✅ Safari 14+
- ✅ Edge 80+

Push notifications require modern browser support.

## Contributing

When making changes:
1. Test on mobile devices
2. Check browser console for errors
3. Verify API calls work
4. Test notification permissions
5. Check responsive design

## Next Steps

After setup:
1. **Test the complete flow** - Subscribe → Get notifications
2. **Customize styling** - Colors, fonts, layout in `style.css`
3. **Add features** - Historical data, maps, etc.
4. **Deploy** - Put it live for real aurora alerts! 