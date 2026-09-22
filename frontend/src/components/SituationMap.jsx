import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function SituationMap({
  pairId,
  selectedDistrict,
  baseMapType = 'satellite',
  activeLayers = { flood: true, water_pre: true, water_peak: false },
  layersData = {},
  inspectorData,
  onMapClick
}) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const baseLayersRef = useRef({});
  const layerGroupsRef = useRef({
    water_pre: null,
    water_peak: null,
    flood: null
  });
  const inspectMarkerRef = useRef(null);

  // 1. Initialize map and dedicated panes once
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [50.29, 127.54],
      zoom: 11,
      minZoom: 6,
      maxZoom: 17,
      zoomControl: false,
    });

    // Create Dedicated Panes with Fixed Z-Index Hierarchy
    // Guarantees flood is ALWAYS visible on top of river water!
    const riverPane = map.createPane('riverPane');
    riverPane.style.zIndex = '410'; // Bottom: natural river bed

    const peakPane = map.createPane('peakPane');
    peakPane.style.zIndex = '420'; // Middle: peak water extent

    const floodPane = map.createPane('floodPane');
    floodPane.style.zIndex = '430'; // Top: newly flooded zones ALWAYS visible on top!

    // CartoDB Positron / Dark Reference for GIS Schema Mode
    const darkBase = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Esri, HERE, Garmin',
      maxZoom: 16
    });

    const darkLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      attribution: '',
      maxZoom: 16
    });

    const darkGroup = L.layerGroup([darkBase, darkLabels]);

    // High-Resolution Satellite World Imagery (No API keys, No watermarks)
    const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Source: Esri, Maxar Earthstar',
      maxZoom: 17
    });

    baseLayersRef.current = {
      dark: darkGroup,
      satellite: satLayer
    };

    // Add satellite layer by default as requested
    if (baseMapType === 'satellite') {
      satLayer.addTo(map);
    } else {
      darkGroup.addTo(map);
    }

    // Zoom control at bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Map click for inspector
    map.on('click', (e) => {
      const { lat, lng } = e.latlng;
      if (onMapClick) {
        onMapClick(lat, lng);
      }
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Basemap switching (Dark vs Satellite)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !baseLayersRef.current.dark) return;

    if (baseMapType === 'satellite') {
      map.removeLayer(baseLayersRef.current.dark);
      baseLayersRef.current.satellite.addTo(map);
    } else {
      map.removeLayer(baseLayersRef.current.satellite);
      baseLayersRef.current.dark.addTo(map);
    }
  }, [baseMapType]);

  // 3. Center on district change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const districtCenters = {
      blagoveshchensk: [50.29, 127.54],
      svobodny: [51.38, 128.13],
      belogorsk: [50.92, 128.47],
      konstantinovka: [49.62, 127.98],
      poyarkovo: [49.62, 128.66],
    };

    if (selectedDistrict && districtCenters[selectedDistrict]) {
      map.setView(districtCenters[selectedDistrict], 11);
      map.invalidateSize({ animate: false });
    }
  }, [selectedDistrict, pairId]);

  // 4. Unified Layer Sync: Re-renders layers automatically on data change OR activeLayers toggle!
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const layerConfigs = {
      water_pre: {
        pane: 'riverPane',
        style: {
          color: '#0055CC',
          weight: 1.5,
          opacity: 0.95,
          fillColor: '#007AFF',
          fillOpacity: 0.58,
        },
        label: 'Русло реки до паводка',
        textColor: 'text-blue-400'
      },
      water_peak: {
        pane: 'peakPane',
        style: {
          color: '#009688',
          weight: 1.5,
          opacity: 0.85,
          fillColor: '#00C7BE',
          fillOpacity: 0.5,
        },
        label: 'Вода на пике разлива',
        textColor: 'text-teal-400'
      },
      flood: {
        pane: 'floodPane',
        style: {
          color: '#D70015',
          weight: 2,
          opacity: 1.0,
          fillColor: '#FF3B30',
          fillOpacity: 0.72,
        },
        label: 'Зона нового затопления',
        textColor: 'text-red-400'
      }
    };

    let hasRendered = false;

    // Synchronize each layer with current data and visibility
    Object.keys(layerConfigs).forEach((key) => {
      // Remove previous layer instance from map
      if (layerGroupsRef.current[key]) {
        map.removeLayer(layerGroupsRef.current[key]);
        layerGroupsRef.current[key] = null;
      }

      // Check if data matches current active pairId (avoids drawing old city polygons during switch)
      const isMatchingPair = !layersData?.pair_id || layersData.pair_id === pairId;
      const isVisible = !!activeLayers[key];
      const data = isMatchingPair && layersData ? layersData[key] : null;
      const cfg = layerConfigs[key];

      // Add to map immediately if visible and features are present
      if (isVisible && data && data.features && data.features.length > 0) {
        const geoLayer = L.geoJSON(data, {
          pane: cfg.pane,
          style: () => cfg.style,
          onEachFeature: (feature, layer) => {
            const props = feature.properties || {};
            layer.bindTooltip(
              `<div class="font-sans text-xs space-y-0.5">
                <div class="font-semibold ${cfg.textColor}">
                  ${cfg.label}
                </div>
                <div class="text-slate-300">Площадь: <b class="text-white">${props.area_ha || 0} га</b> (${props.area_km2 || 0} км²)</div>
              </div>`,
              { sticky: true, className: 'hud-tooltip' }
            );

            layer.on('click', (e) => {
              if (onMapClick && e.latlng) {
                onMapClick(e.latlng.lat, e.latlng.lng);
              }
            });
          }
        });

        geoLayer.addTo(map);
        layerGroupsRef.current[key] = geoLayer;
        hasRendered = true;
      }
    });

    if (hasRendered && mapInstanceRef.current) {
      mapInstanceRef.current.invalidateSize({ animate: false });
    }

  }, [layersData, activeLayers, pairId]);

  // 5. Inspector Marker Pin
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (inspectMarkerRef.current) {
      map.removeLayer(inspectMarkerRef.current);
      inspectMarkerRef.current = null;
    }

    if (inspectorData && inspectorData.coordinates) {
      const { lat, lon } = inspectorData.coordinates;
      const customIcon = L.divIcon({
        className: 'radar-pin',
        html: `<div class="relative flex items-center justify-center">
          <span class="absolute w-8 h-8 rounded-full bg-[#007AFF] animate-ping opacity-75"></span>
          <span class="w-4 h-4 rounded-full bg-[#007AFF] border-2 border-white shadow-xl"></span>
        </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker([lat, lon], { icon: customIcon }).addTo(map);
      inspectMarkerRef.current = marker;
    }
  }, [inspectorData]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapRef} className="w-full h-full z-0" />
    </div>
  );
}
