import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.11.2/dist/maplibre-gl.mjs';

const mapElement = document.querySelector('#garage-map');
const locationCards = [...document.querySelectorAll('.location-card')];

if (mapElement && locationCards.length) {
  const locations = locationCards.map((card) => ({
    card,
    name: card.dataset.name,
    address: card.dataset.address,
    hours: card.dataset.hours,
    point: [Number(card.dataset.lng), Number(card.dataset.lat)],
  }));
  const map = new maplibregl.Map({
    container: mapElement,
    style: 'https://tiles.openfreemap.org/styles/liberty',
    center: [77.641, 12.96],
    zoom: 10,
    attributionControl: false,
    cooperativeGestures: true,
  });
  const markers = [];

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.addControl(new maplibregl.AttributionControl({
    compact: false,
    customAttribution: '<a href="https://openfreemap.org/">OpenFreeMap</a> · © <a href="https://openmaptiles.org/">OpenMapTiles</a> · <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }), 'bottom-right');

  map.once('style.load', () => {
    const bounds = new maplibregl.LngLatBounds();
    locations.forEach((location) => {
      const markerElement = document.createElement('button');
      markerElement.className = 'garage-map-marker';
      markerElement.type = 'button';
      markerElement.setAttribute('aria-label', location.name);

      const popup = document.createElement('div');
      const name = document.createElement('strong');
      const address = document.createElement('div');
      const hours = document.createElement('small');
      name.textContent = location.name;
      address.textContent = location.address;
      hours.textContent = location.hours;
      popup.append(name, address, hours);

      const marker = new maplibregl.Marker({ element: markerElement, anchor: 'bottom' })
        .setLngLat(location.point)
        .setPopup(new maplibregl.Popup({ offset: 22 }).setDOMContent(popup))
        .addTo(map);
      markerElement.addEventListener('click', () => selectLocation(location));
      location.card.addEventListener('click', (event) => {
        if (event.target.closest('.location-directions')) return;
        selectLocation(location);
        map.flyTo({ center: location.point, zoom: 15, duration: 700 });
        marker.togglePopup();
      });
      markers.push(marker);
      bounds.extend(location.point);
    });
    if (markers.length === 1) map.setZoom(14);
    else map.fitBounds(bounds, { padding: 36, maxZoom: 12 });
    mapElement.classList.add('is-ready');
  });

  function selectLocation(location) {
    locationCards.forEach((card) => card.classList.remove('is-selected'));
    location.card.classList.add('is-selected');
  }

  map.on('error', () => {
    if (!mapElement.classList.contains('is-ready')) mapElement.classList.add('map-error');
  });
}