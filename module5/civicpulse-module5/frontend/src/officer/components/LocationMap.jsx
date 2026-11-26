import 'leaflet/dist/leaflet.css'
import { CircleMarker, MapContainer, TileLayer } from 'react-leaflet'
import { priorityStyle } from '../lib/labels'

const OSM = { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors' }

/** Small preview map for the complaint detail page. */
export function LocationMap({ latitude, longitude, band }) {
  if (latitude == null || longitude == null) {
    return <p className="p-4 text-sm text-muted">This complaint has no GPS location.</p>
  }
  const color = priorityStyle(band).hex
  return (
    <MapContainer center={[latitude, longitude]} zoom={16} scrollWheelZoom={false} className="h-64 w-full rounded-b-lg"
                  aria-label="Complaint location map">
      <TileLayer {...OSM} />
      <CircleMarker center={[latitude, longitude]} radius={10} pathOptions={{ color, fillColor: color, fillOpacity: 0.7 }} />
    </MapContainer>
  )
}
