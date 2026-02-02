# TODO: Link Frontend to Backend

## API Configuration
- [x] Define API base URL (http://127.0.0.1:8001/)
- [x] Add Axios library for HTTP requests

## Authentication
- [x] Implement JWT token storage in localStorage
- [x] Connect login form to `/api/users/login/`
- [x] Connect signup form to `/api/users/` (POST)
- [x] Implement logout functionality
- [x] Add token refresh mechanism
- [x] Update UI based on auth state

## Properties
- [x] Fetch properties from `/api/properties/`
- [x] Display properties dynamically in grid
- [x] Connect search/filter form to backend
- [ ] Implement pagination for properties
- [x] Connect "View Details" buttons

## Favorites System
- [x] Connect favorite buttons to `/api/properties/favorites/`
- [x] Toggle favorites (add/remove)
- [x] Check if property is favorited on load

## Reviews & Feedback
- [x] Submit feedback to `/api/reviews/feedback/`
- [x] Load testimonials from `/api/reviews/reviews/`

## User Profile
- [x] Fetch user profile from `/api/users/profile/`
- [x] Display user info in header when logged in

## Error Handling
- [x] Add proper error handling for all API calls
- [x] Show error messages via toast notifications
- [x] Handle network errors gracefully

## Code Structure
- [x] Create API service module (app.js)
- [x] Create Auth service module
- [x] Create Properties service module

---
## Usage Instructions:

1. Start the Django backend server:
   ```bash
   cd immob_backend
   python manage.py runserver 127.0.0.1:8001
   ```

2. Open the frontend:
   ```bash
   # Open frontend/immob.html in a browser
   # OR serve it with a local server
   cd frontend
   python -m http.server 8000
   ```

3. The frontend will connect to the backend at http://127.0.0.1:8001/

