import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet'
import { config } from '../config'
import { priorityStyle, statusLabel } from '../lib/labels'
import { shortId } from '../lib/format'
import { HeatLayer } from './HeatLayer'

const OSM = { url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap contributors' }

function FitToPoints({ points }) {
  const map = useMap()
  useEffect(() => {
    if (!points.length) return
    map.fitBounds(points.map((p) => [p.latitude, p.longitude]), { padding: [32, 32], maxZoom: 15 })
  }, [map, points])
  return null
}

export function OverviewMap({ points, heat, showMarkers, showHeat }) {
  return (
    <MapContainer center={config.mapCenter} zoom={config.mapZoom} className="h-[32rem] w-full" aria-label="Complaint map">
      <TileLayer {...OSM} />
      <FitToPoints points={points} />
      {showHeat && <HeatLayer points={heat} />}
      {showMarkers && points.map((p) => {
        const color = priorityStyle(p.priority_band).hex
        return (
          <CircleMarker key={p.id} center={[p.latitude, p.longitude]} radius={7}
                        pathOptions={{ color: '#fff', weight: 1.5, fillColor: color, fillOpacity: 0.9 }}>
            <Popup>
              <p className="font-semibold">{p.issue_type || 'Complaint'} ({shortId(p.id)})</p>
              <p>{p.priority_band || 'Unrated'}{p.priority_score != null ? ` \u2014 ${Math.round(p.priority_score)}/100` : ''}</p>
              <p>{statusLabel(p.status)}, {p.report_count} report{p.report_count === 1 ? '' : 's'}</p>
              <Link to={`/officer/complaints/${p.id}`} className="font-semibold text-civic underline">Open complaint</Link>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
