from dotenv import load_dotenv
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType
from openrgb.utils import RGBColor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager
import math
import time
import PySimpleGUI as sg
from PyQt5.QtWidgets import QApplication, QColorDialog
from selenium.webdriver.firefox.options import Options

app = QApplication([])

Options = Options()
Options.headless = True

load_dotenv()
gecko_service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(options=Options, service=gecko_service)
cli = OpenRGBClient()
users_keyb = cli.get_devices_by_type(DeviceType.KEYBOARD)[0]
keyb_length = len(users_keyb.colors)


key_columns = {  # make a dictionary that shows what number is what key?
    0: [0, 16, 33, 50, 63, 76, 77],
    1: [17, 34, 51, 64, 78],
    2: [1, 18, 35, 52, 65],
    3: [2, 19, 36, 53, 66],
    4: [3, 20, 37, 54, 67],
    5: [4, 21, 38, 55, 68, 79],
    6: [22, 39, 56, 69],
    7: [5, 23, 40, 57, 70],
    8: [6, 24, 41, 58, 71],
    9: [7, 25, 42, 59, 72, 80],
    10: [8, 26, 43, 60, 73, 81],
    11: [9, 27, 44, 61, 82],
    12: [10, 11, 28, 45, 62, 74],
    13: [12, 29, 46, 83],
    14: [13, 30, 47, 84],
    15: [14, 31, 48, 75, 85],
    16: [15, 32, 49, 86],
}

key_rows = {
    0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    1: [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
    2: [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
    3: [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63],
    4: [64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75],
    5: [76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86],
}


def get_decimal(number):
    number = number % 1
    return number


# maybe make color a class or something idk if you plan on adding more colors per team


def mix_colors(home_percent_as_decimal, color1, color2):
    away_percent_as_decimal = 1 - home_percent_as_decimal
    color1_RGB_array = split_color_to_RGB(color1)
    color2_RGB_array = split_color_to_RGB(color2)
    mixed_color_RGB_array = []

    for i in range(0, len(color1_RGB_array)):
        color1_attribute = round(home_percent_as_decimal * color1_RGB_array[i])
        color2_attribute = round(away_percent_as_decimal * color2_RGB_array[i])
        mixed_color_attribute = round(color1_attribute + color2_attribute / 2)
        mixed_color_RGB_array.append(mixed_color_attribute)

    mixed_color = RGBColor(
        mixed_color_RGB_array[0], mixed_color_RGB_array[1], mixed_color_RGB_array[2]
    )
    return mixed_color


def split_color_to_RGB(color):
    color = [color.red, color.green, color.blue]
    return color


def find_match(match):
    driver.get("https://google.com")
    search_box = driver.find_element(by=By.CLASS_NAME, value="gLFyf")
    search_box.send_keys(match)
    search_box.send_keys(Keys.ENTER)
    match_info = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "imso_mh__ma-sc-cont"))
    )
    match_info.click()


def get_current_home_possession():
    match_page = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "lr-imso-ss-wdt"))
    )
    possession_class = match_page.find_elements(by=By.CLASS_NAME, value="MzWkAb")[2]
    possession_stats = possession_class.find_elements(by=By.TAG_NAME, value="td")
    home_possession = int(possession_stats[0].get_attribute("innerHTML")[:2])
    driver.refresh()
    return home_possession


def set_keyboard_team_color(
    keyboard_coverage=100, main_color="#FFFFFF", blend_colors=None, secondary_color=None
):
    adjusted_keyboard_coverage = (keyboard_coverage / 100) * len(key_columns)
    num_of_key_columns_to_change = math.ceil(adjusted_keyboard_coverage)
    color_spectrum = users_keyb.colors
    for key_column in range(0, num_of_key_columns_to_change):
        for key in key_columns[key_column]:
            color_to_set_key = main_color
            if secondary_color:
                for key_row in sorted(key_rows.values())[1::2]:
                    if key in key_row:
                        color_to_set_key = secondary_color

            if blend_colors:
                if key_column == num_of_key_columns_to_change - 1:
                    # minus 1 so the rounded possession matches up with the key columns
                    mixed_color_to_account_for_decimals = mix_colors(
                        get_decimal(adjusted_keyboard_coverage),
                        color_to_set_key,
                        users_keyb.colors[key],
                    )
                    color_to_set_key = mixed_color_to_account_for_decimals
            color_spectrum[key] = color_to_set_key

    users_keyb.set_colors(color_spectrum)


print("Done.")

sg.theme("DarkAmber")


def color_btn(key):
    return sg.Button(key=key, button_color="red", size=(8, 4), visible=True)


def options(team):
    return sg.Checkbox(
        "Secondary Color",
        key=(f"-TEAM{team}-", f"-{team}_TOGGLE_SECOND_COLOR-"),
        default=True,
        enable_events=True,
    )


def color_row(header, team):
    return [
        [sg.Text(header), options(team)],
        [
            color_btn((f"-TEAM{team}-", "-MAIN_COLOR_BUTTON-")),
            color_btn((f"-TEAM{team}-", "-SECONDARY_COLOR_BUTTON-")),
        ],
    ]


def set_keyboard_for_match(refresh_time):  # rename function to something better
    while True:
        cycle = 0

        if event == "Stop":
            print("STOPPED")
            break

        for team in reversed(
            list(teams_settings.keys())
        ):  # STATE WHY YOU REVERSED THIS HERE
            keyboard_coverage = get_current_home_possession()
            secondary_color = None
            blend_colors = True

            if cycle == 0:
                keyboard_coverage = 100
                blend_colors = False

            if teams_settings[team][0]["is_secondary_color_toggled"]:
                print(teams_settings[team][0]["is_secondary_color_toggled"])
                print(teams_settings)
                secondary_color = RGBColor.fromHEX(
                    teams_settings[team][0]["secondary_color"]
                )

            time.sleep(1)
            set_keyboard_team_color(
                keyboard_coverage=keyboard_coverage,
                main_color=RGBColor.fromHEX(teams_settings[team][0]["main_color"]),
                secondary_color=secondary_color,
                blend_colors=blend_colors,
            )
            cycle += 1

        time.sleep(refresh_time)


teams_settings = {
    "-TEAM1-": [
        {
            "main_color": "#FF0000",
            "secondary_color": "#0000FF",
            "is_secondary_color_toggled": True,
        }
    ],
    "-TEAM2-": [
        {
            "main_color": "#FF0000",
            "secondary_color": "#0000FF",
            "is_secondary_color_toggled": True,
        }
    ],
}

layout = [
    [color_row("Team 1 (Home)", 1)],
    [color_row("Team 2 (Away)", 2)],
    [
        sg.Text("Match to search."),
        sg.Spin([i for i in range(5, 121)], initial_value=10, key="-REFRESH_TIME-"),
        sg.Text("Refresh Time"),
    ],
    [sg.Input(key="-IN-")],
    [sg.Button("Start"), sg.Button("Stop"), sg.Button("Exit")],
]

window = sg.Window("Pattern 2B", layout)

while True:  # Event Loops
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED or event == "Exit":
        break

    if event == "Start":
        find_match(values["-IN-"])
        window.start_thread(
            lambda: set_keyboard_for_match(values["-REFRESH_TIME-"]),
            "-SET_KEYBOARD_FOR_MATCH_COMPLETED-",
        )

    if event[0] is not None and "TEAM" in event[0]:  # event[0] is the team, event[1] is the element event for the team
        team = event[0]
        element_event = event[1]
        if "TOGGLE_SECOND_COLOR" in element_event:
            window[(team, "-SECONDARY_COLOR_BUTTON-")].update(
                visible=not window[(event[0], "-SECONDARY_COLOR_BUTTON-")].visible
            )
            teams_settings[team][0]["is_secondary_color_toggled"] = not teams_settings[
                team
            ][0]["is_secondary_color_toggled"]
        elif "COLOR_BUTTON" in element_event:
            dialog = QColorDialog()
            color = dialog.getColor().name()
            window[(team, element_event)].update(button_color=(color, color))
            if "-MAIN_COLOR_BUTTON-" == element_event:  # switch case for all of this?
                teams_settings[team][0]["main_color"] = color
            elif "-SECONDARY_COLOR_BUTTON-" == element_event:
                teams_settings[team][0]["secondary_color"] = color

window.close()
