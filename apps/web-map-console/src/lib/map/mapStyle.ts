export const offlineMapStyle = {
  version: 8,
  sources: {
    "offline-tiles": {
      type: "vector",
      url: "pmtiles://offline-map.pmtiles"
    }
  },
  layers: [
    {
      id: "background",
      type: "background",
      paint: {
        "background-color": "#eef2f7"
      }
    }
  ]
};

export const fallbackCenter = {
  lng: 115.216667,
  lat: -8.65,
  zoom: 12
};

