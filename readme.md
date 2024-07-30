# ⛏️ Ice Axe

## Description
Ice Axe is a Snowflake Native Application designed to provide insights into Snowflake account activities that may be potential threats. It enables users to efficiently audit and monitor login history, user activities, and system usage. 

## Features
- Overview of threat leads and user activity
- Detailed threat leads
- Detailed user activity tracking

## Installation and Usage
### Manual install
#### Pre-requisites
* Download & install [SnowSQL](https://developers.snowflake.com/snowsql/)
* make
* python3.11
* ~/.snowsql/config file containing a connection named "ICE_AXE", used for deployment only


#### Prepare
Configure Snowflake connection "ICE_AXE" in ~/.snowsql/config
```conf
[connections.ICE_AXE]
accountname = ... 
username = ...
password = ...
```
Run the following commands
```bash
git clone https://github.com/DuneGroup/ICE_AXE.git iceaxe
cd iceaxe
pip install -r requirements.txt
```

#### Deploy to Snowflake account
```bash
make
```

#### Delete from Snowflake account
```bash
make clean
```

#### Use
* Log in to your Snowflake snowsight UI
* Click `Data Products` on the sidebar
* Click `Apps` under `Data Products`
* Click `Ice Axe` to launch

##### First run only
* Click the ⛨ security icon next to `Manage Access`
* Review and grant requested permissions

### Install from the marketplace
Not yet available

## Support
For feedback, support or additional information, please contact [us](contact@dunegroup.xyz).

## License
This project is licensed under the [Apache](LICENSE).

## Note
This application requires and requests specific privileges on Snowflake databases for full functionality.