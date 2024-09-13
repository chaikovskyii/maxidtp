import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import os
import json

json_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
creds_dict = json.loads(json_creds)

with open('/tmp/credentials.json', 'w') as f:
    json.dump(creds_dict, f)


# Constants
BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="
SHEET_NAME = 'Test'

app = Flask(__name__)


def connect_to_sheet():
    """
    Connect to Google Sheets using credentials and return the first sheet.
    """
    scopes = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = Credentials.from_service_account_file('/tmp/credentials.json', scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet


@app.route('/')
def main_page():
    """
    Render the main page.
    """
    return render_template('index.html')


def get_date_range(start_date, end_date):
    """
    Generate a range of dates from start_date to end_date, inclusive.
    """
    current_date = start_date
    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)


def fetch_rate(session, date):
    """
    Fetch exchange rates for a given date using requests.Session.
    """
    formatted_date = date.strftime('%d.%m.%Y')
    url = f"{BASE_URL}{formatted_date}"
    try:
        response = session.get(url)
        if response.status_code == 200:
            data = response.json()
            usd_rates = next((rate for rate in data.get('exchangeRate', []) if rate['currency'] == 'USD'), None)
            return formatted_date, usd_rates
        else:
            return formatted_date, None
    except Exception as e:
        print(f"Error fetching data for {formatted_date}: {e}")
        return formatted_date, None


def fetch_all_rates(start_date, end_date):
    """
    Fetch exchange rates for all dates in the range using requests.Session.
    """
    with requests.Session() as session:
        results = []
        for date in get_date_range(start_date, end_date):
            result = fetch_rate(session, date)
            results.append(result)
        return results



@app.route('/update_rate', methods=['POST'])
def update_rate():
    data = request.get_json()

    update_from = data.get('update_from')
    update_to = data.get('update_to')

    today = datetime.today().strftime('%d.%m.%Y')
    if not update_from or update_from in ["undefined.undefined.", None]:
        update_from = today
    if not update_to or update_to in ["undefined.undefined.", None]:
        update_to = today

    try:
        update_from_date = datetime.strptime(update_from, '%d.%m.%Y')
        update_to_date = datetime.strptime(update_to, '%d.%m.%Y')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use dd.mm.yyyy.'}), 400

    if update_from_date > update_to_date:
        return jsonify({'error': 'The "Update From" date must be before or the same as the "Update To" date.'}), 400

    results = fetch_all_rates(update_from_date, update_to_date)

    sheet = connect_to_sheet()
    rows_to_append = []

    for formatted_date, usd_rates in results:
        if usd_rates:
            sale_rate = usd_rates.get('saleRate')
            purchase_rate = usd_rates.get('purchaseRate')
            rows_to_append.append([formatted_date, sale_rate, purchase_rate])

    if rows_to_append:
        try:
            sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        except Exception as e:
            return jsonify({'error': f'Failed to update Google Sheets: {e}'}), 500

    return jsonify({'message': 'Data successfully updated. Please visit https://docs.google.com/spreadsheets/d/1H9PjXE3PBeW1-huahsqfQ6Cm4ZBn1SmpWJM3aLyHpqw/edit?gid=0#gid=0'}), 200


if __name__ == '__main__':
    app.run(debug=True)