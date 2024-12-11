import traceback
from flask import Flask, make_response, send_file
from flask import Blueprint, request, jsonify
from flask_cors import CORS
import numpy as np
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import requests
import unicodedata
import io
from psycopg2 import sql
from sqlalchemy import create_engine

load_dotenv()
app = Flask(__name__)
CORS(app)


db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

database_url = f"postgresql://{db_user}:{db_password}@db/{db_name}"
print(f"Database URL: {database_url}")
upload_bp = Blueprint('uplosad_bp', __name__)

def normalize_unicode_nfc(text):
    if isinstance(text, str):
        return unicodedata.normalize('NFC', text)
    return text

def to_python_type(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value
def flatten_to_strings(listOfLists):
    result = []
    for i in listOfLists:
#appending only if i is a string
        if isinstance(i, str):
            result.append(i)
        #otherwise call this function recursively
        else:
            result.extend(flatten_to_strings(i))
    return result

def override_table_psycopg2(df, table_name, db_connection_url):
    try:
        if df.empty:
            raise ValueError("DataFrame is empty. No data to insert.")
        #unicode nfc 
        string_columns = df.select_dtypes(include=['object']).columns
        df[string_columns] = df[string_columns].apply(lambda col: col.apply(normalize_unicode_nfc))
        df = df.replace({pd.NaT: None, np.nan: None})
        with psycopg2.connect(db_connection_url) as conn:
            cursor = conn.cursor()
          
            truncate_query = f"TRUNCATE TABLE {table_name} RESTART IDENTITY;"
            cursor.execute(truncate_query)
            print(f"Table {table_name} truncated successfully.")

            
            insert_query = f"""
            INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in df.columns])})
             OVERRIDING SYSTEM VALUE
            VALUES ({', '.join(['%s'] * len(df.columns))});
            """
            print(f"Insert query: {insert_query}")

            print(f"DataFrame shape: {df.shape}")  
            print(f"DataFrame columns: {df.columns.tolist()}")  

            for row in df.itertuples(index=False):
                print(f"Inserting row: {row}") 
                
                if len(row) != len(df.columns):
                    print(f"Warning: Row length {len(row)} does not match expected length {len(df.columns)}")
                
                cursor.execute(insert_query, row)  
            
            conn.commit()
            print(f"Data inserted into {table_name} successfully.")
    
    except psycopg2.errors.UndefinedTable as e:
        raise 
    except psycopg2.errors.UndefinedColumn as e:
        raise
    except Exception as e:
        print(f"Error during override of table {table_name}: {str(e)}")
        raise Exception(f"There was an error during the override operation: {str(e)}")



def merge_table_psycopg2(df, table_name, db_connection_url):
    try: 
    #unicode nfc
        string_columns = df.select_dtypes(include=['object']).columns
        df[string_columns] = df[string_columns].apply(lambda col: col.apply(normalize_unicode_nfc))
        #for any missing values, put null in the postgresql but as None in python 
        df = df.replace({pd.NaT: None, np.nan: None})
        columns = df.columns.tolist()
        val_placeholder = ', '.join(['%s'] * len(columns))
        with psycopg2.connect(db_connection_url) as conn:
            cursor = conn.cursor()
            query = f"""WITH tab as (SELECT %s::regclass t) SELECT array_agg(attname)
            FROM pg_attribute, tab WHERE attrelid = t
            AND attnum IN (SELECT unnest(conkey) FROM pg_catalog.pg_constraint,
            tab WHERE conrelid = t AND contype = 'p');"""
            cursor.execute(query, (table_name,))
            pk_columns = cursor.fetchone()[0]
            pk_columns = flatten_to_strings(pk_columns)
            conflict_condition = ', '.join(pk_columns)

            update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in pk_columns])

            insert_query = f""" 
            INSERT INTO {table_name} ({', '.join(df.columns)})
            OVERRIDING SYSTEM VALUE
            VALUES ({val_placeholder})
            ON CONFLICT ({conflict_condition})
            DO UPDATE SET
            {update_set};
            """
            for row in df.itertuples(index=False, name=None):
                cursor.execute(insert_query, row)
            conn.commit()
    except psycopg2.errors.UndefinedTable as e:
        raise
    except Exception as e:
        raise Exception(f"There is an error that appeared while merging the table: {str(e)}")

def create_table_psycopg2(df, table_name, db_connection_url):
    try:
        print(f"Attempting to create table: {table_name}")
        #unicode nfc
        string_columns = df.select_dtypes(include=['object']).columns
        df[string_columns] = df[string_columns].apply(lambda col: col.apply(normalize_unicode_nfc))
        df = df.replace({pd.NaT: None, np.nan: None})
        with psycopg2.connect(db_connection_url) as conn:
            conn.set_client_encoding('UTF8')  
            cursor = conn.cursor()
            create_table_query = f"CREATE TABLE {table_name} ("
            for col in df.columns:
                if pd.api.types.is_integer_dtype(df[col]):
                    create_table_query += f'"{col}" INTEGER, '
                elif pd.api.types.is_float_dtype(df[col]):
                    create_table_query += f'"{col}" FLOAT, '
                else:
                    create_table_query += f'"{col}" TEXT, '
            create_table_query = create_table_query.rstrip(", ") + ")"
            
            print(f"Create table query: {create_table_query}")
            cursor.execute(create_table_query)  # Create the table
            conn.commit()
    
            insert_query = f""" 
            INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in df.columns])})
            VALUES ({', '.join(['%s'] * len(df.columns))})
            ON CONFLICT DO NOTHING;"""  

            print(f"Insert query: {insert_query}")

            for row in df.itertuples(index=False, name=None):  
                cursor.execute(insert_query, row)

            conn.commit()  
            print(f"Data inserted into {table_name} successfully.")
    except psycopg2.errors.DuplicateTable as e:
        raise

    except Exception as e:
        print(f"An error occurred during table creation or insertion: {e}")
#function to convert the datetime columns to gmt as well as making them compatible with excel restrictions

def convert_to_gmt(df):
    # Check through columns
    for col in df.columns:
        # If the column is a datetime-like column (including timezone-aware)
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Skip columns with all NaT (Not a Time) values
            if df[col].isna().all():
                continue

            # Check if the datetime column is timezone-aware
            if df[col].dt.tz is not None:
                # Convert to UTC and remove the timezone (make it naive)
                df[col] = df[col].dt.tz_convert('UTC').dt.tz_localize(None)

            # Ensure the column is timezone-naive (if it was previously timezone-aware)
            elif df[col].dt.tz is None:
                # If it's already naive, do nothing, but just to be safe:
                df[col] = df[col].dt.tz_localize(None)

    return df


def get_template_table_names(database_name):
    with psycopg2.connect(database_url) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT table_names, database_id, callbackurl, conflict_type FROM template WHERE database_name = %s", (database_name,))
        result = cursor.fetchone()
        print(f"Query for database '{database_name}' returned: {result}") 
        if result:
            table_names, database_id, callbackurl, conflict_type = result
            return table_names, database_id, callbackurl, conflict_type
        else:
            print(f"No template found for database '{database_name}'.")  
            return None, None, None, None
def get_connection_and_names(database_name):
    with psycopg2.connect(database_url) as conn:
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT database_id, table_names FROM template WHERE database_name = %s", 
            (database_name,)
        )
        template_result = cursor.fetchone()

        if not template_result:
            raise Exception(f"No matching entry found in the 'template' table for database_name '{database_name}'.")

        database_id, table_names = template_result

       
        if isinstance(table_names, str):
            table_names = table_names.split(",")  
        elif not isinstance(table_names, list):
            raise Exception(f"Unexpected data type for table_names: {type(table_names)}")

        cursor.execute(
            "SELECT connection_string FROM databases WHERE id = %s",
            (database_id,)
        )
        database_result = cursor.fetchone()

        if not database_result:
            raise Exception(f"No connection string found in the 'databases' table for ID '{database_id}'.")

        connection_string = database_result[0]
        return connection_string, table_names

        
def execute_callback_url(callbackurl):
    try:
        response = requests.get(callbackurl)
        if response.status_code == 200:
            if response.text.strip():
                try: 
                    return response.json()
                except ValueError:
                    return {"message": "Callback succeeded but no JSON data", "response_text":response.text}
            else:
                return {"message": "Callback succeeded but returned no response body"}
        elif response.status_code ==204:
            return {"message": "Callback succeeded with no content (204 status)"}
        else:
            raise Exception(f"Callback failed with status code {response.status_code}")
    except Exception as e:
        raise Exception(f"Failed to execute callback: {str(e)}")

def get_connection_string(database_id):
    with psycopg2.connect(database_url) as conn:
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        cursor.execute("SELECT connection_string FROM databases WHERE id = %s",(database_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise Exception(f"Database with id {database_id} not found.")

def get_pg_column_types(table_name, db_connection_url):
    with psycopg2.connect(db_connection_url) as conn:
        cursor = conn.cursor()
        query = f""" 
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_name = %s"""
        cursor.execute(query, (table_name,))
        result = cursor.fetchall()
        column_types = {row[0]: row[1] for row in result}
        return column_types
def validate_column_types(df, table_name,db_connection_url):
    with psycopg2.connect(db_connection_url) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT array_agg(column_name), array_agg(column_name) FILTER (WHERE column_default IS NULL and column_name IS NOT NULL) FROM information_schema.columns, (SELECT relname, relnamespace::regnamespace::text s
        FROM pg_class WHERE OID = %s::regclass) WHERE relname = table_name AND s = table_schema
        """, (table_name,))
        columns_info = cursor.fetchone()

        all_columns = columns_info[0] if isinstance(columns_info[0], list) else []
        acceptable_columns = columns_info[1] if isinstance(columns_info[1], list) else []

        
        df_columns = [col.lower() for col in df.columns]
        

        missing_columns = set(acceptable_columns) - set(df_columns)

        if missing_columns:
            raise ValueError(f"Missing the required columns: {missing_columns}")
        
        for column_name in acceptable_columns:
            if column_name.lower() in df_columns:
                print(f"'{column_name}' is present and acceptable.")
        for column_name in df_columns:
            print(f"Importing column: '{column_name}'")


def check_table_conflict(table_name, connection_string):
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)", (table_name.lower(),))
            exists = cursor.fetchone()[0]
            return exists
    except Exception as e:
        return False
        
@upload_bp.route('/upload-excel', methods = ['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'You didnt choose a file '}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    database_name = request.form.get('database')
    if not database_name:
        return jsonify({'message': 'No database selected'}), 400
    print(f"Selected database: {database_name}")
    try:
        template_table_names, database_id, callbackurl, conflict_type = get_template_table_names(database_name)
        if isinstance(conflict_type, set):
            conflict_type = list(conflict_type)

        if isinstance(conflict_type, list):
            conflict_type = ','.join(conflict_type)
        print(f"Conflict type: {conflict_type}")
        if not database_id:
            return jsonify({'message':f'Template for database {database_name} not found'}), 400
        print(f"Template table names: {template_table_names}, Database ID: {database_id}, Callback URL: {callbackurl}") 

        connection_string = get_connection_string(database_id)
        print(f"Using connection string: {connection_string}") 
        all_sheets = pd.read_excel(file, sheet_name=None)

        for index, (sheet_name, df) in enumerate(all_sheets.items()):
            try:
                if index < len(template_table_names):
                    table_name = template_table_names[index]
                else: 
                    return jsonify({'message': 'More sheets than template table names. '}), 400
                print(f"Using table name: {table_name} for sheet: {sheet_name}")
                #unicode nfc
                string_columns = df.select_dtypes(include=['object']).columns
                df[string_columns] = df[string_columns].apply(lambda col: col.apply(normalize_unicode_nfc))
                print(f"DataFrame after normalization: {df.head()}")
                #converting to string and then to hex
                df_head_string = df.head().to_string(index=False)
                df_head_hex = df_head_string.encode('utf-8').hex()  
                print("Normalized DataFrame Head in hex form:", df_head_hex)
#starting to either override, merge or create, depending on the function of the template
                if 'override' in conflict_type:
                    print(f"Overriding table: {table_name}")
                    override_table_psycopg2(df, table_name, connection_string)
                    validate_column_types(df, table_name, connection_string)
                elif 'merge' in conflict_type:
                    merge_table_psycopg2(df, table_name, connection_string)
                elif 'create' in conflict_type:
                    create_table_psycopg2(df, table_name, connection_string)
            except psycopg2.errors.DuplicateTable as e:
                return jsonify({'message': f"Table '{table_name}' already exists"}), 409
            except psycopg2.errors.UndefinedTable as e:
                 return jsonify({'message': f"Error: The table '{table_name}' does not exist. Try creating one! {str(e)}"}), 404
            except Exception as e:
                return jsonify({'message': f'Error during table operation: {str(e)}'}), 400
        if callbackurl:
            callback_response = execute_callback_url(callbackurl)
            return jsonify({'message': 'Success! Callback executed', 'callback_response': callback_response}), 200
        else:
            print("Success! No callback URL provided.") 
            return jsonify({'message': 'Success! No callback URL provided.'}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': f'An error occurred during upload: {str(e)}'}), 500
    
@app.route('/get-databases', methods = ['GET'])
def get_databases():
    print(f"Accessing Database URL: {database_url}")
    try:
        with psycopg2.connect(database_url) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT database_name FROM template")
            database_names = [row[0] for row in cursor.fetchall()]
        return jsonify(database_names), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@upload_bp.route('/get-table-names', methods=['GET'])  
def get_table_names_for_database():
    database_name = request.args.get('database_name')
    if not database_name:
        return jsonify({'message': 'No database name is provided'}), 400
    
    try: 
        with psycopg2.connect(database_url) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT table_names FROM template WHERE database_name = %s", (database_name,))  
            result = cursor.fetchone()

            if result:
                table_names = result[0]  # 
                return jsonify({'table_names': table_names}), 200
            else:
                return jsonify({'message': 'No table names found for the specified database'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500
@app.route('/search-database', methods=['GET', 'OPTIONS'])
def search_database():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:3012")
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Cache-Control')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Max-Age', '3600')
        print("Preflight request handled")
        return response, 200

    query = request.args.get('query', '')
    try:
        with psycopg2.connect(database_url) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT database_name FROM template WHERE database_name ILIKE %s", (f'%{query}%',))
            search_results = cursor.fetchall()
            database_names = [row[0] for row in search_results]
        response = jsonify(database_names)
        response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:3012")
        print("Query processed: ", search_results)
        return response, 200
    except Exception as e:
        response = jsonify({'message': str(e)})
        response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:3012")
        print("Error: ", e)
        return response, 500

@app.route('/download-table', methods=['GET'])
def download_table():
    database_name = request.args.get('database_name')
    print(f"Received database_name: {database_name}") 

   
    try:
        connection_string, table_names = get_connection_and_names(database_name)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

    if not table_names:
        return jsonify({'message': 'No table names found for the database'}), 404

    table_name = table_names[0]
    print(f"Using table name: {table_name}")  

    try:
       
        engine = create_engine(connection_string)

      
        query = f"SELECT * FROM {table_name}"
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)


        df = df.fillna("") 
        #the conversion function
        print("Datetime columns before conversion:")
        print(df.select_dtypes(include=['datetime']).head())
        df = convert_to_gmt(df)
        print("Datetime columns after conversion:") 
        print(df.select_dtypes(include=['datetime']).head())

        def shorten_worksheet_name(name, max_length=31):
            if len(name) <= max_length:
                return name
            acronym = ''.join(word[0] for word in name.split())

            if len(acronym) <= max_length:
                return acronym
            return name[:max_length]
        shortened_name = shorten_worksheet_name(table_name)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=shortened_name)
        excel_buffer.seek(0)

        response = make_response(send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{table_name}.xlsx"
        ))
        response.headers.add("Access-Control-Allow-Origin", "http://127.0.0.1:3012")
        return response
    except Exception as e:
        print(f"Error generating the Excel file: {e}")  
        return jsonify({'message': str(e)}), 500

app.register_blueprint(upload_bp)





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)