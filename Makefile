# Makefile template for ICE_AXE_APP

# Default target
all:
	snowsql -c ICE_AXE -f create.sql

# Clean application from Snowflake account
clean:
	snowsql -c ICE_AXE -f clean.sql

dev:
	streamlit run streamlit/app.py -- --dev true 

devprep:
	snowsql -c ICE_AXE -f stage.dev.sql
	snowsql -c ICE_AXE -f create.dev.sql

devclean:
	snowsql -c ICE_AXE -f clean.dev.sql

.PHONY: all clean
