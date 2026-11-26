import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, TileLayer, Popup } from 'react-leaflet'
import { priorityStyle } from '../lib/labels'

const OSM = { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors' }

const FACILITY_COLORS = {
  hospital: '#DC2626',
  fire_station: '#EA580C',
  school: '#2563EB',
  police: '#4F46E5',
  transit: '#7C3AED',
  government: '#0D9488',
}

/** Preview map with complaint marker and nearby critical facilities. */
export function LocationMap({ latitude, longitude, band, nearbyFacilities = [] }) {
  if (latitude == null || longitude == null) {
    return <p className="p-4 text-sm text-muted">This complaint has no GPS location.</p>
  }
  const color = priorityStyle(band).hex
  return (
    <MapContainer center={[latitude, longitude]} zoom={15} scrollWheelZoom={false} className="h-64 w-full rounded-b-lg"
                  aria-label="Complaint location map">
      <TileLayer {...OSM} />
      <CircleMarker center={[latitude, longitude]} radius={10} pathOptions={{ color: '#000', fillColor: color, fillOpacity: 0.9, weight: 2 }}>
        <Popup>Complaint Location ({band} Priority)</Popup>
      </CircleMarker>
      {nearbyFacilities.map((f, i) => (
        <CircleMarker
          key={i}
          center={[f.lat, f.lon]}
          radius={7}
          pathOptions={{
            color: '#fff',
            fillColor: FACILITY_COLORS[f.type] || '#475569',
            fillOpacity: 0.85,
            weight: 1.5,
          }}
        >
          <Popup>
            <div className="text-xs">
              <strong className="block font-semibold">{f.name}</strong>
              <span className="text-gray-500 uppercase text-[10px] tracking-wider">{f.type}</span>
              <p className="mt-1">{Math.round(f.distance_m)}m from complaint</p>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
