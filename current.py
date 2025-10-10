import streamlit as st
from datetime import datetime
import pandas as pd

# --- INITIALIZE SESSION STATE ---
def initiate_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "sets" not in st.session_state:
        st.session_state.sets = {i: [] for i in range(1, 6)}  # play logs per set
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

# --- ROTATION RECONSTRUCTION LOGIC ---
def compute_rotations_for_set(set_num):
    plays = st.session_state.sets[set_num]
    our_rot = st.session_state.set_data[set_num]["our_starting_rotation"]
    opp_rot = st.session_state.set_data[set_num]["opp_starting_rotation"]
    serve_team = st.session_state.set_data[set_num]["starting_serve"]

    rotation_states = []
    last_serve_team = serve_team

    for play_result, sign, *_ in plays:
        rotation_states.append((our_rot, opp_rot))

        if last_serve_team == "UConn":
            if sign == "-":  # lost serve
                opp_rot = (opp_rot % 6) + 1
                last_serve_team = st.session_state.opp
        else:
            if sign == "+":  # won serve
                our_rot = (our_rot % 6) + 1
                last_serve_team = "UConn"

    return rotation_states

# --- LOGGING FUNCTION ---
def log_play_to_set(play_result, sign):
    current_set = st.session_state.set
    set_info = st.session_state.set_data[current_set]

    if sign == "+":
        if set_info["starting_serve"] == "UConn":
            set_info["our_score"] += 1
        else:
            set_info["opp_score"] += 1
    elif sign == "-":
        if set_info["starting_serve"] == "UConn":
            set_info["opp_score"] += 1
            set_info["starting_serve"] = st.session_state.opp
        else:
            set_info["our_score"] += 1
            set_info["starting_serve"] = "UConn"

    # Append play without rotations; they'll be reconstructed later
    st.session_state.sets[current_set].append((play_result, sign, datetime.now(), set_info["our_score"], set_info["opp_score"]))

# --- UNDO FUNCTION ---
def undo_previous_play():
    current_set = st.session_state.set
    if st.session_state.sets[current_set]:
        st.session_state.sets[current_set].pop()
        st.session_state.set_data[current_set]["our_score"] = 0
        st.session_state.set_data[current_set]["opp_score"] = 0

        # Replay all remaining plays to rebuild score
        serve_team = st.session_state.set_data[current_set]["starting_serve"]
        for play_result, sign, *_ in st.session_state.sets[current_set]:
            if sign == "+":
                if serve_team == "UConn":
                    st.session_state.set_data[current_set]["our_score"] += 1
                else:
                    st.session_state.set_data[current_set]["opp_score"] += 1
            elif sign == "-":
                if serve_team == "UConn":
                    st.session_state.set_data[current_set]["opp_score"] += 1
                    serve_team = st.session_state.opp
                else:
                    st.session_state.set_data[current_set]["our_score"] += 1
                    serve_team = "UConn"
    else:
        st.warning("No plays to undo.")

# --- DISPLAY PLAY LOG ---
def display_data():
    current_set = st.session_state.set
    plays = st.session_state.sets[current_set]
    if not plays:
        st.info("No plays logged yet.")
        return

    rotation_states = compute_rotations_for_set(current_set)
    df = pd.DataFrame(plays, columns=["Play", "Sign", "Timestamp", "Our Score", "Opp Score"])
    df["Our Rotation"], df["Opp Rotation"] = zip(*rotation_states)
    st.dataframe(df)

# --- MAIN APP ---
def main():
    st.title("Volleyball Triangle Tracker (Option B - Replay from Play Log)")
    initiate_session()

    col1, col2, col3, col4 = st.columns(4)

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

    # play_result = st.text_input("Play result (e.g., FB Kill, TRS Error)")
    # sign = st.radio("Result Sign", ["+", "-"])

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
    st.subheader(f"Set {st.session_state.set} Play Log")
    display_data()

if __name__ == "__main__":
    main()
