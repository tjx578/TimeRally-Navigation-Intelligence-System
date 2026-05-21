import type { StyleSpecification } from "maplibre-gl";
import { Protocol } from "pmtiles";

type MapLibreProtocolHost = {
  addProtocol?: unknown;
};

let pmtilesProtocolInstalled = false;

export function getPmtilesUrl() {
  return import.meta.env.VITE_PMTILES_URL ?? "";
}

export function getMapStyleUrl() {
  return import.meta.env.VITE_MAP_STYLE_URL ?? "";
}

export function installPmtilesProtocol(maplibre: MapLibreProtocolHost) {
  const pmtilesUrl = getPmtilesUrl();
  const addProtocol = maplibre.addProtocol as
    | ((scheme: string, handler: unknown) => void)
    | undefined;
  if (!pmtilesUrl || !addProtocol) {
    return false;
  }

  if (!pmtilesProtocolInstalled) {
    const protocol = new Protocol();
    addProtocol("pmtiles", protocol.tile);
    pmtilesProtocolInstalled = true;
  }
  return true;
}

export function buildOfflineStyle(usePmtiles: boolean): StyleSpecification | string {
  const mapStyleUrl = getMapStyleUrl();
  if (mapStyleUrl) {
    return mapStyleUrl;
  }

  const pmtilesUrl = getPmtilesUrl();
  if (usePmtiles && pmtilesUrl) {
    const url = pmtilesUrl.startsWith("pmtiles://") ? pmtilesUrl : `pmtiles://${pmtilesUrl}`;
    return {
      version: 8,
      sources: {
        "offline-tiles": {
          type: "vector",
          url
        }
      },
      layers: [
        {
          id: "background",
          type: "background",
          paint: { "background-color": "#e5edf6" }
        },
        {
          id: "landcover",
          type: "fill",
          source: "offline-tiles",
          "source-layer": "landcover",
          paint: { "fill-color": "#d9edc2", "fill-opacity": 0.72 }
        },
        {
          id: "landuse",
          type: "fill",
          source: "offline-tiles",
          "source-layer": "landuse",
          paint: { "fill-color": "#d1e8bd", "fill-opacity": 0.64 }
        },
        {
          id: "water",
          type: "fill",
          source: "offline-tiles",
          "source-layer": "water",
          paint: { "fill-color": "#a8d8f0" }
        },
        {
          id: "buildings",
          type: "fill",
          source: "offline-tiles",
          "source-layer": "building",
          minzoom: 13,
          paint: { "fill-color": "#d6cbc0", "fill-opacity": 0.72 }
        },
        {
          id: "roads-casing",
          type: "line",
          source: "offline-tiles",
          "source-layer": "transportation",
          paint: {
            "line-color": "#ffffff",
            "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.8, 13, 4.5],
            "line-opacity": 0.9
          }
        },
        {
          id: "roads",
          type: "line",
          source: "offline-tiles",
          "source-layer": "transportation",
          paint: {
            "line-color": "#60717d",
            "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.45, 13, 2.4],
            "line-opacity": 0.88
          }
        },
        {
          id: "transportation-name",
          type: "line",
          source: "offline-tiles",
          "source-layer": "transportation_name",
          minzoom: 12,
          paint: { "line-color": "#60717d", "line-width": 0.01, "line-opacity": 0.01 }
        },
      ]
    } as StyleSpecification;
  }

  return buildOnlineRasterFallbackStyle();
}

export function buildOnlineRasterFallbackStyle(): StyleSpecification {
  return {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap contributors"
      }
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#e5edf6" }
      },
      {
        id: "osm-raster",
        type: "raster",
        source: "osm",
        paint: { "raster-opacity": 0.96 }
      }
    ]
  } as StyleSpecification;
}
