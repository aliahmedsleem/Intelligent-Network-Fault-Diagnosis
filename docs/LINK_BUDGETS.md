# Physics-based link budgets (analytical, not simulated traffic)

Endpoint: `POST /api/models/link-budget`. Use a discriminated `link.medium` payload.

## Fiber
`received_power_dbm = tx_power_dbm - (attenuation_db_per_km × length_km + connector_count × connector_loss_db + splice_count × splice_loss_db)`.

Defaults: 0.35 dB/km at 1310 nm, 0.22 dB/km at 1550 nm, 0.3 dB/connector, 0.1 dB/splice, and 3 dB engineering reserve. These are illustrative values, not guaranteed component specifications. Propagation speed is approximated as 200,000 km/s.

## Wi-Fi 2.4 / 5 GHz and microwave
`FSPL_dB = 32.44 + 20log10(distance_km) + 20log10(frequency_MHz)`.

`received_power_dbm = tx_power_dbm + tx_gain_dbi + rx_gain_dbi - FSPL_dB - additional_loss_db`.

`link_margin_db = received_power_dbm - receiver_sensitivity_dbm - fade_margin_db`.

Assumes free-space line-of-sight propagation. The user explicitly supplies transmitter power, antenna gains, receiver sensitivity and optional additional loss. There is **no** packet-level RF simulation, BER/PER, interference, fading, obstacle model, or hardware calibration here. In particular, Wi-Fi MAC contention and rate adaptation cannot be inferred from these equations.

The endpoint deliberately does not convert margin into invented packet-loss or throughput numbers. These budgets can inform later ns-3 experiments, which must be independently validated.
