import type { StyleSpecification } from "maplibre-gl";

type MapLibreProtocolHost = {
  addProtocol?: unknown;
};

declare global {
  interface Window {
    pmtiles?: {
      Protocol: new () => {
        tile: (params: unknown, callback: unknown) => void;
      };
    };
  }
}

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
  if (!pmtilesUrl || !window.pmtiles?.Protocol || !addProtocol) {
    return false;
  }

  const protocol = new window.pmtiles.Protocol();
  addProtocol("pmtiles", protocol.tile);
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
        }
      ]
    } as StyleSpecification;
  }

  return {
    version: 8,
    sources: {},
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#e5edf6" }
      }
    ]
  } as StyleSpecification;
}
