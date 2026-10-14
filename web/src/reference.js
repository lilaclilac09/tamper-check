// Reference DB. ALL VALUES ARE EXAMPLE PLACEHOLDERS for the demo, NOT official Ledger specs.
// Calibrate by weighing a known-genuine unit bought directly from ledger.com. Mirrors tamper_check/reference.py.
export const REFERENCE = {
  "ledger-nano-s-plus": { name: "Ledger Nano S Plus (EXAMPLE values)", weight_g: 21.0, dims_mm: [62.4, 17.4, 8.2], com_mm: [0, 0], weight_tol_g: 0.05, com_tol_mm: 0.7, battery: false },
  "ledger-nano-x": { name: "Ledger Nano X (EXAMPLE values)", weight_g: 34.0, dims_mm: [72.0, 18.6, 11.8], com_mm: [0, 0], weight_tol_g: 0.05, com_tol_mm: 0.7, battery: true },
  "ledger-stax": { name: "Ledger Stax (EXAMPLE values)", weight_g: 45.0, dims_mm: [85.0, 54.0, 6.0], com_mm: [0, 0], weight_tol_g: 0.05, com_tol_mm: 0.7, battery: true },
  "ledger-flex": { name: "Ledger Flex (EXAMPLE values)", weight_g: 57.0, dims_mm: [78.6, 52.0, 8.0], com_mm: [0, 0], weight_tol_g: 0.05, com_tol_mm: 0.7, battery: true },
};
// Powered OFF in a Faraday bag a Ledger is silent; it has no cellular modem. Any LTE/GSM energy is anomalous.
export const CELL_BANDS_MHZ = [[700, 960], [1710, 2200], [2300, 2700]];
