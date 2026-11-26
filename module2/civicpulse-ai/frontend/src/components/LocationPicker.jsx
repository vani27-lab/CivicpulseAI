import L from "leaflet";
import "leaflet/dist/leaflet.css";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import iconUrl from "leaflet/dist/images/marker-icon.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";
import { useEffect, useMemo, useState } from "react";
import { Circle, MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { useLanguage } from "../context/LanguageContext.jsx";

// Vite needs the marker pictures to be pointed out explicitly.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });

const START_CENTER = [22.5, 79.0]; // middle of India, used until a location is chosen
const START_ZOOM = 5;

const round = (n) => Math.round(n * 1e6) / 1e6;

function ClickToPlace({ onPick }) {
  useMapEvents({ click: (event) => onPick(event.latlng.lat, event.latlng.lng) });
  return null;
}

// Moves the map to a new GPS fix (but not when the user drags the pin).
function FlyTo({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.setView([target.lat, target.lng], Math.max(map.getZoom(), 17));
  }, [target, map]);
  return null;
}

/**
 * value:    null, or { latitude, longitude, accuracy (metres or null), source: "gps" | "manual_pin" }
 * onChange: called with a new value
 */
export default function LocationPicker({ value, onChange }) {
  const { t } = useLanguage();
  const [status, setStatus] = useState("idle"); // idle | finding | found | denied | unavailable | unsupported
  const [flyTarget, setFlyTarget] = useState(null);

  function findMe() {
    if (!navigator.geolocation) {
      setStatus("unsupported");
      return;
    }
    setStatus("finding");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        onChange({ latitude: round(latitude), longitude: round(longitude), accuracy: Math.round(accuracy), source: "gps" });
        setFlyTarget({ lat: latitude, lng: longitude });
        setStatus("found");
      },
      (error) => setStatus(error.code === 1 ? "denied" : "unavailable"),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
  }

  function placePin(lat, lng) {
    // The pin was moved by hand, so the old GPS accuracy no longer describes it.
    onChange({ latitude: round(lat), longitude: round(lng), accuracy: null, source: "manual_pin" });
  }

  const markerEvents = useMemo(
    () => ({
      dragend: (event) => {
        const { lat, lng } = event.target.getLatLng();
        placePin(lat, lng);
      },
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  let message = t("report.locNone");
  if (value?.source === "manual_pin") message = t("report.locManual");
  else if (value?.source === "gps") message = t("report.locGps", { m: value.accuracy });
  else if (status === "finding") message = t("report.locFinding");
  if (status === "denied" && value?.source !== "manual_pin") message = t("report.locDenied");
  if (status === "unavailable" && !value) message = t("report.locUnavailable");
  if (status === "unsupported" && !value) message = t("report.locUnsupported");

  return (
    <div className="space-y-3">
      <button type="button" className="btn btn-secondary" onClick={findMe} disabled={status === "finding"}>
        {status === "finding" ? t("report.locFinding") : t("report.locUse")}
      </button>

      <div
        role="application"
        aria-label={t("report.mapLabel")}
        className="relative z-0 h-72 overflow-hidden rounded-lg border border-line"
      >
        <MapContainer center={START_CENTER} zoom={START_ZOOM} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickToPlace onPick={placePin} />
          <FlyTo target={flyTarget} />
          {value && (
            <>
              <Marker
                position={[value.latitude, value.longitude]}
                draggable
                eventHandlers={markerEvents}
              />
              {value.source === "gps" && value.accuracy > 0 && (
                <Circle
                  center={[value.latitude, value.longitude]}
                  radius={value.accuracy}
                  pathOptions={{ color: "#2F6B8F", weight: 1 }}
                />
              )}
            </>
          )}
        </MapContainer>
      </div>

      <p role="status" className="text-sm text-muted">
        {message}
      </p>
    </div>
  );
}
