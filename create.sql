-- Granting privileges to create an application package
GRANT CREATE APPLICATION PACKAGE ON ACCOUNT TO ROLE accountadmin;

-- Creating a new application package
CREATE APPLICATION PACKAGE ICE_AXE_PACKAGE;

-- Displaying current application packages
SHOW APPLICATION PACKAGES;

-- Setting up for application staging
USE APPLICATION PACKAGE ICE_AXE_PACKAGE;
CREATE SCHEMA STAGE_CONTENT;

-- Creating a stage for the application package
CREATE OR REPLACE STAGE ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_stage
  FILE_FORMAT = (TYPE = 'csv' FIELD_DELIMITER = '|' SKIP_HEADER = 1);

--- Uploading files to the stage, this can only be run from SnowSQL
PUT file://manifest.yml @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE overwrite=true auto_compress=false;
PUT file://scripts/setup.sql @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE/scripts overwrite=true auto_compress=false;

PUT file://streamlit/*.py @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE/streamlit overwrite=true auto_compress=false;
PUT file://streamlit/analytics/*.py @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE/streamlit/analytics overwrite=true auto_compress=false;
PUT file://streamlit/metrics/*.py @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE/streamlit/metrics overwrite=true auto_compress=false;

-- PUT file://streamlit/app.py @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE/streamlit overwrite=true auto_compress=false;
PUT file://streamlit/environment.yml @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE/streamlit overwrite=true auto_compress=false;
PUT file://readme.md @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE overwrite=true auto_compress=false;


-- Listing files in the created stage
LIST @ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE;

-- Installing the application
CREATE APPLICATION ICE_AXE_APP
  FROM APPLICATION PACKAGE ICE_AXE_PACKAGE
  USING '@ICE_AXE_PACKAGE.STAGE_CONTENT.ICE_AXE_STAGE';

-- Verifying the installed applications
SHOW APPLICATIONS;