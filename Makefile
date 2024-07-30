# Makefile template for ICE_AXE_APP

# Default target
all:
	snowsql -c ICE_AXE -f create.sql

# Clean application from Snowflake account
clean:
	snowsql -c ICE_AXE -f clean.sql

dev:
	streamlit run streamlit/app.py -- --dev true 

.PHONY: all clean
