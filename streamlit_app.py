# 10/2/25
# add starting rotation buttons
# add rotation logic so only have to press 1 button at the beginning of each set


import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from util import send_email_with_attachment
import os
import openpyxl
from io import BytesIO


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
                "our_starting_rotation": 1,
                "opp_starting_rotation": 1,
                "starting_serve": "UConn",
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
    if "game_date" not in st.session_state:
        st.session_state.game_date = datetime.today()
    



def compute_rotations_for_set(set_num):
    plays = st.session_state.sets[set_num]
    our_rot = st.session_state.set_data[set_num]["our_starting_rotation"]
    opp_rot = st.session_state.set_data[set_num]["opp_starting_rotation"]
    serve_team = st.session_state.set_data[set_num]["starting_serve"]

    rotation_states = []
    current_server = serve_team  # Track who is serving during the rally

    for play_result, sign, *_ in plays:
        # Record rotations *during* this rally
        rotation_states.append((our_rot, opp_rot))

        # Determine who serves next rally
        if current_server == "UConn":
            if sign == "-":  # we lost serve
                opp_rot = (opp_rot % 6) + 1  # they rotate
                current_server = st.session_state.opp
            # if we win (+), nothing changes
        else:  # opponent was serving
            if sign == "+":  # we won while receiving
                our_rot = (our_rot % 6) + 1  # we rotate
                current_server = "UConn"
            # if they win (-), nothing changes

    return rotation_states



    



def undo_previous_play():
    try:
        current_set = st.session_state.set
        set_info = st.session_state.set_data[current_set]

        if not st.session_state.sets[current_set]:
            st.write("Can't undo previous play, no plays have been made")
            return

        undone_play = st.session_state.sets[current_set].pop()
        play_result, sign, our_score, opp_score, our_rot, opp_rot = undone_play


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
                set_info["stats"][stat] = max(0, set_info["stats"][stat] - 1)

        if not st.session_state.sets[current_set]:
            set_info["our_score"] = 0
            set_info["opp_score"] = 0
            # you can also reset serve tracking if you store one
            # e.g., set_info["starting_serve"] = None


        st.success(f"Undid play: {play_result}")
    except Exception as e:
        st.write(f"Error undoing play: {e}")


def log_play_to_set(play_result, sign):
    current_set = st.session_state.set
    set_info = st.session_state.set_data[current_set]

    # --- Update stats (unchanged) ---
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

    # --- Update score ---
    if sign == "+":
        set_info["our_score"] += 1
    elif sign == "-":
        set_info["opp_score"] += 1

    # --- Determine rotations correctly ---
    plays = st.session_state.sets[current_set]
    set_start_serve = set_info["starting_serve"]

    if not plays:
        # First rally of set
        our_rot = set_info["our_starting_rotation"]
        opp_rot = set_info["opp_starting_rotation"]

    else:
        # Get last play info
        _, last_sign, _, _, last_our_rot, last_opp_rot = plays[-1]
        last_server = set_start_serve
        # reconstruct who was serving before this play
        for p in plays[:-1]:
            _, s, *_ = p
            if last_server == "UConn":
                if s == "-":  # lost serve
                    last_server = st.session_state.opp
            else:
                if s == "+":  # won serve while receiving
                    last_server = "UConn"

        our_rot, opp_rot = last_our_rot, last_opp_rot

        # Determine if serve switched after last rally
        if last_server == "UConn" and last_sign == "-":
            # Opponent gained serve → they rotate
            opp_rot = (opp_rot % 6) + 1
            last_server = st.session_state.opp
        elif last_server == st.session_state.opp and last_sign == "+":
            # UConn gained serve → we rotate
            our_rot = (our_rot % 6) + 1
            last_server = "UConn"
        # Otherwise, rotations stay same

    # --- Record the play with the *current* rotation state ---
    expanded_play = (
        play_result,
        sign,
        set_info["our_score"],
        set_info["opp_score"],
        our_rot,
        opp_rot
    )

    st.session_state.sets[current_set].append(expanded_play)





# Determine current rotations by reconstructing from previous plays
    



    

 
def export_to_excel():
    # When end of game button is clicked, saves all data and sends it out as an excel file
    os.makedirs("data", exist_ok=True)

    filename = f"data/UConn vs {st.session_state.opp} - {st.session_state.game_date} Triangle Stats.xlsx"

    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        any_data_written = False

        # add set logs
        for i, set_data in st.session_state.sets.items():
            if set_data:
                df = pd.DataFrame(set_data, columns=["Play Result", "Triangle +/-", "UConn", st.session_state.opp])
                df.to_excel(writer, sheet_name=f"Set {i} Log", index=False)
                any_data_written = True

        if not any_data_written:
            pd.DataFrame({'Message': ["No data recorded"]}).to_excel(writer, sheet_name="Summary", index=False)
        else:
            triangle_by_set().to_excel(writer, sheet_name="Triangle Stats")
            triangle_percentage_by_set().to_excel(writer, sheet_name="Triangle Percentages")
            triangle_by_rotation().to_excel(writer, sheet_name="Triangle by Rotation")
            triangle_percentage_by_rotation().to_excel(writer, sheet_name="Triangle Rotation Percentages")
            overall_game_stats().to_excel(writer, sheet_name="Overall Game Stats")        

    send_excel_emails(filename)

def send_excel_emails(file):
    try:
        send_email_with_attachment(
                        sender_email='owenbabiec@gmail.com',
                        sender_password="wmxdajqjjexvopxh",
                        # recipients=['owen.babiec@uconn.edu', 'peter.netisingha@uconn.edu', 'mdt23007@uconn.edu'],
                        recipients=['owen.babiec@uconn.edu'],
                        subject=f"UConn vs {st.session_state.opp} - {st.session_state.game_date} Triangle Stats",
                        body=f"Here's the excel files for this game",
                        attachments=[file]
                        )
        st.success("Emails sent successfully")
    except Exception as e:
        st.warning(f"Error sending email: {e}")

def display_data():
    current_set = st.session_state.set

    plays = st.session_state.sets[current_set]
    if not plays:
        st.info("No plays logged yet")
        return
    
    rotation_states = compute_rotations_for_set(current_set)
    df = pd.DataFrame(
        plays,
        columns=[
            "Play Result",
            "+/-",
            "UConn Score",
            f"{st.session_state.opp} Score",
            "Our Rot",
            f"{st.session_state.opp} Rot"
        ]
    )
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

def triangle_by_rotation():
    # Groups together all plays into one dataframe
    all_plays = []
    for set_num, plays in st.session_state.sets.items():
        for play in plays:
            play_result, sign, our_score, opp_score, our_rot, opp_rot = play
            all_plays.append({
                "Set": set_num,
                "Play": play_result,
                "Sign": sign,
                "OurRot": our_rot,
                "OppRot": opp_rot
            })
    
    if not all_plays:
        return pd.DataFrame([{"Message": "No plays recorded"}])

    df = pd.DataFrame(all_plays)

    # Map plays to triangle categories and values
    df["TS"] = 0
    df["FB"] = 0
    df["TRS"] = 0

    ts_plays = ["UConn Ace", "UConn SE", f"{st.session_state.opp} Ace", f"{st.session_state.opp} SE"]
    fb_plays = ["UConn FB Kill", "UConn Stuff Block FB", "UConn Hitting Error FB",
                "UConn Error FB (BHE, Net etc.)", f"{st.session_state.opp} FB Kill",
                f"{st.session_state.opp} Stuff Block FB", f"{st.session_state.opp} Hitting Error FB",
                f"{st.session_state.opp} Error FB (BHE, Net etc.)"]
    tr_plays = ["UConn TR Kill", "UConn Stuff Block TR", "UConn Hitting Error TR",
                "UConn Error TR (BHE, Net etc.)", f"{st.session_state.opp} TR Kill",
                f"{st.session_state.opp} Stuff Block TR", f"{st.session_state.opp} Hitting Error TR",
                f"{st.session_state.opp} Error TR (BHE, Net etc.)"]

    # Assign +/- depending on play
    for i, row in df.iterrows():

        # terminal serve plays
        if row["Play"] in ts_plays:
            if row["Play"] in ["UConn Ace", f"{st.session_state.opp} SE"]:
                df.at[i, "TS"] = +1
            else:
                df.at[i, "TS"] = -1

        # first ball plays
        elif row["Play"] in fb_plays:
            if "UConn" in row["Play"]:
                if "Kill" in row["Play"] or "Stuff" in row["Play"]: 
                    df.at[i, "FB"] = +1
                else:
                    df.at[i, "FB"] = -1 # errors
            else:
                if "Kill" in row["Play"] or "Stuff" in row["Play"]:
                    df.at[i, "FB"] = -1
                else:
                    df.at[i, "FB"] = +1 # their errors

        # transition plays
        elif row["Play"] in tr_plays:
            if "UConn" in row["Play"]:
                if "Kill" in row["Play"] or "Stuff" in row["Play"]:
                    df.at[i, "TRS"] = +1
                else:
                    df.at[i, "TRS"] = -1
            else:
                if "Kill" in row["Play"] or "Stuff" in row["Play"]:
                    df.at[i, "TRS"] = -1
                else:
                    df.at[i, "TRS"] = +1

    # Group by rotation
    grouped = df.groupby("OurRot").agg({
        "TS": "sum",
        "FB": "sum",
        "TRS": "sum"
    }).reset_index()

    grouped.rename(columns={"OurRot": "UConn Rotation", "TS": "Terminal Serve"}, inplace=True)

    return grouped

def triangle_percentage_by_rotation():
    # Group all plays together into one df
    all_plays = []
    for set_num, plays in st.session_state.sets.items():
        for play in plays:
            play_result, sign, our_score, opp_score, our_rot, opp_rot = play
            all_plays.append({
                "Set": set_num,
                "Play": play_result,
                "Sign": sign,
                "OurRot": our_rot,
                "OppRot": opp_rot
            })
    
    if not all_plays:
        return pd.DataFrame([{"Message": "No plays recorded"}])

    # creating separate counter df
    df = pd.DataFrame(all_plays)

    # Initialize counters
    df["TS_win"] = 0
    df["TS_total"] = 0
    df["FB_win"] = 0
    df["FB_total"] = 0
    df["TRS_win"] = 0
    df["TRS_total"] = 0

    # Define categories
    ts_plays = ["UConn Ace", "UConn SE", f"{st.session_state.opp} Ace", f"{st.session_state.opp} SE"]
    fb_plays = ["UConn FB Kill", "UConn Stuff Block FB", "UConn Hitting Error FB",
                "UConn Error FB (BHE, Net etc.)", f"{st.session_state.opp} FB Kill",
                f"{st.session_state.opp} Stuff Block FB", f"{st.session_state.opp} Hitting Error FB",
                f"{st.session_state.opp} Error FB (BHE, Net etc.)"]
    tr_plays = ["UConn TR Kill", "UConn Stuff Block TR", "UConn Hitting Error TR",
                "UConn Error TR (BHE, Net etc.)", f"{st.session_state.opp} TR Kill",
                f"{st.session_state.opp} Stuff Block TR", f"{st.session_state.opp} Hitting Error TR",
                f"{st.session_state.opp} Error TR (BHE, Net etc.)"]

    # Tag each row
    for i, row in df.iterrows():
        play = row["Play"]

        # Terminal Serve
        if play in ts_plays:
            df.at[i, "TS_total"] = 1
            if play in ["UConn Ace", f"{st.session_state.opp} SE"]:
                df.at[i, "TS_win"] = 1

        # First Ball
        elif play in fb_plays:
            df.at[i, "FB_total"] = 1
            if "UConn" in play and ("Kill" in play or "Stuff" in play):
                df.at[i, "FB_win"] = 1
            elif f"{st.session_state.opp}" in play and ("Error" in play or "Hitting Error" in play):
                df.at[i, "FB_win"] = 1

        # Transition
        elif play in tr_plays:
            df.at[i, "TRS_total"] = 1
            if "UConn" in play and ("Kill" in play or "Stuff" in play):
                df.at[i, "TRS_win"] = 1
            elif f"{st.session_state.opp}" in play and ("Error" in play or "Hitting Error" in play):
                df.at[i, "TRS_win"] = 1

    # Aggregate by rotation
    grouped = df.groupby("OurRot").agg({
        "TS_win": "sum", "TS_total": "sum",
        "FB_win": "sum", "FB_total": "sum",
        "TRS_win": "sum", "TRS_total": "sum"
    }).reset_index()

    # Calculate percentages
    grouped["Serve %"] = (grouped["TS_win"] / grouped["TS_total"] * 100).round(1).fillna(0)
    grouped["FB %"] = (grouped["FB_win"] / grouped["FB_total"] * 100).round(1).fillna(0)
    grouped["TRS %"] = (grouped["TRS_win"] / grouped["TRS_total"] * 100).round(1).fillna(0)

    # Keep only clean columns
    result = grouped[["OurRot", "Serve %", "FB %", "TRS %"]].rename(columns={"OurRot": "UConn Rotation"})

    return result



# Streamlit UI
st.title("UConn Volleyball Stat Tracker")
initiate_session()

st.session_state.game_date = st.date_input("Game date:")
st.session_state.opp = st.text_input("Opponent:", value=st.session_state.opp)

col1, col2, col3, col4 = st.columns(4)

# Start of set information
with col1:
        st.session_state.set = st.radio("Select Set", [1, 2, 3, 4, 5], index=st.session_state.set - 1)
with col2:
    st.session_state.set_data[st.session_state.set]["our_starting_rotation"] = st.radio(
        "UConn Starting Rotation", [1, 2, 3, 4, 5, 6]
    )
with col3:
    st.session_state.set_data[st.session_state.set]["opp_starting_rotation"] = st.radio(
        f"{st.session_state.opp} Starting Rotation", [1, 2, 3, 4, 5, 6]
    )
with col4:
    st.session_state.set_data[st.session_state.set]["starting_serve"] = st.radio(
        "Team that starts with serve", ["UConn", st.session_state.opp]
    )

st.write("---")

# Layout for stat tracking
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("Terminal Serve")
    if st.button("UConn Ace", type="primary"):
        log_play_to_set("UConn Ace", "+")
    if st.button("UConn SE", type="primary"):
        log_play_to_set("UConn SE", "-")
    if st.button(f"{st.session_state.opp} Ace"):
        log_play_to_set(f"{st.session_state.opp} Ace", "-")
    if st.button(f"{st.session_state.opp} SE"):
        log_play_to_set(f"{st.session_state.opp} SE", "+")

with col2:
    st.subheader("First Ball")
    if st.button("UConn FB Kill", type="primary"):
        log_play_to_set("UConn FB Kill", "+")
    if st.button("UConn Stuff Block FB", type="primary"):
        log_play_to_set("UConn Stuff Block FB", "+")
    if st.button("UConn Hitting Error FB", type="primary"):
        log_play_to_set("UConn Hitting Error FB", "-")
    if st.button("UConn Error FB (BHE, Net etc.)", type="primary"):
        log_play_to_set("UConn Error FB (BHE, Net etc.)", "-")
    if st.button(f"{st.session_state.opp} FB Kill"):
        log_play_to_set(f"{st.session_state.opp} FB Kill", "-")
    if st.button(f"{st.session_state.opp} Stuff Block FB"):
        log_play_to_set(f"{st.session_state.opp} Stuff Block FB", "-")
    if st.button(f"{st.session_state.opp} Hitting Error FB"):
        log_play_to_set(f"{st.session_state.opp} Hitting Error FB", "+")
    if st.button(f"{st.session_state.opp} Error FB (BHE, Net etc.)"):
        log_play_to_set(f"{st.session_state.opp} Error FB (BHE, Net etc.)", "+")
    

with col3:
    st.subheader("Transition")
    if st.button("UConn TR Kill", type="primary"):
        log_play_to_set("UConn TR Kill", "+")
    if st.button("UConn Stuff Block TR", type="primary"):
        log_play_to_set("UConn Stuff Block TR", "+")
    if st.button("UConn Hitting Error TR", type="primary"):
        log_play_to_set("UConn Hitting Error TR", "-")
    if st.button("UConn Error TR (BHE, Net etc.)", type="primary"):
        log_play_to_set("UConn Error TR (BHE, Net etc.)", "-")
    if st.button(f"{st.session_state.opp} TR Kill"):
        log_play_to_set(f"{st.session_state.opp} TR Kill", "-")
    if st.button(f"{st.session_state.opp} Stuff Block TR"):
        log_play_to_set(f"{st.session_state.opp} Stuff Block TR", "-")
    if st.button(f"{st.session_state.opp} Hitting Error TR"):
        log_play_to_set(f"{st.session_state.opp} Hitting Error TR", "+")
    if st.button(f"{st.session_state.opp} Error TR (BHE, Net etc.)"):
        log_play_to_set(f"{st.session_state.opp} Error TR (BHE, Net etc.)", "+")
    

with col4:
    st.subheader("Other Actions")
    if st.button("Award Point to UConn", type="primary"):
        log_play_to_set(f"Award Point to UConn", "+")
    if st.button(f"Award Point to {st.session_state.opp}"):
        log_play_to_set(f"Award Point to {st.session_state.opp}", "-")

    if st.button("Undo previous play"):
        undo_previous_play()

st.write("---")

# Displays set log, triangle per set and overall game triangle
st.subheader(f"Set {st.session_state.set} Play Log")
display_data()

triangle_by_sets = triangle_by_set()
st.subheader("Triangle Stats")
st.dataframe(triangle_by_sets)

triangle_pcts = triangle_percentage_by_set()
st.subheader("Triangle Percentages")
st.dataframe(triangle_pcts)

triangle_rot = triangle_by_rotation()
st.subheader("Triangle by UConn Rotation")
st.dataframe(triangle_rot)

triangle_pct_rot = triangle_percentage_by_rotation()
st.subheader("Triangle Percentages by UConn Rotation")
st.dataframe(triangle_pct_rot)



if st.button("End of game, export data to email"):
    export_to_excel()



