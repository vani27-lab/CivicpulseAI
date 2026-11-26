import { useEffect } from 'react'
import L from 'leaflet'
import { useMap } from 'react-leaflet'

/** leaflet.heat attaches itself to the global L, so expose L before loading the plugin. */
export function HeatLayer({ points, radius = 28, blur = 20 }) {
  const map = useMap()
  useEffect(() => {
    let layer
    let cancelled = false
    window.L = L
    import('leaflet.heat').then(() => {
      if (cancelled || !points.length) return
      layer = L.heatLayer(points, { radius, blur, maxZoom: 16, minOpacity: 0.35 }).addTo(map)
    })
    return () => { cancelled = true; if (layer) map.removeLayer(layer) }
  }, [map, points, radius, blur])
  return null
}
