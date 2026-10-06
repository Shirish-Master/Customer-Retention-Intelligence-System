//135.Create src/api.js: export BASE_URL reading from REACT_APP_API_URL env variable or defaulting to http://localhost:8000

export const BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8000";