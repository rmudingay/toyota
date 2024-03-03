# Toyota Order Status Tracker

## Overview
This Python script provides a convenient way to access the Toyota API to keep up with the status of your car order. It's designed those like me who wish to get updates about the status of their car, including estimated delivery dates, current status, and more detailed information about the car and order processing steps.

## Prerequisites
To use this script, you must:
- Have an active order with Toyota.
- Have an account with Toyota, as your username and password will be required to access the API.

## Environment Setup
Before running the script, you need to set up a Python environment. The script is compatible with Python 3.7+ and requires the `requests` module to interact with the Toyota API.

### Using Conda
If you're using Conda, you can create an environment with all necessary dependencies as follows:

1. Create a `conda` environment using the `environment.yml` file (provided separately):
    ```bash
    conda env create -f environment.yml
    ```

2. Activate the environment:
    ```bash
    conda activate toyota_api_env
    ```

### Using Pip
Alternatively, if you prefer using `pip`, ensure you have Python 3.9 installed and then install the dependencies as follows:
1. Install the required module using the `requirements.txt` file (provided separately) or simply install the `requests` module:
    ```bash
    pip install -r requirements.txt
    # Or simply
    pip install requests
    ```

## Running the Script
To execute the script, use the following command, substituting `$username` and `$password` with your actual Toyota account username and password:
```bash
python toyota.py --username $username --password $password
```

## Expected output
The script will output the current status of your order, similar to the example below:
```yaml
   Order 0000XXXXXXXXXXX1

  Status: ArrivedInCountry
  Estimated Delivery?: 2024-03-04

  Call Off?: Called off
  Delayed?: False
  Damage?: None

  Vehicle: Corolla Cross
  Engine: 2.0 Hybrid Synergy Drive
  Transmission: Hybridtransmission
  Color Code: 089

  VIN: ZXXXXXXXXXXX1

  │ Step              │ Location                              │ Status  │
  ├───────────────────┼───────────────────────────────────────┼─────────┤
  │ processedOrder    │                                       │ visited │
  │ buildInProgress   │ Toyota City (Aichi Prefecture), JAPAN │ visited │
  │ leftTheFactory    │ Toyota City (Aichi Prefecture), JAPAN │ visited │
  │ inTransit         │ Zeebrugge, BELGIUM                    │ current │
  │ arrivedAtRetailer │ LUND, SWEDEN                          │ pending │

  │ Loc. Code      │ Location                              │ Loc. Type   │ Transport │ Visited    │
  ├────────────────┼───────────────────────────────────────┼─────────────┼───────────┼────────────┤
  │ SU.TJ.1, JP    │ Toyota City (Aichi Prefecture), JAPAN │ FACTORY     │ Vessel    │ visited    │
  │ HB.ZB.1, BE    │ Zeebrugge, BELGIUM                    │ HUB         │ Vessel    │ visited    │
  │ HB.MA.1, SE    │ Malmo, SWEDEN                         │ HUB         │ Truck     │ inTransit  │
  │ DL.04413.1, SE │ LUND, SWEDEN                          │ DESTINATION │ Truck     │ notVisited │
```
