# correctly realizes when in a different set
# correctly distinguishes between sets
# loads current triangle and overall triangle
# 8/12/25 9:23

import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from io import BytesIO
from util import send_email_with_attachment
import os
import openpyxl


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
                    "our_fb_stuff": 0, "opp_fb_he": 0, "opp_fb_err": 0,
                    "opp_fb_stuff": 0, "our_fb_he": 0, "our_fb_err": 0,

                    "our_trs_kills": 0, "our_trs_stop": 0, "opp_trs_kills": 0, "opp_trs_stop": 0,
                    "our_trs_stuff": 0, "opp_trs_he": 0, "opp_trs_err": 0,
                    "opp_trs_stuff": 0, "our_trs_he": 0, "our_trs_err": 0
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
            "UConn Ace": ["our_ts_ace"],
            "UConn SE": ["our_ts_err"],
            f"{st.session_state.opp} Ace": ["opp_ts_ace"],
            f"{st.session_state.opp} SE": ["opp_ts_err"],

            "UConn FB Kill": ["our_fb_kills"],
            "UConn Stuff Block FB": ["our_fb_stop", "our_fb_stuff"],
            f"{st.session_state.opp} Hitting Error FB": ["our_fb_stop", "opp_fb_he"],
            f"{st.session_state.opp} Error FB (BHE, Net etc.)": ["our_fb_stop", "opp_fb_err"],

            f"{st.session_state.opp} FB Kill": ["opp_fb_kills"],
            f"{st.session_state.opp} Stuff Block FB": ["opp_fb_stop", "opp_fb_stuff"],
            "UConn Hitting Error FB": ["opp_fb_stop", "our_fb_he"],
            "UConn Error FB (BHE, Net etc.)": ["opp_fb_stop", "our_fb_err"],

            "UConn TR Kill": ["our_trs_kills"],
            "UConn Stuff Block TR": ["our_trs_stop", "our_trs_stuff"],
            f"{st.session_state.opp} Hitting Error TR": ["our_trs_stop", "opp_trs_he"],
            f"{st.session_state.opp} Error TR (BHE, Net etc.)": ["our_trs_stop", "opp_trs_err"],

            f"{st.session_state.opp} TR Kill": ["opp_trs_kills"],
            f"{st.session_state.opp} Stuff Block TR": ["opp_trs_stop", "opp_trs_stuff"],
            "UConn Hitting Error TR": ["opp_trs_stop", "our_trs_he"],
            "UConn Error TR (BHE, Net etc.)": ["opp_trs_stop", "our_trs_err"]
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
            "UConn Ace": ["our_ts_ace"],
            "UConn SE": ["our_ts_err"],
            f"{st.session_state.opp} Ace": ["opp_ts_ace"],
            f"{st.session_state.opp} SE": ["opp_ts_err"],

            "UConn FB Kill": ["our_fb_kills"],
            "UConn Stuff Block FB": ["our_fb_stop", "our_fb_stuff"],
            f"{st.session_state.opp} Hitting Error FB": ["our_fb_stop", "opp_fb_he"],
            f"{st.session_state.opp} Error FB (BHE, Net etc.)": ["our_fb_stop", "opp_fb_err"],

            f"{st.session_state.opp} FB Kill": ["opp_fb_kills"],
            f"{st.session_state.opp} Stuff Block FB": ["opp_fb_stop", "opp_fb_stuff"],
            "UConn Hitting Error FB": ["opp_fb_stop", "our_fb_he"],
            "UConn Error FB (BHE, Net etc.)": ["opp_fb_stop", "our_fb_err"],

            "UConn TR Kill": ["our_trs_kills"],
            "UConn Stuff Block TR": ["our_trs_stop", "our_trs_stuff"],
            f"{st.session_state.opp} Hitting Error TR": ["our_trs_stop", "opp_trs_he"],
            f"{st.session_state.opp} Error TR (BHE, Net etc.)": ["our_trs_stop", "opp_trs_err"],

            f"{st.session_state.opp} TR Kill": ["opp_trs_kills"],
            f"{st.session_state.opp} Stuff Block TR": ["opp_trs_stop", "opp_trs_stuff"],
            "UConn Hitting Error TR": ["opp_trs_stop", "our_trs_he"],
            "UConn Error TR (BHE, Net etc.)": ["opp_trs_stop", "our_trs_err"]
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
            df = pd.DataFrame(set_data, columns=["Play Result", "Triangle +/-", "UConn", st.session_state.opp])
            df.to_excel(writer, sheet_name=f"Set {i+1} Log")

        # todo: change to one table for all of the set data (sets 1-5, plus total game)
        for i, set_stats in enumerate(st.session_state.set_data):
            df = pd.DataFrame(set_stats)
            df.to_excel(writer, sheet_name=f"Set {i+1} Stats")

        # adds triangle by set (+ overall triangle per game)
        sets_by_triangle = triangle_by_set()
        df = pd.DataFrame(sets_by_triangle)
        df.to_excel(writer, sheet_name="Triangle Stats")

        # adds triangle % by set (+ overall % triangle per game)
        sets_by_triangle_pcts = triangle_percentage_by_set()
        df = pd.DataFrame(sets_by_triangle_pcts)
        df.to_excel(writer, sheet_name="Triangle Percentages")

        overall_stats = overall_game_stats()
        df = pd.DataFrame(overall_stats)
        df.to_excel(writer, sheet_name="Overall Game Stats")

    send_excel_emails(filename)

def send_excel_emails(file):
    try:
        send_email_with_attachment(
                        sender_email='owenbabiec@gmail.com',
                        sender_password="wmxdajqjjexvopxh",
                        recipient_email=['owen.babiec@uconn.edu'],
                        subject=f"UConn vs {st.session_state.opp} - {datetime.today().strftime('%Y-%m-%d')} Triangle Stats",
                        body=f"Here's the excel files for this game",
                        attachments=[file]
                        )
        st.success("Emails sent successfully")
    except Exception as e:
        st.warning(f"Error sending email: {e}")

def display_data():
    current_set = st.session_state.set
    st.subheader(f"Set {current_set} Play Log")
    set_data = st.session_state.sets[current_set]
    df = pd.DataFrame(set_data, columns=["Play Result", "+/-", "UConn", st.session_state.opp])
    st.dataframe(df)


def display_triangle_stats(triangle_stats, overall_stats):
    current_set = st.session_state.set

    st.subheader(f"Triangle Stats - Set {current_set}")
    current_df = pd.DataFrame([triangle_stats[current_set]])
    st.dataframe(current_df)

    st.subheader("Triangle Stats - Overall Game")
    overall_df = pd.DataFrame([overall_stats])
    st.dataframe(overall_df)

def triangle_by_set():
    st.subheader("Triangle Stats")
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
        "Set #" : "Game",
        "Terminal Serve": sum(row["Terminal Serve"] for row in triangle_stats),
        "First Ball": sum(row["First Ball"] for row in triangle_stats),
        "Transition": sum(row["Transition"] for row in triangle_stats)
    }

    triangle_stats.append(overall_total)

    return pd.DataFrame(triangle_stats)

def overall_game_stats():
    triangle_stats = []
    for set_num in range(1, 6):
        stats = st.session_state.set_data[set_num]["stats"]
        triangle_stats.append({
            "Set #": set_num, 
            "UConn Ace": stats["our_ts_ace"],
            "UConn SE": stats["our_ts_err"],
            f"{st.session_state.opp} Ace": stats["opp_ts_ace"],
            f"{st.session_state.opp} SE": stats["opp_ts_err"],

            "UConn FB Kill": stats["our_fb_kills"],
            "UConn FB Stuff Block": stats["our_fb_stuff"],
            "UConn FB Hitting Err": stats["our_fb_he"],
            "UConn FB Error (BHE, Net etc)": stats["our_fb_err"],
            f"{st.session_state.opp} FB Kill": stats["opp_fb_kills"],
            f"{st.session_state.opp} FB Stuff Block": stats["opp_fb_stuff"],
            f"{st.session_state.opp} FB Hitting Err": stats["opp_fb_he"],
            f"{st.session_state.opp} FB Error (BHE, Net etc)": stats["opp_fb_err"],

            "UConn TR Kill": stats["our_trs_kills"],
            "UConn TR Stuff Block": stats["our_trs_stuff"],
            "UConn TR Hitting Err": stats["our_trs_he"],
            "UConn TR Error (BHE, Net etc)": stats["our_trs_err"],
            f"{st.session_state.opp} TR Kill": stats["opp_trs_kills"],
            f"{st.session_state.opp} TR Stuff Block": stats["opp_trs_stuff"],
            f"{st.session_state.opp} TR Hitting Err": stats["opp_trs_he"],
            f"{st.session_state.opp} TR Error (BHE, Net etc)": stats["opp_trs_err"]
        })

    overall_total = ({
        "Set #": "Game Total", 
        # sum(row["Terminal Serve"] for row in triangle_stats)
        "UConn Ace": sum(row["UConn Ace"] for row in triangle_stats),
        "UConn SE": sum(row["UConn SE"] for row in triangle_stats),
        f"{st.session_state.opp} Ace": sum(row[f"{st.session_state.opp} Ace"] for row in triangle_stats),
        f"{st.session_state.opp} SE": sum(row[f"{st.session_state.opp} SE"] for row in triangle_stats),

        "UConn FB Kill": sum(row["UConn FB Kill"] for row in triangle_stats),
        "UConn FB Stuff Block": sum(row["UConn FB Stuff Block"] for row in triangle_stats),
        "UConn FB Hitting Err": sum(row["UConn FB Hitting Err"] for row in triangle_stats),
        "UConn FB Error (BHE, Net etc)": sum(row["UConn FB Error (BHE, Net etc)"] for row in triangle_stats),
        f"{st.session_state.opp} FB Kill": sum(row[f"{st.session_state.opp} FB Kill"] for row in triangle_stats),
        f"{st.session_state.opp} FB Stuff Block": sum(row[f"{st.session_state.opp} FB Stuff Block"] for row in triangle_stats),
        f"{st.session_state.opp} FB Hitting Err": sum(row[f"{st.session_state.opp} FB Hitting Err"] for row in triangle_stats),
        f"{st.session_state.opp} FB Error (BHE, Net etc)": sum(row[f"{st.session_state.opp} FB Error (BHE, Net etc)"] for row in triangle_stats),

        "UConn TR Kill": sum(row["UConn TR Kill"] for row in triangle_stats),
        "UConn TR Stuff Block": sum(row["UConn TR Stuff Block"] for row in triangle_stats),
        "UConn TR Hitting Err": sum(row["UConn TR Hitting Err"] for row in triangle_stats),
        "UConn TR Error (BHE, Net etc)": sum(row["UConn TR Error (BHE, Net etc)"] for row in triangle_stats),
        f"{st.session_state.opp} TR Kill": sum(row[f"{st.session_state.opp} TR Kill"] for row in triangle_stats),
        f"{st.session_state.opp} TR Stuff Block": sum(row[f"{st.session_state.opp} TR Stuff Block"] for row in triangle_stats),
        f"{st.session_state.opp} TR Hitting Err": sum(row[f"{st.session_state.opp} TR Hitting Err"] for row in triangle_stats),
        f"{st.session_state.opp} TR Error (BHE, Net etc)": sum(row[f"{st.session_state.opp} TR Error (BHE, Net etc)"] for row in triangle_stats)
    })

    triangle_stats.append(overall_total)

    return pd.DataFrame(triangle_stats)

def triangle_percentage_by_set():
    st.subheader("Triangle Percentages")
    triangle_stats = []

    for set_num in range(1, 6):
        stats = st.session_state.set_data[set_num]["stats"]

        # Calculate Serve %, FB %, TRS % for this set
        serve_total = (stats["our_ts_ace"] + stats["our_ts_err"] +
                       stats["opp_ts_ace"] + stats["opp_ts_err"])
        serve_pct = ((stats["our_ts_ace"] + stats["opp_ts_err"]) / serve_total * 100
                     if serve_total > 0 else 0)

        fb_total = (stats["our_fb_kills"] + stats["our_fb_stop"] +
                    stats["opp_fb_kills"] + stats["opp_fb_stop"])
        fb_pct = ((stats["our_fb_kills"] + stats["our_fb_stop"]) / fb_total * 100
                  if fb_total > 0 else 0)

        trs_total = (stats["our_trs_kills"] + stats["our_trs_stop"] +
                     stats["opp_trs_kills"] + stats["opp_trs_stop"])
        trs_pct = ((stats["our_trs_kills"] + stats["our_trs_stop"]) / trs_total * 100
                   if trs_total > 0 else 0)

        triangle_stats.append({
            "Set #": set_num,
            "Serve %": round(serve_pct, 1),
            "FB %": round(fb_pct, 1),
            "TRS %": round(trs_pct, 1)
        })

    # Calculate Overall Totals
    overall_our_ts_ace = sum(st.session_state.set_data[s]["stats"]["our_ts_ace"] for s in range(1, 6))
    overall_our_ts_err = sum(st.session_state.set_data[s]["stats"]["our_ts_err"] for s in range(1, 6))
    overall_opp_ts_ace = sum(st.session_state.set_data[s]["stats"]["opp_ts_ace"] for s in range(1, 6))
    overall_opp_ts_err = sum(st.session_state.set_data[s]["stats"]["opp_ts_err"] for s in range(1, 6))

    overall_our_fb_kills = sum(st.session_state.set_data[s]["stats"]["our_fb_kills"] for s in range(1, 6))
    overall_our_fb_stop = sum(st.session_state.set_data[s]["stats"]["our_fb_stop"] for s in range(1, 6))
    overall_opp_fb_kills = sum(st.session_state.set_data[s]["stats"]["opp_fb_kills"] for s in range(1, 6))
    overall_opp_fb_stop = sum(st.session_state.set_data[s]["stats"]["opp_fb_stop"] for s in range(1, 6))

    overall_our_trs_kills = sum(st.session_state.set_data[s]["stats"]["our_trs_kills"] for s in range(1, 6))
    overall_our_trs_stop = sum(st.session_state.set_data[s]["stats"]["our_trs_stop"] for s in range(1, 6))
    overall_opp_trs_kills = sum(st.session_state.set_data[s]["stats"]["opp_trs_kills"] for s in range(1, 6))
    overall_opp_trs_stop = sum(st.session_state.set_data[s]["stats"]["opp_trs_stop"] for s in range(1, 6))

    # Overall percentages
    overall_serve_total = overall_our_ts_ace + overall_our_ts_err + overall_opp_ts_ace + overall_opp_ts_err
    overall_fb_total = overall_our_fb_kills + overall_our_fb_stop + overall_opp_fb_kills + overall_opp_fb_stop
    overall_trs_total = overall_our_trs_kills + overall_our_trs_stop + overall_opp_trs_kills + overall_opp_trs_stop

    overall_serve_pct = ((overall_our_ts_ace + overall_opp_ts_err) / overall_serve_total * 100
                         if overall_serve_total > 0 else 0)
    overall_fb_pct = ((overall_our_fb_kills + overall_our_fb_stop) / overall_fb_total * 100
                      if overall_fb_total > 0 else 0)
    overall_trs_pct = ((overall_our_trs_kills + overall_our_trs_stop) / overall_trs_total * 100
                       if overall_trs_total > 0 else 0)

    overall_total = {
        "Set #": "Game",
        "Serve %": round(overall_serve_pct, 1),
        "FB %": round(overall_fb_pct, 1),
        "TRS %": round(overall_trs_pct, 1)
    }

    triangle_stats.append(overall_total)

    return pd.DataFrame(triangle_stats)

def triangle_percentage_by_set():
    st.subheader("Triangle Percentages")
    triangle_stats = []

    for set_num in range(1, 6):
        stats = st.session_state.set_data[set_num]["stats"]

        # Calculate Serve %, FB %, TRS % for this set
        serve_total = (stats["our_ts_ace"] + stats["our_ts_err"] +
                       stats["opp_ts_ace"] + stats["opp_ts_err"])
        serve_pct = ((stats["our_ts_ace"] + stats["opp_ts_err"]) / serve_total * 100
                     if serve_total > 0 else 0)

        fb_total = (stats["our_fb_kills"] + stats["our_fb_stop"] +
                    stats["opp_fb_kills"] + stats["opp_fb_stop"])
        fb_pct = ((stats["our_fb_kills"] + stats["our_fb_stop"]) / fb_total * 100
                  if fb_total > 0 else 0)

        trs_total = (stats["our_trs_kills"] + stats["our_trs_stop"] +
                     stats["opp_trs_kills"] + stats["opp_trs_stop"])
        trs_pct = ((stats["our_trs_kills"] + stats["our_trs_stop"]) / trs_total * 100
                   if trs_total > 0 else 0)

        triangle_stats.append({
            "Set #": set_num,
            "Serve %": round(serve_pct, 1),
            "FB %": round(fb_pct, 1),
            "TRS %": round(trs_pct, 1)
        })

    # Calculate Overall Totals
    overall_our_ts_ace = sum(st.session_state.set_data[s]["stats"]["our_ts_ace"] for s in range(1, 6))
    overall_our_ts_err = sum(st.session_state.set_data[s]["stats"]["our_ts_err"] for s in range(1, 6))
    overall_opp_ts_ace = sum(st.session_state.set_data[s]["stats"]["opp_ts_ace"] for s in range(1, 6))
    overall_opp_ts_err = sum(st.session_state.set_data[s]["stats"]["opp_ts_err"] for s in range(1, 6))

    overall_our_fb_kills = sum(st.session_state.set_data[s]["stats"]["our_fb_kills"] for s in range(1, 6))
    overall_our_fb_stop = sum(st.session_state.set_data[s]["stats"]["our_fb_stop"] for s in range(1, 6))
    overall_opp_fb_kills = sum(st.session_state.set_data[s]["stats"]["opp_fb_kills"] for s in range(1, 6))
    overall_opp_fb_stop = sum(st.session_state.set_data[s]["stats"]["opp_fb_stop"] for s in range(1, 6))

    overall_our_trs_kills = sum(st.session_state.set_data[s]["stats"]["our_trs_kills"] for s in range(1, 6))
    overall_our_trs_stop = sum(st.session_state.set_data[s]["stats"]["our_trs_stop"] for s in range(1, 6))
    overall_opp_trs_kills = sum(st.session_state.set_data[s]["stats"]["opp_trs_kills"] for s in range(1, 6))
    overall_opp_trs_stop = sum(st.session_state.set_data[s]["stats"]["opp_trs_stop"] for s in range(1, 6))

    # Overall percentages
    overall_serve_total = overall_our_ts_ace + overall_our_ts_err + overall_opp_ts_ace + overall_opp_ts_err
    overall_fb_total = overall_our_fb_kills + overall_our_fb_stop + overall_opp_fb_kills + overall_opp_fb_stop
    overall_trs_total = overall_our_trs_kills + overall_our_trs_stop + overall_opp_trs_kills + overall_opp_trs_stop

    overall_serve_pct = ((overall_our_ts_ace + overall_opp_ts_err) / overall_serve_total * 100
                         if overall_serve_total > 0 else 0)
    overall_fb_pct = ((overall_our_fb_kills + overall_our_fb_stop) / overall_fb_total * 100
                      if overall_fb_total > 0 else 0)
    overall_trs_pct = ((overall_our_trs_kills + overall_our_trs_stop) / overall_trs_total * 100
                       if overall_trs_total > 0 else 0)

    overall_total = {
        "Set #": "Game",
        "Serve %": round(overall_serve_pct, 1),
        "FB %": round(overall_fb_pct, 1),
        "TRS %": round(overall_trs_pct, 1)
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
    if st.button("UConn Ace"):
        log_play_to_set(("UConn Ace", "+"))
    if st.button("UConn SE"):
        log_play_to_set(("UConn SE", "-"))
    if st.button(f"{st.session_state.opp} Ace"):
        log_play_to_set((f"{st.session_state.opp} Ace", "-"))
    if st.button(f"{st.session_state.opp} SE"):
        log_play_to_set((f"{st.session_state.opp} SE", "+"))

with col2:
    st.subheader("First Ball")
    if st.button("UConn FB Kill"):
        log_play_to_set(("UConn FB Kill", "+"))
    if st.button("UConn Stuff Block FB"):
        log_play_to_set(("UConn Stuff Block FB", "+"))
    if st.button(f"{st.session_state.opp} Hitting Error FB"):
        log_play_to_set((f"{st.session_state.opp} Hitting Error FB", "+"))
    if st.button(f"{st.session_state.opp} Error FB (BHE, Net etc.)"):
        log_play_to_set((f"{st.session_state.opp} Error FB (BHE, Net etc.)", "+"))
    
    if st.button(f"{st.session_state.opp} FB Kill"):
        log_play_to_set((f"{st.session_state.opp} FB Kill", "-"))
    if st.button(f"{st.session_state.opp} Stuff Block FB"):
        log_play_to_set((f"{st.session_state.opp} Stuff Block FB", "-"))
    if st.button("UConn Hitting Error FB"):
        log_play_to_set(("UConn Hitting Error FB", "-"))
    if st.button("UConn Error FB (BHE, Net etc.)"):
        log_play_to_set(("UConn Error FB (BHE, Net etc.)", "-"))

with col3:
    st.subheader("Transition")
    if st.button("UConn TR Kill"):
        log_play_to_set(("UConn TR Kill", "+"))
    if st.button("UConn Stuff Block TR"):
        log_play_to_set(("UConn Stuff Block TR", "+"))
    if st.button(f"{st.session_state.opp} Hitting Error TR"):
        log_play_to_set((f"{st.session_state.opp} Hitting Error TR", "+"))
    if st.button(f"{st.session_state.opp} Error TR (BHE, Net etc.)"):
        log_play_to_set((f"{st.session_state.opp} Error TR (BHE, Net etc.)", "+"))


    if st.button(f"{st.session_state.opp} TR Kill"):
        log_play_to_set((f"{st.session_state.opp} TR Kill", "-"))
    if st.button(f"{st.session_state.opp} Stuff Block TR"):
        log_play_to_set((f"{st.session_state.opp} Stuff Block TR", "-"))
    if st.button("UConn Hitting Error TR"):
        log_play_to_set(("UConn Hitting Error TR", "-"))
    if st.button("UConn Error TR (BHE, Net etc.)"):
        log_play_to_set(("UConn Error TR (BHE, Net etc.)", "-"))

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

triangle_by_sets = triangle_by_set()
st.dataframe(triangle_by_sets)

triangle_pcts = triangle_percentage_by_set()
st.dataframe(triangle_pcts)


if st.button("End of game, export data to email"):
    export_to_excel()



