from openrgb import OpenRGBClient
from openrgb.utils import DeviceType
from openrgb.utils import RGBColor
from PyQt5.QtWidgets import QApplication, QColorDialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import math
import PySimpleGUI as sg
import time

APP = QApplication([])

SETTINGS = sg.UserSettings(path=".")
SETTINGS.load()
GENERAL_SETTINGS = "-general-"

CLI = OpenRGBClient()
USERS_KEYB = CLI.get_devices_by_type(DeviceType.KEYBOARD)[
    SETTINGS[GENERAL_SETTINGS]["-keyboard_number-"]
]
KEYB_LENGTH = len(USERS_KEYB.colors)

MIN_REFRESH_TIME = 10
MAX_REFRESH_TIME = 121
WEBDRIVERS = {"gecko_driver": "-GECKO_DRIVER-", "chrome_driver": "-CHROME_DRIVER-"}
STATISTIC_TYPES = {
    "Shots": 0,
    "Shots On Target": 1,
    "Possession": 2,
    "Passes": 3,
    "Pass Accuracy": 4,
    "Fouls": 5,
    "Yellow Cards": 6,
    "Red Cards": 7,
    "Offsides": 8,
    "Corners": 9,
}

KEY_COLUMNS = {  # make a dictionary that shows what number is what key?
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

KEY_ROWS = {
    0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    1: [16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
    2: [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
    3: [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63],
    4: [64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75],
    5: [76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86],
}


def update_status(text):
    window["-STATUS-"].update(text)


def find_item_in_dict(item, dict):
    for key, value in dict.items():
        if item == value:
            return value
    return None


def get_decimal(number):
    number = number % 1
    return number


def remove_non_numbers(string):
    return "".join(c for c in string if c.isdigit())


# mix colors - used for transitioning between colors
def mix_colors(color1_opacity, color1, color2):
    color2_opacity = 1 - color1_opacity
    color1_RGB_array = split_color_to_RGB_array(color1)
    color2_RGB_array = split_color_to_RGB_array(color2)
    mixed_color_RGB_array = []

    for i in range(0, len(color1_RGB_array)):
        color1_attribute = round(color1_opacity * color1_RGB_array[i])
        color2_attribute = round(color2_opacity * color2_RGB_array[i])
        mixed_color_attribute = round(color1_attribute + color2_attribute / 2)
        mixed_color_RGB_array.append(mixed_color_attribute)

    mixed_color = RGBColor(
        mixed_color_RGB_array[0], mixed_color_RGB_array[1], mixed_color_RGB_array[2]
    )
    return mixed_color


def split_color_to_RGB_array(color):
    color = [color.red, color.green, color.blue]
    return color


def find_match(driver, match):
    driver.get("https://google.com")
    search_box = driver.find_element(by=By.CLASS_NAME, value="gLFyf")
    search_box.send_keys(match)
    search_box.send_keys(Keys.ENTER)
    match_info = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "imso_mh__ma-sc-cont"))
    )
    match_info.click()


# picks and finds your chosen statistic on the page
def scrape_chosen_statistic(statistic_type):
    all_stats = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "MzWkAb"))
    )

    chosen_statistic_index = STATISTIC_TYPES[statistic_type]
    chosen_statistic_class = all_stats[chosen_statistic_index]
    chosen_statistic_stats = chosen_statistic_class.find_elements(
        by=By.TAG_NAME, value="td"
    )

    home_chosen_statistic_stat = int(
        remove_non_numbers(chosen_statistic_stats[0].get_attribute("innerHTML"))
    )
    away_chosen_statistic_stat = int(
        remove_non_numbers(chosen_statistic_stats[1].get_attribute("innerHTML"))
    )

    # return's the home team's percentage of the total chosen stat
    # E.G the home team has 2 out of 5 shots on goal in total, it would return 20%
    # and thus the home team's color would take up 20% of the space on the keyboard
    total_stat_percentage = home_chosen_statistic_stat + away_chosen_statistic_stat
    home_percentage_of_total_stat = round(
        home_chosen_statistic_stat / total_stat_percentage * 100
    )

    driver.refresh()
    return home_percentage_of_total_stat


def set_keyboard_team_color(
    percent_of_keyb_covered=100,
    main_color="#FFFFFF",
    blend_colors=None,
    secondary_color=None,
):
    adjusted_percent_of_keyb_covered = (percent_of_keyb_covered / 100) * len(
        KEY_COLUMNS
    )
    num_of_key_columns_to_change = math.ceil(adjusted_percent_of_keyb_covered)
    color_spectrum = USERS_KEYB.colors
    for key_column in range(0, num_of_key_columns_to_change):
        for key in KEY_COLUMNS[key_column]:
            color_to_set_key = main_color
            if secondary_color:
                # we use [1::2] to make the stripe pattern when a second color is selected
                for key_row in sorted(KEY_ROWS.values())[1::2]:
                    if key in key_row:
                        color_to_set_key = secondary_color

            if blend_colors:
                if key_column == num_of_key_columns_to_change - 1:
                    # minus 1 so the rounded possession matches up with the key columns
                    mixed_color_to_account_for_decimals = mix_colors(
                        get_decimal(adjusted_percent_of_keyb_covered),
                        color_to_set_key,
                        USERS_KEYB.colors[key],
                    )
                    color_to_set_key = mixed_color_to_account_for_decimals
            color_spectrum[key] = color_to_set_key

    return color_spectrum


# defines a button that lets you pick a color for a team
def color_button(team, key, secondary_color):
    if secondary_color:
        color = SETTINGS[team]["-secondary_color-"]
        visibility = SETTINGS[team]["-secondary_color_toggled-"]
    else:
        color = SETTINGS[team]["-main_color-"]
        visibility = True

    return sg.Button(
        key=(team, key), button_color=color, size=(8, 4), visible=visibility
    )


def team_options(team):
    return sg.Checkbox(
        "Secondary Color",
        key=(team, "-TOGGLE_SECOND_COLOR-"),
        default=SETTINGS[team]["-secondary_color_toggled-"],
        enable_events=True,
    )


# a team's color buttons and options
def team_color_buttons(header, team):
    return [
        [sg.Text(header), team_options(team)],
        [
            color_button(team, "-MAIN_COLOR_BUTTON-", False),
            color_button(team, "-SECONDARY_COLOR_BUTTON-", True),
        ],
    ]


# the cycle that controls scraping during the match
def scrape_in_cycle_for_match(refresh_time, statistic_type):
    while True:
        cycle = 0

        if event == "Stop":
            update_status("Stopped.")
            break

        # we reverse so we draw the away team's color first,
        # and then the home team on top of it
        for team in reversed(list(SETTINGS.dict.keys())):
            percent_of_keyb_covered = scrape_chosen_statistic(statistic_type)
            secondary_color = None
            blend_colors = True

            if cycle == 0:
                percent_of_keyb_covered = 100
                blend_colors = False

            if "team" in team.lower():
                if SETTINGS[team]["-secondary_color_toggled-"]:
                    secondary_color = RGBColor.fromHEX(
                        SETTINGS[team]["-secondary_color-"]
                    )

                color_spectrum = set_keyboard_team_color(
                    percent_of_keyb_covered=percent_of_keyb_covered,
                    main_color=RGBColor.fromHEX(SETTINGS[team]["-main_color-"]),
                    secondary_color=secondary_color,
                    blend_colors=blend_colors,
                )
                cycle += 1

        USERS_KEYB.set_colors(color_spectrum)
        update_status(
            time.strftime("Success! Keyboard colors last updated at %I:%M:%S %p")
        )
        print("Keyboard colors set.")
        time.sleep(refresh_time)


sg.theme("DarkAmber")
layout = [
    [
        sg.Text("Scraper Type:"),
        sg.Radio(
            "Chrome",
            "DRIVER_TYPE",
            default=(
                SETTINGS[GENERAL_SETTINGS]["-driver_type-"]
                == WEBDRIVERS["chrome_driver"]
            ),
            key="-CHROME_DRIVER-",
            enable_events=True,
        ),
        sg.Radio(
            "Firefox",
            "DRIVER_TYPE",
            default=(
                SETTINGS[GENERAL_SETTINGS]["-driver_type-"]
                == WEBDRIVERS["gecko_driver"]
            ),
            key=WEBDRIVERS["gecko_driver"],
            enable_events=True,
        ),
    ],
    [
        sg.Checkbox(
            "See scraper window",
            key="-SEE_WINDOW-",
            default=SETTINGS[GENERAL_SETTINGS]["-SEE_WINDOW-"],
        )
    ],
    [
        sg.pin(
            sg.Column(
                [
                    [
                        sg.Text("Select Firefox EXE"),
                        sg.Input(
                            default_text=SETTINGS[GENERAL_SETTINGS][
                                "-FIREFOX_EXE_PATH-"
                            ],
                            size=(14, 1),
                            key="-FIREFOX_EXE_PATH-",
                        ),
                        sg.FileBrowse(),
                    ]
                ],
                key="-SELECT_FIREFOX_EXE-",
                visible=(
                    SETTINGS[GENERAL_SETTINGS]["-driver_type-"]
                    == WEBDRIVERS["gecko_driver"]
                ),
            )
        )
    ],
    [
        sg.Text("Refresh Time"),
        sg.Spin(
            [i for i in range(MIN_REFRESH_TIME, MAX_REFRESH_TIME)],
            initial_value=SETTINGS[GENERAL_SETTINGS]["-REFRESH_TIME-"],
            key="-REFRESH_TIME-",
        ),
    ],
    [sg.HorizontalSeparator()],
    [team_color_buttons("Team 1 (Home)", "-TEAM1-")],
    [team_color_buttons("Team 2 (Away)", "-TEAM2-")],
    [sg.Text("Match to search"), sg.Push(), sg.Text("Choose statistic")],
    [
        sg.Input(
            default_text=SETTINGS[GENERAL_SETTINGS]["-IN-"], key="-IN-", size=(24, 1)
        ),
        sg.Combo(
            [
                "Shots",
                "Shots On Target",
                "Possession",
                "Passes",
                "Pass Accuracy",
                "Fouls",
                "Yellow Cards",
                "Red Cards",
                "Offsides",
                "Corners",
            ],
            key="-STATISTIC_TYPE-",
            default_value=SETTINGS[GENERAL_SETTINGS]["-STATISTIC_TYPE-"],
        ),
    ],
    [sg.Button("Start"), sg.Button("Stop"), sg.Button("Exit")],
    [sg.Text("Booted up.", key="-STATUS-")],
]

window = sg.Window("SoccerStats RGB", layout)


def button_events(event):
    # event[0] is the team, event[1] is the element event for the team
    if "TEAM" in event[0]:
        team = event[0]
        element_event = event[1]
        if "TOGGLE_SECOND_COLOR" in element_event:
            window[(team, "-SECONDARY_COLOR_BUTTON-")].update(
                visible=not window[(event[0], "-SECONDARY_COLOR_BUTTON-")].visible
            )
            SETTINGS[team]["-secondary_color_toggled-"] = not SETTINGS[team][
                "-secondary_color_toggled-"
            ]

        elif "COLOR_BUTTON" in element_event:
            dialog = QColorDialog()
            color = dialog.getColor().name()
            window[(team, element_event)].update(button_color=(color, color))
            match element_event:
                case "-MAIN_COLOR_BUTTON-":
                    SETTINGS[team]["-main_color-"] = color
                case "-SECONDARY_COLOR_BUTTON-":
                    SETTINGS[team]["-secondary_color-"] = color
        save_team_settings(team)


def save_general_settings(values=None):
    if values:
        general_settings_list = [
            "-IN-",
            "-SEE_WINDOW-",
            "-REFRESH_TIME-",
            "-FIREFOX_EXE_PATH-",
            "-STATISTIC_TYPE-",
        ]

        for setting in general_settings_list:
            SETTINGS[GENERAL_SETTINGS][setting] = values[setting]
    # doing this to register key and save to due pysimplegui quirk
    SETTINGS[GENERAL_SETTINGS] = SETTINGS[GENERAL_SETTINGS]


def save_team_settings(team):
    # doing this to register key and save to due pysimplegui quirk
    SETTINGS[team] = SETTINGS[team]


# sets your chosen driver
def check_chosen_driver(values):
    for driver_name_key, driver_name in WEBDRIVERS.items():
        if values[driver_name]:
            selected_driver = driver_name
            SETTINGS[GENERAL_SETTINGS]["-driver_type-"] = selected_driver
            save_general_settings()
            if selected_driver == WEBDRIVERS["chrome_driver"]:
                Options = webdriver.ChromeOptions()
                if not values["-SEE_WINDOW-"]:
                    Options.headless = True
                service = Service(executable_path="./chromedriver.exe")
                driver = webdriver.Chrome(service=service, options=Options)

            if selected_driver == WEBDRIVERS["gecko_driver"]:
                Options = webdriver.FirefoxOptions()
                Options.binary_location = values["-FIREFOX_EXE_PATH-"]
                if not values["-SEE_WINDOW-"]:
                    Options.headless = True
                service = Service(executable_path="./geckodriver.exe")
                driver = webdriver.Firefox(service=service, options=Options)
    return driver


while True:  # Event Loops
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Exit":
        break

    button_events(event)

    if find_item_in_dict(event, WEBDRIVERS):
        if event == WEBDRIVERS["gecko_driver"]:
            window["-SELECT_FIREFOX_EXE-"].update(visible=True)
        else:
            window["-SELECT_FIREFOX_EXE-"].update(visible=False)

    if event == "Start":  # general settings
        update_status("Started! Saving settings...")
        save_general_settings(values)
        update_status("Registering chosen driver...")
        driver = check_chosen_driver(values)
        update_status("Finding match...")
        find_match(driver, values["-IN-"])
        update_status("On webpage. Attempting to get info...")
        window.start_thread(
            lambda: scrape_in_cycle_for_match(
                values["-REFRESH_TIME-"], values["-STATISTIC_TYPE-"]
            ),
            "-SET_KEYBOARD_FOR_MATCH_COMPLETED-",
        )


window.close()
