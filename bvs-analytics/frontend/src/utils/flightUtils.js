// Утилиты для обработки данных полетов
export const processFlightData = (flights) => {

    return flights.map(flight => {
        const hasDeparture = flight.dep && flight.dep.lat && flight.dep.lon;
        const hasArrival = flight.arr && flight.arr.lat && flight.arr.lon;


        return {
            ...flight,
            hasValidRoute: hasDeparture && hasArrival,
            isCircular: hasDeparture && hasArrival &&
                flight.dep.lat === flight.arr.lat &&
                flight.dep.lon === flight.arr.lon
        };
    });
};

// Создание GeoJSON для точек
export const createPointsGeoJSON = (flights) => {
    // Проверяем входные данные
    if (!flights || !Array.isArray(flights)) {
        console.error('createPointsGeoJSON: flights не является массивом', flights)
        return {
            type: 'FeatureCollection',
            features: []
        }
    }

    const features = flights.map((flight, index) => {
        // Проверяем наличие координат departure
        if (flight.dep && flight.dep.lat !== null && flight.dep.lon !== null) {
            return {
                type: 'Feature',
                properties: {
                    flightId: flight.sid || `flight-${index}`,
                    center_name: flight.center_name || 'Неизвестно',
                    uav_type: flight.uav_type || 'Неизвестно',
                    operator: flight.operator || 'Неизвестно'
                },
                geometry: {
                    type: 'Point',
                    coordinates: [flight.dep.lon, flight.dep.lat] // [longitude, latitude]
                }
            }
        }
        console.warn('Полет без координат departure:', flight)
        return null
    }).filter(feature => feature !== null)

    console.log('Создано features:', features.length)

    return {
        type: 'FeatureCollection',
        features: features
    }
}
// Создание GeoJSON для линий маршрутов
export const createRoutesGeoJSON = (flights) => {
    const features = flights
        .filter(flight => flight.dep && flight.dep.lat && flight.dep.lon &&
            flight.arr && flight.arr.lat && flight.arr.lon &&
            !(flight.dep.lat === flight.arr.lat && flight.dep.lon === flight.arr.lon))
        .map(flight => ({
            type: 'Feature',
            properties: {
                flightId: flight.sid,
                uavType: flight.uav_type,
                duration: flight.duration_min,
                center: flight.center_name,
                operator: flight.operator
            },
            geometry: {
                type: 'LineString',
                coordinates: [
                    [flight.dep.lon, flight.dep.lat],
                    [flight.arr.lon, flight.arr.lat]
                ]
            }
        }));

    return {
        type: 'FeatureCollection',
        features
    };
};

// Создание GeoJSON для круговых полетов (зоны)
export const createZonesGeoJSON = (flights) => {
    const features = flights
        .filter(flight => flight.shr && flight.shr.zone_center_lat && flight.shr.zone_center_lon)
        .map(flight => ({
            type: 'Feature',
            properties: {
                flightId: flight.sid,
                uavType: flight.uav_type,
                radius: flight.shr.zone_radius_nm,
                center: flight.center_name,
                window: `${flight.shr.window_start_hhmm}-${flight.shr.window_end_hhmm}`
            },
            geometry: {
                type: 'Point',
                coordinates: [flight.shr.zone_center_lon, flight.shr.zone_center_lat]
            }
        }));

    return {
        type: 'FeatureCollection',
        features
    };
};

export const getFlightType = (flight) => {
    if (!flight.dep || !flight.dep.lat || !flight.dep.lon) return 'unknown';

    if (!flight.arr || !flight.arr.lat || !flight.arr.lon) return 'one_way';

    if (flight.dep.lat === flight.arr.lat && flight.dep.lon === flight.arr.lon) {
        return 'circular';
    }

    return 'route';
};

// Улучшенная обработка данных
export const enhanceFlightData = (flight) => {
    const type = getFlightType(flight);

    return {
        ...flight,
        flightType: type,
        hasValidDeparture: !!flight.dep?.lat && !!flight.dep?.lon,
        hasValidArrival: !!flight.arr?.lat && !!flight.arr?.lon,
        isCompleted: !!flight.duration_min,
        coordinates: {
            departure: flight.dep ? [flight.dep.lon, flight.dep.lat] : null,
            arrival: flight.arr ? [flight.arr.lon, flight.arr.lat] : null
        }
    };
};
