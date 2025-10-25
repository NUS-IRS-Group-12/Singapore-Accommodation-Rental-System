"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from "leaflet";

export default function ListingDetailPage() {
  const params = useParams();
  const { id, user_id } = params;
  const [listing, setListingDetails] = useState({});
  const [metrics, setMetric] = useState([]);
  const [position, setPosition] = useState([]);
  const [loaded, setLoading] = useState(false)

  const houseIcon = new L.Icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/69/69524.png",
    iconSize: [32, 32],
  });

  const urllistings = `http://localhost:8000/properties/${id}/details`;

  useEffect(() => {
    fetchDetails();
  }, []);

  async function fetchDetails() {
    const response = await fetch( urllistings,
      { method: "POST", headers: {'Content-Type': 'application/json',},
      body: JSON.stringify({ user_id: user_id }) }
    );
    const data = await response.json();
    data.amenities = data.amenities.replace(/[\[\]"]+/g, '').replace('\\u',' ');
    setListingDetails(data);
    setPosition([data.latitude, data.longitude]);
    setLoading(true);
    setMetric([
      {label: 'Accuracy', value: data.review_scores_accuracy, icon: '🎯'},
      {label: 'Cleanliness', value: data.review_scores_cleanliness, icon: '🧹'},
      {label: 'Check-in', value: data.review_scores_checkin, icon: '🔑'},
      {label: 'Communication', value: data.review_scores_communication, icon: '💬'},
      {label: 'Location', value: data.review_scores_location, icon: '📍'},
      {label: 'Value', value: data.review_scores_value, icon: '💰',}
    ]);
  }

  return (
    <main className="min-h-screen bg-gray-50 p-6 text-black">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-md overflow-hidden">
        <img src={listing.picture_url} className="w-full h-96 object-cover"/>
        <div className="p-4">
          <h1 className="text-3xl font-bold mb-1">
            {listing.property_name}
          </h1>
          <p className="text-2xl font-semibold text-gray-800 mb-1">
            Price: ${listing.price} SGD
          </p>
          <p className="text-2xl text-gray-700 mb-1">★ {listing.review_scores_rating}</p>
          <div className="text-m text-gray-800 mb-2">
            <div>{listing.neighbourhood_cleansed}, {listing.neighbourhood_group_cleansed}</div>
            <div>{listing.bedrooms} Bedrooms • {listing.beds} Beds • {listing.bathrooms} Bathrooms</div>
            <div>{listing.accommodates} guests • {listing.property_type} • {listing.room_type}</div>
          </div>
          <hr className="mb-3"></hr>
          <div className="text-2xl"> Ratings </div>
          <div className="grid grid-cols-2 grid-cols-3 gap-4 p-6">
            {metrics.map((metric, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-xl p-4 text-center hover:shadow-md transition-shadow">
                <div className="text-2xl mb-2">{metric.icon}</div>
                <div className="text-sm font-medium text-gray-600 mb-1">{metric.label}</div>
                <div className="text-xl font-bold text-gray-800">{metric.value}</div>
                <div className="text-xs text-gray-400 mt-1">/5 rating</div>
              </div>
            ))}
          </div>
          <hr className="mb-3"></hr>
          <div className="text-2xl"> Amenities </div>
          <div>{listing.amenities}</div>
        </div>
        {loaded && (<MapContainer center={position} zoom={17} style={{ height: '400px', width: '100%' }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
            <Marker position={position} icon={houseIcon}>
            </Marker>
        </MapContainer>)}
      </div>
    </main>
  );
}