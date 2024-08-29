import aiohttp
import asyncio
import requests
import datetime
from openpyxl import Workbook
import csv
from tqdm import tqdm
from time import sleep
from credentials import API_KEY  # Ensure your credentials.py file has the API_KEY defined

BASE_URL = 'http://ws.audioscrobbler.com/2.0/'

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def get_period_short_name(period):
    period_map = {
        "weekly": "Week",
        "monthly": "Month",
        "yearly": "Year"
    }
    return period_map.get(period, period.capitalize())

async def fetch_with_retry(session, username, start, end, retry=0):
    url = f"{BASE_URL}?method=user.getWeeklyTrackChart&user={username}&from={start}&to={end}&api_key={API_KEY}&format=json"
    try:
        async with session.get(url) as response:
            result = await response.json()
            tracks = result.get('weeklytrackchart', {}).get('track', [])
            if tracks or retry >= MAX_RETRIES:
                return tracks
            else:
                await asyncio.sleep(RETRY_DELAY)
                return await fetch_with_retry(session, username, start, end, retry + 1)
    except Exception as e:
        if retry < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)
            return await fetch_with_retry(session, username, start, end, retry + 1)
        else:
            print(f"Failed to fetch data for period {start} to {end}: {e}")
            return []

async def generate_excel(username, num_tracks, start_date, end_date, week_start_day, period, file_format):
    period_short_name = get_period_short_name(period)
    first_scrobble = get_user_info(username)
    first_scrobble_timestamp = int(first_scrobble.timestamp())
    
    start_time = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_time = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp())

    if file_format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = f"{period.capitalize()} Top Tracks"
        if period == "weekly":
            ws.append(['No', f'{period_short_name} Num', 'Start', 'End', 'Track Name', 'Artist', 'Play Count'])
        else:
            ws.append(['No', f'{period_short_name} Num', 'Period', 'Track Name', 'Artist', 'Play Count'])

    elif file_format == "csv":
        file_path = f'{username}_{period}_{start_date}_to_{end_date}_top_tracks_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if period == "weekly":
                writer.writerow(['No', f'{period_short_name} Num', 'Start', 'End', 'Track Name', 'Artist', 'Play Count'])
            else:
                writer.writerow(['No', f'{period_short_name} Num', 'Period', 'Track Name', 'Artist', 'Play Count'])

    elif file_format == "reddit":
        file_path = f'{username}_{period}_{start_date}_to_{end_date}_top_tracks_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        with open(file_path, mode='w', encoding='utf-8') as file:
            if period == "weekly":
                file.write(f"No|{period_short_name} Num|Start|End|Track Name|Artist|Play Count\n")
                file.write(f":--:|:--:|:--:|:--:|:--|:--|--:\n")
            else:
                file.write(f"No|{period_short_name} Num|Period|Track Name|Artist|Play Count\n")
                file.write(f":--:|:--:|:--:|:--|--|--:\n")

    async with aiohttp.ClientSession() as session:
        with tqdm(total=(end_time - start_time) // get_period_seconds(period), desc=f"Processing {period_short_name.capitalize()}s") as pbar:
            row_number = 1
            while start_time <= end_time:
                if period == "weekly":
                    period_end_time = start_time + 7 * 86400 - 1
                    period_start = datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')
                    period_end = datetime.datetime.fromtimestamp(period_end_time).strftime('%Y-%m-%d')
                    current_number = (start_time - first_scrobble_timestamp) // (7 * 86400) + 1
                elif period == "monthly":
                    period_start_date = datetime.datetime.fromtimestamp(start_time).replace(day=1)
                    period_end_date = (period_start_date + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
                    period_start = period_start_date.strftime('%b %Y')
                    period_end_time = int(period_end_date.timestamp())
                    current_number = ((period_start_date.year - first_scrobble.year) * 12 + period_start_date.month - first_scrobble.month) + 1
                elif period == "yearly":
                    period_start_date = datetime.datetime.fromtimestamp(start_time).replace(month=1, day=1)
                    period_start = period_start_date.strftime('%Y')
                    period_end_time = int(datetime.datetime.fromtimestamp(start_time).replace(month=12, day=31).timestamp())
                    current_number = period_start_date.year - first_scrobble.year + 1

                tracks = await fetch_with_retry(session, username, start_time, period_end_time)

                if tracks:
                    for i in range(min(num_tracks, len(tracks))):
                        top_track = tracks[i]
                        if period == "weekly":
                            row_data = [
                                row_number,
                                current_number,
                                period_start,
                                period_end,
                                top_track['name'],
                                top_track['artist']['#text'],
                                top_track['playcount']
                            ]
                        else:
                            row_data = [
                                row_number,
                                current_number,
                                period_start,
                                top_track['name'],
                                top_track['artist']['#text'],
                                top_track['playcount']
                            ]

                        if file_format == "xlsx":
                            ws.append(row_data)
                        elif file_format == "csv":
                            with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                                writer = csv.writer(file)
                                writer.writerow(row_data)
                        elif file_format == "reddit":
                            with open(file_path, mode='a', encoding='utf-8') as file:
                                file.write("|".join(map(str, row_data)) + "\n")
                        
                        row_number += 1

                else:
                    if period == "weekly":
                        row_data = [
                            row_number,
                            current_number,
                            period_start,
                            period_end,
                            "No Data",
                            "No Data",
                            "No Data"
                        ]
                    else:
                        row_data = [
                            row_number,
                            current_number,
                            period_start,
                            "No Data",
                            "No Data",
                            "No Data"
                        ]

                    if file_format == "xlsx":
                        ws.append(row_data)
                    elif file_format == "csv":
                        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
                            writer = csv.writer(file)
                            writer.writerow(row_data)
                    elif file_format == "reddit":
                        with open(file_path, mode='a', encoding='utf-8') as file:
                            file.write("|".join(map(str, row_data)) + "\n")
                    
                    row_number += 1

                if period == "weekly":
                    start_time = period_end_time + 1
                elif period == "monthly":
                    start_time = int((period_start_date + datetime.timedelta(days=32)).replace(day=1).timestamp())
                elif period == "yearly":
                    start_time = int((datetime.datetime.fromtimestamp(start_time).replace(year=datetime.datetime.fromtimestamp(start_time).year + 1, month=1, day=1)).timestamp())

                pbar.update(1)

    if file_format == "xlsx":
        file_path = f'{username}_{period}_{start_date}_to_{end_date}_top_tracks_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb.save(file_path)
        print(f"Excel file '{file_path}' generated successfully.")
    elif file_format in ["csv", "reddit"]:
        print(f"File '{file_path}' generated successfully.")

def get_user_info(username):
    url = f"{BASE_URL}?method=user.getinfo&user={username}&api_key={API_KEY}&format=json"
    response = requests.get(url).json()
    registered = response['user']['registered']['unixtime']
    return datetime.datetime.fromtimestamp(int(registered))

def adjust_to_week_start(timestamp, week_start_day):
    current_weekday = datetime.datetime.fromtimestamp(timestamp).weekday()
    target_weekday = (week_start_day + 1) % 7
    adjustment_days = (target_weekday - current_weekday) % 7
    adjusted_timestamp = timestamp - adjustment_days * 86400
    return adjusted_timestamp

def get_period_seconds(period):
    if period == "weekly":
        return 7 * 86400
    elif period == "monthly":
        return 30 * 86400  # Approximation, we'll handle month-end more accurately in the logic
    elif period == "yearly":
        return 365 * 86400  # Approximation, we'll handle year-end more accurately in the logic

def select_date_range(period, username):
    first_scrobble = get_user_info(username)
    today = datetime.datetime.now()
    print(f"Select the date range for {period.capitalize()}:")
    print("1. From today")
    print("2. All time")
    print("3. Custom time")
    
    choice = input("Enter your choice: ")

    if choice == "1":
        if period == "weekly":
            weeks = int(input("Enter the number of weeks: "))
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - datetime.timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        elif period == "monthly":
            months = int(input("Enter the number of months: "))
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - datetime.timedelta(days=months*30)).strftime('%Y-%m-%d')
        elif period == "yearly":
            years = int(input("Enter the number of years: "))
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - datetime.timedelta(days=years*365)).strftime('%Y-%m-%d')

    elif choice == "2":
        start_date = first_scrobble.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

    elif choice == "3":
        if period == "weekly":
            start_date = input("Enter the start date (DD-MM-YYYY): ")
            end_date = input("Enter the end date (DD-MM-YYYY): ")
            start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y").strftime('%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y").strftime('%Y-%m-%d')
        elif period == "monthly":
            start_date = input("Enter the start month/year (MM-YYYY): ")
            end_date = input("Enter the end month/year (MM-YYYY): ")
            start_date = datetime.datetime.strptime(start_date, "%m-%Y").strftime('%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, "%m-%Y").strftime('%Y-%m-%d')
        elif period == "yearly":
            start_year = input("Enter the start year (YYYY): ")
            end_year = input("Enter the end year (YYYY): ")
            start_date = f"{start_year}-01-01"
            end_date = f"{end_year}-12-31"

    if datetime.datetime.strptime(start_date, "%Y-%m-%d") < first_scrobble:
        start_date = first_scrobble.strftime('%Y-%m-%d')
    if datetime.datetime.strptime(end_date, "%Y-%m-%d") > today:
        end_date = today.strftime('%Y-%m-%d')

    return start_date, end_date

def main():
    username = input("Enter Last.fm username: ")
    while True:
        print("Select the period:")
        print("1. Weekly")
        print("2. Monthly")
        print("3. Yearly")
        period_choice = input("Enter your choice (1-3): ").strip()

        period_map = {"1": "weekly", "2": "monthly", "3": "yearly"}
        period = period_map.get(period_choice)
        if not period:
            print("Invalid choice, please try again.")
            continue
        
        break
    
    num_tracks = int(input("Enter number of top tracks per period (1-10): "))
    start_date, end_date = select_date_range(period, username)
    week_start_day = None
           
    while True:
        print("Select the file format:")
        print("1. XLSX")
        print("2. CSV")
        print("3. Reddit Table")
        file_choice = input("Enter your choice (1-3): ").strip()

        file_format_map = {"1": "xlsx", "2": "csv", "3": "reddit"}
        file_format = file_format_map.get(file_choice)
        if not file_format:
            print("Invalid choice, please try again.")
            continue
        
        break
    
    asyncio.run(generate_excel(username, num_tracks, start_date, end_date, week_start_day, period, file_format))

if __name__ == "__main__":
    main()
