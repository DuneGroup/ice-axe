from snowflake.snowpark.session import Session
from snowflake.snowpark.context import get_active_session

def create_local_session():
    import configparser
    import pathlib
    
    config = configparser.ConfigParser()    
    config.read(pathlib.Path('~/.snowsql/config').expanduser())

    connection_parameters = {
        "account": config['connections.ICE_AXE']['accountname'],
        "user": config['connections.ICE_AXE']['username'],
        "password": config['connections.ICE_AXE']['password'],
    } 

    Session.builder.configs(connection_parameters).create()  


def request_permissions():
    import snowflake.permissions as permissions
    
    session = get_active_session()
    # Check if required privileges are missing
    missing_privileges = permissions.get_missing_account_privileges(["IMPORTED PRIVILEGES ON SNOWFLAKE DB"])
    if missing_privileges:
        # Request permissions from the user
        permissions.request_account_privileges(missing_privileges)