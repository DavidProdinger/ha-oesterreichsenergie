# Österreichsenergie Smart-Meter-Adapter for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
![Version](https://img.shields.io/github/v/release/DavidProdinger/ha-oesterreichsenergie?style=for-the-badge)

This Home Assistant integration allows you to receive data from a Smart Meter Adapter (SMA) as specified by [Österreichs E-Wirtschaft](https://oesterreichsenergie.at/fileadmin/user_upload/Smart_Meter-Plattform/20200201_Konzept_Kundenschnittstelle_SM.pdf).

The integration supports two ways of communication:
- **JSON API**: Polling the adapter directly via HTTP/HTTPS.
- **MQTT**: Receiving real-time updates pushed by the adapter to an MQTT broker.

## Features

- **JSON API Support**: 
  - Periodic polling of measurement and status data.
  - Automatic device creation for the adapter and the connected meter.
- **MQTT Support**:
  - Real-time updates.
  - **Dynamic Meter Discovery**: Automatically creates a new Home Assistant device for every unique smart meter encountered on the subscribed MQTT topic.
  - Availability tracking: Sensors are marked as `unavailable` if no data is received for 5 minutes.
- **Comprehensive Sensors**: Supports a wide range of OBIS codes including active/reactive energy (import/export), instantaneous power, voltage, and current for all three phases.

## Installation

### Via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on the three dots in the upper right corner and select **Custom repositories**.
3. Enter `https://github.com/DavidProdinger/ha-oesterreichsenergie` in the URL field.
4. Select **Integration** as the category.
5. Click **Add**.
6. Find the **Österreichsenergie Smart Meter Adapter** integration and click **Download**.
7. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/oesterreichsenergie_sma` directory to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Österreichsenergie Smart Meter Adapter**.
3. Choose your preferred connection method:

### JSON API
- **Host**: The IP address or hostname of your Smart Meter Adapter (e.g., `192.168.1.100`).
- **Token**: The API token configured on your adapter.
- **Verify SSL**: Whether to verify the SSL certificate (usually `False` for self-signed certificates).

### MQTT
- **Topic**: The MQTT topic the adapter is publishing to (default: `sma`). The integration will subscribe to this topic and automatically discover all meters sending data there.
- **QoS**: MQTT Quality of Service level (default: `0`).

## Supported OBIS Codes

The following measurements are currently supported (depending on your meter and adapter configuration):

| OBIS Code  | Description                     |
|------------|---------------------------------|
| 0-0:96.1.0 | Meter number                    |
| 1-0:1.8.0  | Active Energy Import (A+)       |
| 1-0:2.8.0  | Active Energy Export (A-)       |
| 1-0:3.8.0  | Reactive Energy Import (R+)     |
| 1-0:4.8.0  | Reactive Energy Export (R-)     |
| 1-0:1.7.0  | Instantaneous Power Import (+P) |
| 1-0:2.7.0  | Instantaneous Power Export (-P) |
| 1-0:32.7.0 | Voltage L1                      |
| 1-0:52.7.0 | Voltage L2                      |
| 1-0:72.7.0 | Voltage L3                      |
| 1-0:31.7.0 | Current L1                      |
| 1-0:51.7.0 | Current L2                      |
| 1-0:71.7.0 | Current L3                      |

## Contributing

If you want to contribute to this project, please read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
