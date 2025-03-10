
from flask import *
from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_ID = '1vZMubx6bREW-c8X7OWnyBUo7FaJUAfkFM7gi4w7pHtk'  # Your spreadsheet ID
RANGE_NAME = 'Sheet1!A1:Z1000'  # Adjust based on your needs

def get_google_sheets_service():
    """Get authenticated Google Sheets service"""
    credentials_path = 'test-gl-sheet-c4a182ac8072.json'  # Path to your credentials JSON file
    
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=credentials)
    return service



@app.route('/api/sheet-data', methods=['GET'])
def get_sheet_data():
    """Endpoint to get all data from the Google Sheet"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # Call the Sheets API with valueRenderOption set to FORMATTED_VALUE
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueRenderOption='FORMATTED_VALUE'
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return jsonify({'error': 'No data found in spreadsheet'}), 404
        
        # Assuming first row contains headers
        headers = values[0]
        data = []
        
        # Convert to list of dictionaries
        for row in values[1:]:
            # Create a dictionary for each row, filling in missing values with null
            row_data = {}
            for i in range(len(headers)):
                # If this column exists in the current row, use it, otherwise use null
                if i < len(row):
                    row_data[headers[i]] = row[i]
                else:
                    row_data[headers[i]] = None
            
            data.append(row_data)
        
        return jsonify({'data': data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/columns', methods=['GET'])
def get_columns():
    """Endpoint to get just the column names from the Google Sheet"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # Call the Sheets API to get just the header row
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                   range='Sheet1!A1:Z1').execute()
        values = result.get('values', [])
        
        if not values:
            return jsonify({'error': 'No headers found in spreadsheet'}), 404
        
        # Return just the headers/columns
        columns = values[0]
        
        return jsonify({'columns': columns})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
#
#@app.route('/api/column/<column_name>', methods=['GET'])
#def get_column_data(column_name):
#    """Endpoint to get data from a specific column"""
#    try:
#        service = get_google_sheets_service()
#        sheet = service.spreadsheets()
#        
#        # First get headers to find column index
#        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
#                                   range='Sheet1!A1:Z1').execute()
#        headers = result.get('values', [[]])[0]
#        
#        if column_name not in headers:
#            return jsonify({'error': f'Column {column_name} not found'}), 404
#        
#        # Find index of the column
#        col_index = headers.index(column_name)
#        col_letter = chr(65 + col_index)  # Convert to A, B, C, etc.
#        
#        # Get all data from that column
#        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
#                                   range=f'Sheet1!{col_letter}1:{col_letter}1000').execute()
#        values = result.get('values', [])
#        
#        # Skip the header and extract the values
#        column_data = []
#        if len(values) > 1:
#            column_data = [item[0] if item and len(item) > 0 else None for item in values[1:]]
#        
#        return jsonify({column_name: column_data})
#    
#    except Exception as e:
#        return jsonify({'error': str(e)}), 500

@app.route('/api/raw-data', methods=['GET'])
def get_raw_data():
    """Endpoint to get all data exactly as it appears in the sheet"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # Call the Sheets API with valueRenderOption set to FORMATTED_VALUE
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueRenderOption='FORMATTED_VALUE'
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return jsonify({'error': 'No data found in spreadsheet'}), 404
        
        return jsonify({'data': values})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/update-sheet', methods=['POST'])
def update_google_sheet():
    """Update a specific row based on the team name"""
    try:
        # Parse form data
        data = request.json
        team_name = data.get('team_name')  # Dropdown selected team
        input_value = data.get('input_value')  # Textbox input
        
        if not team_name or not input_value:
            return jsonify({'error': 'Missing team_name or input_value'}), 400

        service = get_google_sheets_service()
        sheet = service.spreadsheets()

        # Fetch all rows to find the row number of the team
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range='Sheet1!A:A').execute()
        values = result.get('values', [])

        if not values:
            return jsonify({'error': 'No data found in spreadsheet'}), 404

        # Find the row number where the team name exists
        row_number = None
        for i, row in enumerate(values, start=1):
            if row and row[0] == team_name:
                row_number = i
                break

        if row_number is None:
            return jsonify({'error': 'Team not found in the sheet'}), 404

        # Update the respective row in column B (second column)
        update_range = f'Sheet1!B{row_number}'
        body = {'values': [[input_value]]}

        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=update_range,
                              valueInputOption='RAW', body=body).execute()

        return jsonify({'message': 'Sheet updated successfully', 'row': row_number})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)