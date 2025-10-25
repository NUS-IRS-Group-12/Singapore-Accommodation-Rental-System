"use client";
import { useState, useEffect } from "react";
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [isloggedIn, setIsLoggedIn] = useState(false);
  const [user_id, setUserId] = useState(0);
  const [showSignIn, setShowSignIn] = useState(false);
  const [showMenu, setMenu] = useState(false);
  const [listings, setListings] = useState([]);
  const [sortOption, setSortOption] = useState("");
  const [display, setDisplay] = useState("");
  const [favlistings, setFavListings] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [duration, setDuration] = useState("2");

  const urlHome = "http://localhost:8000/properties?";
  const urlLogin = "http://localhost:8000/login";
  const urlRec = "http://localhost:8000/recommend"; // POST User ID
  const urlFav = "http://localhost:8000/liked-properties"; // POST User ID
  const urlSearch = "http://localhost:8000/search"; // POST Property ID

  const [selectedTypes, setSelectedTypes] = useState({
    'Private room': true,
    'Entire home/apt': true,
    'Hotel room': true,
    'Shared room': true
  });
  const [selectedRegions, setSelectedRegions] = useState({
    'Central': true,
    'East': true,
    'North': true,
    'North-East': true,
    'West': true
  });
  const [selectedAccomodates, setSelectedAccomodates] = useState({
    '1-2': true,
    '3-4': true,
    '5-6': true,
    '7 +': true
  });

  const houseTypes = ["Private room", "Entire home/apt", "Hotel room", "Shared room"];
  const regions = ["Central", "East", "North", "North-East", "West"];
  const accomodates = ['1-2', '3-4', '5-6', '7 +'];
 
  // Helpers for filters, convert to string for parameters API
  function getValuesAsString(obj) {
    const trueValues = [];
    
    for (const [key, value] of Object.entries(obj)) {
      if (value === true) {
        trueValues.push(key);
      }
    }
    
    return trueValues.join(',');
  }

  useEffect(() => {
    fetchListings();
  }, []);

  async function fetchFav() {
    try{
      const res = await fetch(urlFav , {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: user_id }),
      });
      if (!res.ok) {
        throw new Error(`HTTP error!`);
      }
      const data = await res.json();
      const dataf_id = data.map(item => item.property_id)
      setFavListings(dataf_id);
      setListings(data);
      setDisplay("Your Favourites");
    } catch (error) {
      setListings([])
      setDisplay("Your Favourites");
    }
  }

  async function fetchRec() {
    try {
      const res = await fetch(urlRec , {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: user_id}),
      });
      if (!res.ok) {
        throw new Error(`HTTP error!`);
      }
      const data = await res.json();
      setListings(data);
      setDisplay("Recommended for you");
    } catch (error) {
      setListings([])
      setDisplay("Recommended for you");
    }
  }

  async function fetchListings() {
    try {
      if (duration == "1") {
        setSelectedTypes({
          'Private room': false,
          'Entire home/apt': false,
          'Hotel room': true,
          'Shared room': false
        })
      }
      const params = {
        types: getValuesAsString(selectedTypes),
        regions: getValuesAsString(selectedRegions),
        accomodates: getValuesAsString(selectedAccomodates),
        page: page
      };
      const queryString = new URLSearchParams(params).toString();
      const response = await fetch(urlHome + queryString);
      if (!response.ok) {
          throw new Error(`HTTP error!`);
        }
      const json = await response.json();
      const data = json.data;
      setListings(data);
      if (json.total == 0) {
        setTotalPages(1);
      } else {
        const tp =  Math.ceil(json.total / 12);
        setTotalPages(tp);
      }
      setDisplay("Top Listings");
    } catch (error) {
      setDisplay("Top Listings");
      setTotalPages(1);
      setListings([]);
    }
  }

  async function sendLikes(id) {
    const response = await fetch('http://localhost:8000/properties/'+ id.toString() +'/like' , {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user_id }),
    });
    setFavListings((prev) =>prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]);
  };
 
  // handlers for filters
  const handleType = (type) => (e) => {
    setSelectedTypes(prev => ({
      ...prev,
      [type]: e.target.checked
    }));
  }
  const handleRegion = (region) => (e) => {
    setSelectedRegions(prev => ({
      ...prev,
      [region]: e.target.checked
    }));
  }
  const handleAcc = (accomod) => (e) => {
    setSelectedAccomodates(prev => ({
      ...prev,
      [accomod]: e.target.checked
    }));
  }
  const handleApplyFilters = async () => {
    setPage(1);
    await fetchListings();
   };
 
  // helpers for sorting
  const parsePrice = (p) => {
    if (p == null) return 0;
    const n = Number(String(p).replace(/[^\d.-]/g, ""));
    return Number.isFinite(n) ? n : 0;
  };
  const parseRating = (item) => {
    if (!item || item.rating == null) return 0;
    const r = Number(item.rating);
    return r;
  }
  const sortedListings = [...listings].sort((a, b) => {
    if (sortOption === "") return parseRating(b) - parseRating(a);
    if (sortOption === "price-asc") return parsePrice(a.price) - parsePrice(b.price);
    if (sortOption === "price-desc") return parsePrice(b.price) - parsePrice(a.price);
    return 0;
  });

  const handleLogin = async (username, password) => {
    const res = await fetch(urlLogin , {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
    });
    const data = await res.json();
    if (data.message =='ok' && data.user_id) {
      setIsLoggedIn(true);
      setUserId(data.user_id);
      setShowSignIn(false);
      const resF = await fetch(urlFav , {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: data.user_id }),
      });
      const dataF = await resF.json();
      const dataf_id = dataF.map(item => item.property_id)
      setFavListings(dataf_id);
    } else {
      alert("Login failed. Please check your credentials.");
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserId(0);
  }
 
  // Chat state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { id: 1, from: "bot", text: "Hi, how can I help you today?" }
  ]);
  const [chatInput, setChatInput] = useState("");

  const urlChat = "http://localhost:8001/chat";

  async function handleSendMessage(e) {
    if (e && e.preventDefault) e.preventDefault();
    const text = (chatInput || "").trim();
    if (!text) return;
    const userMsg = { id: Date.now(), from: "user", text };
    setChatMessages((m) => [...m, userMsg]);
    setChatInput("");
    const res = await fetch(urlChat, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id:user_id , prompt: text }),
    });
    if (!res.ok) throw new Error(`HTTP error!`);
    const replyText = await res.text(); 
    if (typeof replyText == 'string') {
      const cleaned = replyText.replace("Returning structured response: ResponseFormat\(response=", '')
      .replace(/\"/g,'').replace(/\'/g,'').replace(/\(/g,'').replace(/\)/g,'').replace(/\\\\n/g, '\\n');
      const botMsg = { id: Date.now() + 1, from: "bot", text: cleaned };
      setChatMessages((m) => [...m, botMsg]);
    } else {
      const botMsg = { id: Date.now() + 1, from: "bot", text: 'An error occurred, please try again' };
      setChatMessages((m) => [...m, botMsg]);
    }
  };

  async function handleSearch(id) {
    const pid = id.trim();
    try {
      const res = await fetch(urlSearch , {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pid: pid }),
      });
      if (!res.ok) {
        throw new Error(`HTTP error!`);
      }
      const data = await res.json();
      setListings(data);
      setDisplay("Search Result");
    } catch (error) {
      setListings([])
      setDisplay("Search Result");
    }
  }

  return (
    <>
      <main className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm py-4 px-8 flex items-center justify-between mb-8 sticky top-0 z-40">
          <span className="text-xl font-bold text-blue-700 cursor-pointer" onClick={()=>fetchListings()}>Rental System</span>
          <div className="mb-3 h-10 bg-gray-100 cursor-pointer rounded-xl pl-1">
              <input id='search' type="text" placeholder="Search Id" className="text-black text-xl outline-none"/>
              <button className="text-m bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700 cursor-pointer" onClick={() => handleSearch(document.querySelector('#search').value)}>
                Search
              </button>
          </div>
          <div className="flex items-center gap-4">
            <button
              className="bg-blue-600 text-white px-4 py-2 rounded-full hover:bg-blue-700 cursor-pointer transition"
              onClick={() => setMenu(showMenu => !showMenu)}
            >
              ☰
            </button>
          </div>
        </nav>

        {showMenu && (
          <div className="fixed z-1 top-19 right-2">
            <div className="bg-white rounded-4xl shadow-lg p-8 w-full max-w-3xl relative z-60 text-black">
              {isloggedIn ? (
                <button
                  className="w-full h-15 text-xl rounded-2xl hover:bg-gray-200 cursor-pointer"
                  onClick={() => {handleLogout(); setMenu(false);}}
                >
                  Log Out
                </button>
              ) : 
              (<button
                className="w-full h-15 text-xl rounded-2xl hover:bg-gray-200 cursor-pointer"
                onClick={() => {setMenu(false); setShowSignIn(true);}}
              >
                Log in or sign up
              </button>)}
              <button
                className="w-full h-15 text-xl rounded-2xl hover:bg-gray-200 cursor-pointer"
                onClick={() => {
                  if (!isloggedIn) {
                    setShowSignIn(true)
                  } else {
                    fetchFav();
                  }
                }}
              >
                Favourites
              </button>
              <button
                className="w-full h-15 text-xl rounded-2xl hover:bg-gray-200 cursor-pointer"
                onClick={() => {
                  if (!isloggedIn) {
                    setShowSignIn(true)
                  } else {
                    fetchRec();
                  }
                }}
              >
                Recommended for you
              </button>
            </div>
          </div>
        )}

        {showSignIn && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.1)]">
            <div className="bg-white rounded-4xl shadow-lg p-8 w-full max-w-3xl relative z-60 text-black">
              <div>
                <span
                  className="absolute top-6 left-10 w-10 h-10 rounded-full text-4xl flex justify-center items-center hover:bg-gray-100 cursor-pointer"
                  onClick={() => setShowSignIn(false)}
                >
                  <div>&times;</div>
                </span>
                <h2 className="text-xl font-bold mb-8 text-center">
                  Log in or Sign up
                </h2>
              </div>
              <hr className="my-4 border-t"></hr>
              <h2 className="text-3xl mb-7">Welcome to Singapore Rental</h2>
              <input
                id='username'
                type="text"
                placeholder="Username"
                className="w-full mb-3 h-18 px-3 py-2 border rounded-2xl"
              />
              <input
                type="password"
                placeholder="Password"
                className="w-full mb-6 h-18 px-3 py-2 border rounded-2xl"
              />
              <button className="w-full h-15 text-2xl bg-blue-600 text-white py-2 rounded-2xl hover:bg-blue-700 cursor-pointer mb-10" onClick={() => handleLogin(document.querySelector('#username').value, document.querySelector('input[type="password"]').value)}>
                Continue
              </button>
              <hr className="my-4 border-t"></hr>
            </div>
          </div>
        )}

        <div className="flex">
          { /* Sidebar filter */}
          <aside className="w-64 text-black bg-white rounded-2xl shadow-md p-6 mr-8 mt-2 flex-shrink-0">
            <h3 className="text-lg font-bold mb-4 text-blue-700">
              Filter Listings
            </h3>
            
            {/* Sort Listings */}
            <div className="mb-6">
              <label className="block font-semibold mb-2">Sort</label>
              <select
                value={sortOption}
                onChange={(e) => setSortOption(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="">Ratings</option>
                <option value="price-asc">Price: Low → High</option>
                <option value="price-desc">Price: High → Low</option>
              </select>
            </div>

            {/* Stay Duration */}
            {display == "Top Listings" &&  <div className="mb-6">
              <label className="block font-semibold mb-2">Stay Duration</label>
              <select
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="1">Less than 3 Months</option>
                <option value="2">Longer than 3 Month</option>
              </select>
            </div>}

            {display == "Top Listings" && <div>
              <div className="mb-6">
                <label className="block font-semibold mb-2">
                  House Type
                </label>
                <div className="flex flex-col gap-2">
                  {houseTypes.map((check_type) => (
                    <label key={check_type} className="flex items-center gap-2 cursor-pointer">
                      {duration == "1" && <input type="checkbox" checked={check_type=="Hotel room"} disabled={true} className="accent-blue-600"/>}
                      {duration == "2" && <input type="checkbox" checked={selectedTypes[check_type]} onChange={handleType(check_type)} className="accent-blue-600"/>}
                      <span>{check_type}</span>
                    </label>
                  ))}
                </div>
              </div>
              {/* Region Filter */}
              <div className="mb-6">
                <label className="block font-semibold mb-2">
                  Regions
                </label>
                <div className="flex flex-col gap-2">
                  {regions.map((region) => (
                    <label key={region} className="flex items-center cursor-pointer gap-2">
                      <input type="checkbox" checked={selectedRegions[region]} onChange={handleRegion(region)} className="accent-blue-600"/>
                      <span>{region}</span>
                    </label>
                  ))}
                </div>
              </div>
              {/* Accoomodates Filter */}
              <div className="mb-6">
                <label className="block font-semibold mb-2">
                  Number of Guests
                </label>
                <div className="flex flex-col gap-2">
                  {accomodates.map((accomod) => (
                    <label key={accomod} className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={selectedAccomodates[accomod]} onChange={handleAcc(accomod)} className="accent-blue-600"/>
                      <span>{accomod}</span>
                    </label>
                  ))}
                </div>
              </div>
              {/* Apply Filters button */}
              <div className="mt-4">
                <button onClick={handleApplyFilters} className="w-full bg-blue-600 text-white py-2 rounded-2xl cursor-pointer hover:bg-blue-700">
                  Apply filters
                </button>
              </div>
            </div>}
          </aside>

          {/* Listings section */}
          <div className="flex-1">
            <section className="mb-12 bg-gray-50">
              <h2 className="text-black text-2xl font-semibold mb-6">
                {display}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-8 bg-gray-50">
                {sortedListings.map((listing) => (
                  <div key={listing.property_id} className="bg-gray-50 rounded-lg flex flex-col h-full overflow-hidden relative cursor-pointer hover:shadow-lg transition-shadow duration-200">
                    <img src={listing.image_url} className="w-full h-64 object-cover rounded-4xl"/>
                    {isloggedIn && favlistings.includes(listing.property_id) && <button className="absolute top-3 right-6 bg-opacity-0 rounded-full hover:scale-120 transition-transform duration-150" onClick={()=>sendLikes(listing.property_id)}> 
                        <svg fill="rgba(223, 16, 71, 0.62)" viewBox="0 0 24 24" strokeWidth={2.2} stroke="white" className="w-7 h-7">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M4.318 6.318a5.5 5.5 0 0 1 7.778 0l.904.903.904-.903a5.5 5.5 0 1 1 7.778 7.778l-8.682 8.682a1 1 0 0 1-1.414 0l-8.682-8.682a5.5 5.5 0 0 1 0-7.778z"
                          />
                        </svg>
                      </button>
                    }
                    {isloggedIn && !favlistings.includes(listing.property_id) && <button className="absolute top-3 right-6 bg-opacity-0 rounded-full hover:scale-120 transition-transform duration-150" onClick={()=>sendLikes(listing.property_id)}>
                        <svg fill="rgba(229, 231, 235, 0.4)" viewBox="0 0 24 24" strokeWidth={2.2} stroke="white" className="w-7 h-7">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M4.318 6.318a5.5 5.5 0 0 1 7.778 0l.904.903.904-.903a5.5 5.5 0 1 1 7.778 7.778l-8.682 8.682a1 1 0 0 1-1.414 0l-8.682-8.682a5.5 5.5 0 0 1 0-7.778z"
                          />
                        </svg>
                      </button>
                    }
                    <Link href={`/properties/${listing.property_id}/user/${user_id}`} target="_blank">
                      <div className="flex-1 w-full text-left">
                        <div className="p-4 text-left">
                          <h2 className="text-gray-800 text-xl font-semibold mb-2">
                            {listing.room_type} in {listing.region}
                          </h2>
                          <p className="text-gray-800 font-bold mb-2">
                            $ {listing.price}
                          </p>
                          <p className="text-gray-500 text-sm mb-4">
                            ★ {listing.rating}
                          </p>
                        </div>
                      </div>
                    </Link>
                  </div>
                ))}
              </div>

              {/* Pagination controls */}
              {display == "Top Listings" && <div className="mt-6 flex items-center justify-center gap-3 text-black">
                <button
                  onClick={() => {
                    setPage((p) => Math.max(1, p - 1))
                    fetchListings();
                  }}
                  disabled={page <= 1}
                  className="px-3 py-1 bg-white border rounded disabled:opacity-50"
                >
                  Prev
                </button>
                <div className="text-sm">
                  Page {page} of {totalPages}
                </div>
                <button
                  onClick={() => {
                    setPage((p) => Math.min(totalPages, p + 1))
                    fetchListings();
                  }}
                  disabled={page >= totalPages}
                  className="px-3 py-1 bg-white border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>}
             </section>
           </div>
         </div>

        {/* Chat window (bottom-right) */}
        {isloggedIn && <div className="fixed bottom-4 right-4 z-50">
          <div className="flex flex-col items-end">
            {chatOpen && (
              <div className="w-150 bg-white rounded-xl shadow-lg overflow-hidden mb-3">
                <div className="px-4 py-2 bg-blue-600 text-white flex items-center justify-between">
                  <div className="font-semibold">Rental Agent</div>
                  <button
                    onClick={() => setChatOpen(false)}
                    className="text-white cursor-pointer"
                  >
                    ✕
                  </button>
                </div>
                <div className="h-150 overflow-y-auto p-3 space-y-2 bg-gray-50">
                  {chatMessages.map((m) => (
                    <div key={m.id} className={m.from === "user" ? "text-right" : "text-left"}>
                      <div className={`inline-block p-2 rounded-lg ${m.from === "user" ? "bg-blue-600 text-white" : "bg-white text-gray-800 border"}`}>
                        <ReactMarkdown>
                          {m.text.replace(/\\n/g, "\n")}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
                <form onSubmit={handleSendMessage} className="p-3 bg-white text-black flex gap-2">
                  <input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    className="flex-1 px-3 py-2 border rounded-lg"
                    placeholder="Ask about listings..."/>
                  <button type="submit" className="w-10 h-10 bg-blue-600 text-white text-xl rounded-full cursor-pointer">
                    ↑
                  </button>
                </form>
              </div>
            )}

            <button
              onClick={() => setChatOpen((s) => !s)}
              className="w-16 h-16 rounded-full text-3xl bg-blue-600 text-white cursor-pointer shadow-lg flex items-center justify-center"
            >
              💬
            </button>
          </div>
        </div>}
      </main>
    </>
  );
}