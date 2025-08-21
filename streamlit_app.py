# correctly realizes when in a different set
# correctly distinguishes between sets
# loads current triangle and overall triangle
# 8/12/25 9:23

import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from io import BytesIO
# from util import email
import os


# Set a password for access
# CORRECT_PASSWORD = "huskies"


def initiate_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "sets" not in st.session_state:
        st.session_state.sets = {i: [] for i in range(1, 6)}
    if "opp" not in st.session_state:
        st.session_state.opp = "Opp"
    if "set" not in st.session_state:
        st.session_state.set = 1
    if "set_data" not in st.session_state:
        st.session_state.set_data = {
            i: {
                "our_score": 0,
                "opp_score": 0,
                "stats": {
                    "our_ts_ace": 0, "our_ts_err": 0, "opp_ts_ace": 0, "opp_ts_err": 0,
                    "our_fb_kills": 0, "our_fb_stop": 0, "opp_fb_kills": 0, "opp_fb_stop": 0,
                    "our_fb_blks": 0, "our_fb_ae": 0, "opp_fb_blks": 0, "opp_fb_ae": 0,
                    "our_trs_kills": 0, "our_trs_stop": 0, "opp_trs_kills": 0, "opp_trs_stop": 0,
                    "our_trs_blks": 0, "our_trs_ae": 0, "opp_trs_blks": 0, "opp_trs_ae": 0
                }
            } for i in range(1, 6)
        }


def undo_previous_play():
    try:
        current_set = st.session_state.set
        set_info = st.session_state.set_data[current_set]

        if not st.session_state.sets[current_set]:
            st.write("Can't undo previous play, no plays have been made")
            return

        undone_play = st.session_state.sets[current_set].pop()
        play_result = undone_play[0]
        sign = undone_play[1]

        if sign == "+":
            set_info["our_score"] -= 1
        elif sign == "-":
            set_info["opp_score"] -= 1

        stat_map = {
            "UConn Serve Ace": ["our_ts_ace"],
            "UConn Serve Error": ["our_ts_err"],
            f"{st.session_state.opp} Serve Ace": ["opp_ts_ace"],
            f"{st.session_state.opp} Serve Error": ["opp_ts_err"],
            "UConn First Ball Kills": ["our_fb_kills"],
            f"UConn Stops {st.session_state.opp} First Ball - Blocked": ["our_fb_stop", "our_fb_blks"],
            f"UConn Stops {st.session_state.opp} First Ball - Out of Bounds": ["our_fb_stop", "our_fb_ae"],
            f"{st.session_state.opp} First Ball Kills": ["opp_fb_kills"],
            f"{st.session_state.opp} Stops UConn First Ball - Blocked": ["opp_fb_stop", "opp_fb_blks"],
            f"{st.session_state.opp} Stops UConn First Ball - Out of Bounds": ["opp_fb_stop", "opp_fb_ae"],
            "UConn Transition Kills": ["our_trs_kills"],
            f"UConn Stops {st.session_state.opp} Transition - Blocked": ["our_trs_stop", "our_trs_blks"],
            f"UConn Stops {st.session_state.opp} Transition - Out of Bounds": ["our_trs_stop", "our_trs_ae"],
            f"{st.session_state.opp} Transition Kills": ["opp_trs_kills"],
            f"{st.session_state.opp} Stops UConn Transition - Blocked": ["opp_trs_stop", "opp_trs_blks"],
            f"{st.session_state.opp} Stops UConn Transition - Out of Bounds": ["opp_trs_stop", "opp_trs_ae"]
        }

        if play_result in stat_map:
            for stat in stat_map[play_result]:
                set_info["stats"][stat] -= 1

        st.success(f"Undid play: {play_result}")
    except Exception as e:
        st.write(f"Error undoing play: {e}")


def log_play_to_set(play):
    current_set = st.session_state.set
    set_info = st.session_state.set_data[current_set]

    play_result = play[0]
    sign = play[1]

    stat_map = {
        "UConn Serve Ace": ["our_ts_ace"],
        "UConn Serve Error": ["our_ts_err"],
        f"{st.session_state.opp} Serve Ace": ["opp_ts_ace"],
        f"{st.session_state.opp} Serve Error": ["opp_ts_err"],
        "UConn First Ball Kills": ["our_fb_kills"],
        f"UConn Stops {st.session_state.opp} First Ball - Blocked": ["our_fb_stop", "our_fb_blks"],
        f"UConn Stops {st.session_state.opp} First Ball - Out of Bounds": ["our_fb_stop", "our_fb_ae"],
        f"{st.session_state.opp} First Ball Kills": ["opp_fb_kills"],
        f"{st.session_state.opp} Stops UConn First Ball - Blocked": ["opp_fb_stop", "opp_fb_blks"],
        f"{st.session_state.opp} Stops UConn First Ball - Out of Bounds": ["opp_fb_stop", "opp_fb_ae"],
        "UConn Transition Kills": ["our_trs_kills"],
        f"UConn Stops {st.session_state.opp} Transition - Blocked": ["our_trs_stop", "our_trs_blks"],
        f"UConn Stops {st.session_state.opp} Transition - Out of Bounds": ["our_trs_stop", "our_trs_ae"],
        f"{st.session_state.opp} Transition Kills": ["opp_trs_kills"],
        f"{st.session_state.opp} Stops UConn Transition - Blocked": ["opp_trs_stop", "opp_trs_blks"],
        f"{st.session_state.opp} Stops UConn Transition - Out of Bounds": ["opp_trs_stop", "opp_trs_ae"]
    }

    if play_result in stat_map:
        for stat in stat_map[play_result]:
            set_info["stats"][stat] += 1

    if sign == "+":
        set_info["our_score"] += 1
    elif sign == "-":
        set_info["opp_score"] += 1

    expanded_play = (
        play_result,
        sign,
        datetime.now(),
        set_info["our_score"],
        set_info["opp_score"]
    )

    st.session_state.sets[current_set].append(expanded_play)

def export_to_excel():
    # When end of game button is clicked, saves all data and sends it out as an excel file
    filename = f"data/UConn vs {st.session_state.opp} - {datetime.today().strftime('%Y-%m-%d')} Triangle Stats.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # add each set to excel
        for i, set_data in enumerate(st.session_state.sets):
            df = pd.DataFrame(set_data, columns=["Play Result", "Triangle +/-", "Timestamp", "UConn", st.session_state.opp])
            df.to_excel(writer, sheet_name=f"Set {i+1} Log")

        # add better set information (blks, ae)
        for i, set_stats in enumerate(st.session_state.set_data):
            df = pd.DataFrame(set_stats)
            df.to_excel(writer, sheet_name=f"Set {i+1} Stats")

        # adds triangle by set (+ overall triangle per game)
        sets_by_triangle = triangle_by_set()
        df = pd.DataFrame(sets_by_triangle)
        df.toexcel(writer, sheet_name=f"Triangle Stats")

    send_excel_emails(filename)

def send_excel_emails(file):
    try:
        email.send_mail(send_from='owen.babiec@uconn.edu',
                        send_to=['owen.babiec@uconn.edu'],
                        subject=f"UConn vs {st.session_state.opp} - {datetime.today().strftime('%Y-%m-%d')} Triangle Stats",
                        text=f"Here's the excel files for this game",
                        files=[file]
                        )
        st.success("Emails sent successfully")
    except Exception as e:
        st.write(f"Error sending email: {e}")

def display_data():
    current_set = st.session_state.set
    st.subheader(f"Set {current_set} Play Log")
    set_data = st.session_state.sets[current_set]
    df = pd.DataFrame(set_data, columns=["Play Result", "+/-", "Timestamp", "UConn", st.session_state.opp])
    st.dataframe(df)


def calculate_triangle_stats():
    triangle_stats = {}
    overall_stats = {
        "Terminal Serve": 0,
        "First Ball": 0,
        "Transition": 0
    }

    for set_num in range(1, 6):
        stats = st.session_state.set_data[set_num]["stats"]
        terminal_serve = stats["our_ts_ace"] - stats["our_ts_err"] - stats["opp_ts_ace"] + stats["opp_ts_err"]
        first_ball = stats["our_fb_kills"] + stats["our_fb_stop"] - stats["opp_fb_kills"] - stats["opp_fb_stop"]
        transition = stats["our_trs_kills"] + stats["our_trs_stop"] - stats["opp_trs_kills"] - stats["opp_trs_stop"]

        triangle_stats[set_num] = {
            "Set #": set_num,
            "Terminal Serve": terminal_serve,
            "First Ball": first_ball,
            "Transition": transition
        }

        overall_stats["Terminal Serve"] += terminal_serve
        overall_stats["First Ball"] += first_ball
        overall_stats["Transition"] += transition

    return triangle_stats, overall_stats

def display_triangle_stats(triangle_stats, overall_stats):
    current_set = st.session_state.set

    st.subheader(f"Triangle Stats - Set {current_set}")
    current_df = pd.DataFrame([triangle_stats[current_set]])
    st.dataframe(current_df)

    st.subheader("Triangle Stats - Overall Game")
    overall_df = pd.DataFrame([overall_stats])
    st.dataframe(overall_df)

def triangle_by_set():
    triangle_stats = []
    for set_num in range(1, 6):
        stats = st.session_state.set_data[set_num]["stats"]
        terminal_serve = stats["our_ts_ace"] - stats["our_ts_err"] - stats["opp_ts_ace"] + stats["opp_ts_err"]
        first_ball = stats["our_fb_kills"] + stats["our_fb_stop"] - stats["opp_fb_kills"] - stats["opp_fb_stop"]
        transition = stats["our_trs_kills"] + stats["our_trs_stop"] - stats["opp_trs_kills"] - stats["opp_trs_stop"]
        triangle_stats.append({
            "Set #": set_num,
            "Terminal Serve": terminal_serve,
            "First Ball": first_ball,
            "Transition": transition
        })

    overall_total = {
        "Set #" : "Overall Game",
        "Terminal Serve": sum(row["Terminal Serve"] for row in triangle_stats),
        "First Ball": sum(row["First Ball"] for row in triangle_stats),
        "Transition": sum(row["Transition"] for row in triangle_stats)
    }

    triangle_stats.append(overall_total)

    return pd.DataFrame(triangle_stats)


# Password prompt
# if not st.session_state.authenticated:
#     st.title("Volleyball Stat Tracker")
#     password = st.text_input("Enter password to access the tracker:", type="password")
#     if password == CORRECT_PASSWORD:
#         st.session_state.authenticated = True
#         st.success("Access granted!")
#     elif password:
#         st.error("Incorrect password")
# else:

# Streamlit UI
initiate_session()
st.title("UConn Volleyball Stat Tracker")


st.session_state.opp = st.text_input("Opponent:", value=st.session_state.opp)
st.session_state.set = st.radio("Select Set", [1, 2, 3, 4, 5])
st.session_state.game_date = st.date_input("Game date:")

# Layout for stat tracking
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("Terminal Serve")
    if st.button("UConn Serve Ace"):
        log_play_to_set(("UConn Serve Ace", "+"))
    if st.button("UConn Serve Error"):
        log_play_to_set(("UConn Serve Error", "-"))
    if st.button(f"{st.session_state.opp} Serve Ace"):
        log_play_to_set((f"{st.session_state.opp} Serve Ace", "-"))
    if st.button(f"{st.session_state.opp} Serve Error"):
        log_play_to_set((f"{st.session_state.opp} Serve Error", "+"))

with col2:
    st.subheader("First Ball")
    if st.button("UConn First Ball Kills"):
        log_play_to_set(("UConn First Ball Kills", "+"))
    if st.button(f"UConn Stops {st.session_state.opp} First Ball - Blocked"):
        log_play_to_set((f"UConn Stops {st.session_state.opp} First Ball - Blocked", "+"))
    if st.button(f"UConn Stops {st.session_state.opp} First Ball - Out of Bounds"):
        log_play_to_set((f"UConn Stops {st.session_state.opp} First Ball - Out of Bounds", "+"))
    if st.button(f"{st.session_state.opp} First Ball Kills"):
        log_play_to_set((f"{st.session_state.opp} First Ball Kills", "-"))
    if st.button(f"{st.session_state.opp} Stops UConn First Ball - Blocked"):
        log_play_to_set((f"{st.session_state.opp} Stops UConn First Ball - Blocked", "-"))
    if st.button(f"{st.session_state.opp} Stops UConn First Ball - Out of Bounds"):
        log_play_to_set((f"{st.session_state.opp} Stops UConn First Ball - Out of Bounds", "-"))

with col3:
    st.subheader("Transition")
    if st.button("UConn Transition Kills"):
        log_play_to_set(("UConn Transition Kills", "+"))
    if st.button(f"UConn Stops {st.session_state.opp} Transition - Blocked"):
        log_play_to_set((f"UConn Stops {st.session_state.opp} Transition - Blocked", "+"))
    if st.button(f"UConn Stops {st.session_state.opp} Transition - Out of Bounds"):
        log_play_to_set((f"UConn Stops {st.session_state.opp} Transition - Out of Bounds", "+"))
    if st.button(f"{st.session_state.opp} Transition Kills"):
        log_play_to_set((f"{st.session_state.opp} Transition Kills", "-"))
    if st.button(f"{st.session_state.opp} Stops UConn Transition - Blocked"):
        log_play_to_set((f"{st.session_state.opp} Stops UConn Transition - Blocked", "-"))
    if st.button(f"{st.session_state.opp} Stops UConn Transition - Out of Bounds"):
        log_play_to_set((f"{st.session_state.opp} Stops UConn Transition - Out of Bounds", "-"))

with col4:
    st.subheader("Other Actions")
    if st.button("Award Point to UConn"):
        log_play_to_set((f"Award Point to UConn", "+"))
    if st.button(f"Award Point to {st.session_state.opp}"):
        log_play_to_set((f"Award Point to {st.session_state.opp}", "-"))

    if st.button("Undo previous play"):
        undo_previous_play()

# Displays set log, triangle per set and overall game triangle
display_data()
curr_triangle, ovr_triangle = calculate_triangle_stats()
display_triangle_stats(curr_triangle, ovr_triangle)

triangle_by_sets = triangle_by_set()
st.dataframe(triangle_by_sets)


if st.button("End of game, export data to email"):
    export_to_excel()



