# Pickup Location Map Feature

## Overview
The Waste Care application now includes an interactive map feature using Leaflet.js to track garbage pickup locations in real-time. The map is specifically scoped to **Almeria, Biliran, Philippines** to focus on the service area.

## Features Added

### 1. Database Changes
- Added `latitude` and `longitude` fields to the `Appointment` model
- Migration created and applied successfully

### 2. API Endpoint
- **URL**: `/api/map-appointments/`
- **Method**: GET
- **Parameters**:
  - `status` (optional): Filter by appointment status
  - `date` (optional): Filter by preferred date
- **Returns**: JSON with appointment locations and details

### 3. Map View
- **URL**: `/pickup-map/`
- **Features**:
  - Interactive Leaflet map with OpenStreetMap tiles
  - Color-coded markers based on appointment status:
    - 🟠 Orange: Requested
    - 🔵 Blue: Scheduled
    - 🟡 Gold: In Progress
    - 🟢 Green: Completed
    - 🔴 Red: Cancelled
  - Click markers to view appointment details
  - Filter by status and date
  - Auto-zoom to fit all markers
  - Responsive design

### 4. Form Updates
- Appointment creation/edit forms now include latitude and longitude fields
- Optional fields with helpful placeholders
- Validation for coordinate ranges

## How to Use

### Adding Location to Appointments

#### Option 1: Manual Entry
1. Go to "Schedule Pickup" or edit an existing appointment
2. Fill in the address
3. Enter latitude and longitude coordinates (optional)
   - Example: Latitude: 14.5995, Longitude: 120.9842

#### Option 2: Using Online Tools
1. Visit [Google Maps](https://maps.google.com)
2. Right-click on your location
3. Click on the coordinates to copy them
4. Paste into the appointment form

#### Option 3: Click on Map (Future Enhancement)
- The map has click detection enabled for future geocoding integration

### Viewing the Map
1. Navigate to **Appointments > Pickup Map** in the menu
2. Use filters to view specific appointments:
   - Filter by status (Requested, Scheduled, etc.)
   - Filter by date
3. Click on any marker to see appointment details
4. Click "View Details" in the popup to go to the full appointment page

## Technical Details

### Files Modified/Created
1. **Models**: `core/models.py` - Added latitude/longitude fields
2. **Views**: `core/advanced_views.py` - Added `pickup_map` view
3. **API**: `core/api_views.py` - Added `get_map_appointments` endpoint
4. **Forms**: `core/forms.py` - Updated AppointmentForm
5. **URLs**: `core/urls.py` - Added map routes
6. **Template**: `core/templates/core/pickup_map.html` - New map interface
7. **Navigation**: `waste_care/templates/includes/navbar.html` - Added map link

### Dependencies
- **Leaflet.js**: v1.9.4 (loaded via CDN)
- **OpenStreetMap**: Free tile provider
- No additional Python packages required

## Future Enhancements

### Recommended Improvements
1. **Geocoding Integration**
   - Auto-fill coordinates from address using Google Maps API or Nominatim
   - Reverse geocoding to validate coordinates

2. **Route Planning**
   - Connect to existing route optimization API
   - Show optimal route for drivers

3. **Clustering**
   - Add marker clustering for better performance with many appointments
   - Use Leaflet.markercluster plugin

4. **Heatmap**
   - Visualize pickup density
   - Identify high-demand areas

5. **Real-time Updates**
   - WebSocket integration for live marker updates
   - Show driver location in real-time

6. **Mobile Geolocation**
   - Use browser geolocation API
   - "Use My Location" button

## Testing

### Sample Coordinates (Almeria, Biliran, Philippines)
The map is scoped to Almeria, Biliran area. Use coordinates within these bounds:
- Almeria Town Center: 11.6447, 124.3931
- Almeria Municipal Hall area: 11.6450, 124.3925
- Sample Barangay locations (approximate):
  - Villa Vicenta: 11.6500, 124.3950
  - Iyosan: 11.6400, 124.3900
  - Poblacion: 11.6447, 124.3931

**Valid Coordinate Range:**
- Latitude: 11.5800 to 11.7100
- Longitude: 124.3200 to 124.4700

### Testing Steps
1. Create appointments with the sample coordinates above
2. Visit the map page
3. Verify markers appear at correct locations
4. Test filters (status, date)
5. Click markers to view popups
6. Test responsive design on mobile

## Troubleshooting

### No Markers Showing
- Ensure appointments have latitude and longitude values
- Check browser console for JavaScript errors
- Verify API endpoint is returning data

### Map Not Loading
- Check internet connection (Leaflet loads from CDN)
- Verify browser supports modern JavaScript
- Clear browser cache

### Incorrect Marker Positions
- Verify coordinate format (latitude: -90 to 90, longitude: -180 to 180)
- Ensure coordinates are not swapped (lat/lng order matters)

## Support
For issues or questions, check the Django logs or browser console for error messages.
