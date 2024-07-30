# Instructions
## Install & Configure SnowSQL
* Download & install [SnowSQL](https://developers.snowflake.com/snowsql/)
* Configure SnowSQL profile "ICE_AXE" in ~/.snowsql/config
```conf
[connections.ICE_AXE]
accountname = <snowflake account name>
username = <username>
password = <password>
```

## Publish the application to Snowflake
* `make` to push the app and install it on the account
* `make clean` to remove the app from the account

## Enabling local development mode
`streamlit run streamlit/app.py -- --dev true` or `make dev`