CREATE database iceaxe;
USE DATABASE iceaxe;

-- creating dev stage for udf python filewas
CREATE SCHEMA STAGE_CONTENT;
CREATE OR REPLACE STAGE STAGE_CONTENT.ICE_AXE_stage
  FILE_FORMAT = (TYPE = 'csv' FIELD_DELIMITER = '|' SKIP_HEADER = 1);

--- Uploading files to the stage, this can only be run from SnowSQL
PUT file://manifest.yml @STAGE_CONTENT.ICE_AXE_STAGE overwrite=true auto_compress=false;
PUT file://scripts/setup.sql @STAGE_CONTENT.ICE_AXE_STAGE/scripts overwrite=true auto_compress=false;

PUT file://streamlit/*.py @STAGE_CONTENT.ICE_AXE_STAGE/streamlit overwrite=true auto_compress=false;
PUT file://streamlit/analytics/*.py @STAGE_CONTENT.ICE_AXE_STAGE/streamlit/analytics overwrite=true auto_compress=false;
PUT file://streamlit/metrics/*.py @STAGE_CONTENT.ICE_AXE_STAGE/streamlit/metrics overwrite=true auto_compress=false;

PUT file://streamlit/environment.yml @STAGE_CONTENT.ICE_AXE_STAGE/streamlit overwrite=true auto_compress=false;
PUT file://readme.md @STAGE_CONTENT.ICE_AXE_STAGE overwrite=true auto_compress=false;
