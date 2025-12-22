import React, { useState, useEffect } from "react";

const PlayerAnalytics = ({ player }) => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch ML Prediction when player loads
  useEffect(() => {
    if (player?.name) {
      setLoading(true);
      fetch(`http://127.0.0.1:8000/predict/${player.name}`)
        .then((res) => res.json())
        .then((data) => {
          setPrediction(data.projected_fantasy_points);
          setLoading(false);
        })
        .catch((err) => {
          console.error("ML Error:", err);
          setLoading(false);
        });
    }
  }, [player]);

  if (!player) return null;

  return (
    <div className="bg-gray-800 p-4 rounded-lg mt-4 text-white shadow-lg">
      <h3 className="text-xl font-bold mb-4 border-b border-gray-600 pb-2">
        🧠 AI Analytics & Projections
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. ML Prediction Card */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 rounded-lg text-center">
          <p className="text-sm uppercase tracking-wide opacity-80">Next Game Projection</p>
          <div className="text-4xl font-extrabold my-2">
            {loading ? (
              <span className="animate-pulse">...</span>
            ) : (
              prediction || "N/A"
            )}
            <span className="text-lg font-normal ml-1">Pts</span>
          </div>
          <p className="text-xs italic opacity-75">Powered by Linear Regression</p>
        </div>

        {/* 2. Historical Context Card */}
        <div className="bg-gray-700 p-4 rounded-lg">
          <p className="text-sm uppercase tracking-wide opacity-80 mb-2">2025 Performance Context</p>
          
          {/* Percentile Rank */}
          <div className="flex justify-between items-center mb-2">
            <span>League Rank:</span>
            <span className="font-bold text-green-400">
               {player.comparison?.percentile || "N/A"}
            </span>
          </div>

          {/* Deltas (Year over Year) */}
          {player.comparison?.fantasy_points_delta && (
            <div className="flex justify-between items-center">
              <span>vs Last Year:</span>
              <span className={`font-bold ${player.comparison.fantasy_points_delta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {player.comparison.fantasy_points_delta > 0 ? "+" : ""}
                {player.comparison.fantasy_points_delta} Pts
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerAnalytics;