import re

# UDF LEADS
def show_tables(query_text):    
    return re.search(r'SHOW\s+TABLES', query_text, re.I) is not None


def create_temp_storage(query_text):
    return re.search(r'^CREATE\s+TEMP.*STORAGE', query_text, re.I) is not None


def accountadmin_changes(query_text):
    return re.search(r'GRANT.*ACCOUNTADMIN.*\s+TO\s+', query_text, re.I) is not None


def copy_ext_location(query_text):
    return re.search(r"COPY\s+INTO.*'(s3|s3gov|s3china|gcs|azure)://", query_text, re.I) is not None


def get_file(query_text):
    return re.search(r"GET\s+.*file://", query_text, re.I) is not None


def copy_into_select_all(query_text):
    return re.search(r"COPY\s+INTO.*SELECT\s+*", query_text, re.I) is not None


def create_ext_volume(query_text):
    return re.search(r"CREATE.*EXTERNAL.*VOLUME.*(s3|gcs|azure)://", query_text, re.I) is not None


MODIFICATION_KEYWORDS = [
        'create role', 'manage grants', 'create integration', 'alter integration'
        , 'create share', 'create account', 'monitor usage', 'ownership', 'drop table'
        , 'drop database', 'create stage', 'drop stage', 'alter stage', 'create user'
        , 'alter user', 'drop user', 'create network policy', 'alter network policy'
        , 'drop network policy', 'copy'
]
MOD_KEYWORDS_RE = re.compile('(' + '|'.join(MODIFICATION_KEYWORDS) + ')')


def impactful_modifications(query_text):
    return MOD_KEYWORDS_RE.search(query_text) is not None


UDF_THREAT_LEADS = [
    {
        "type": "udf",
        "name": "copy_into_select_all",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "COPY INTO and select * in a single query.",
        "detect_fn": copy_into_select_all
    },
    {
        "type": "udf",
        "name": "show_tables",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Performing a show tables query",
        "detect_fn": show_tables
    },
    {
        "type": "udf",
        "name": "create_temp_storage",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Creation of temporary storage",
        "detect_fn": create_temp_storage
    },
    {
        "type": "udf",
        "name": "accountadmin_changes",
        "mitre_technique_id": "T1098",
        "mitre_technique_description": "Account Manipulation",
        "description": "Role grants",
        "detect_fn": accountadmin_changes
    },
    {
        "type": "udf",
        "name": "impactful_modifications",
        "mitre_technique_id": "T1484",
        "mitre_technique_description": "Domain or Tenant Policy Modification",
        "description": "Impactful modifications",
        "detect_fn": impactful_modifications
    },
    {
        "type": "udf",
        "name": "copy_external_location",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "A Query containing COPY INTO and cloud storage location",
        "detect_fn": copy_ext_location
    },
    {
        "type": "udf",
        "name": "copy_external_volume",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "A Query containing COPY INTO and cloud storage location",
        "detect_fn": create_ext_volume
    },
    {
        "type": "udf",
        "name": "get_file",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "Get file contents",
        "detect_fn": get_file
    }
]


class LeadsDetector:
    def process(self, query_id, query_type, query_text):
        no_hits = True
        for tl in UDF_THREAT_LEADS:
            hit = tl['detect_fn'](query_text)
            if hit:
                no_hits = False
                yield (query_id, tl['name'])

        if no_hits:
            yield None