// src/pages/Home.jsx
// Landing page with hero and centered search bar.
// On submit, it performs client-side navigation to /search?q=...
import robot from "./assets/robot.png";
import SearchBar from "./components/SearchBar.jsx";

export default function Home() {
  // Parent handler passed to SearchBar. It updates the browser history
  // so the in-file router (see src/main.jsx) renders the Results page.
  function handleSearch(query) {
    // Build new URL with query param
    const url = "/search?" + new URLSearchParams({ q: query }).toString();
    // Push a new history entry without full page reload
    window.history.pushState({}, "", url);
    // Notify our simple router to re-evaluate location
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  return (
    <div className="min-h-dvh bg-gradient-to-r from-[#500000] via-orange-500 to-[#500000] flex flex-col items-center justify-center text-white px-6 py-10">
      {/* Hero image */}
      <img
        src={robot}
        alt="Rusty the Patent Miner"
        className="w-40 sm:w-56 md:w-72 lg:w-96 xl:w-[520px] h-auto mx-auto mb-4"
      />
      {/* Title + subtitle */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white drop-shadow-lg tracking-tight mb-2 text-center">
        The Patent Miner
      </h1>
      <p className="text-base sm:text-lg text-white/90 mb-8 text-center">
        Rusty uncovers innovation, one swing at a time ⚒️
      </p>

      {/* Centered search bar */}
      <div className="w-full flex justify-center px-2">
        <SearchBar onSearch={handleSearch} />
      </div>
    </div>
  );
}
