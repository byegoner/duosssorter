import pandas as pd
import random
import streamlit as st
import math

members_1 = pd.Series(['Seoyeon', 'Jiwoo', 'Chaeyeon', 'Yooyeon', 'Nakyoung', 'Yubin', 'Kaede', 'Dahyun', 'Kotone', 'Nien', 'Sohyun', 'Xinyu', 'Mayu', 'Jiyeon'], index=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
members_2 = pd.Series(['Seoyeon', 'Jiwoo', 'Chaeyeon', 'Yooyeon', 'Nakyoung', 'Yubin', 'Kaede', 'Dahyun', 'Kotone', 'Nien', 'Sohyun', 'Xinyu', 'Mayu', 'Jiyeon'], index=[0, 1, 2, 3, 4, 5, 6, 7, 8 ,9, 10, 11, 12, 13])

all_ships_init = []

#Creating all possible pairing options
for i in range(len(members_1)):
    for j in range(len(members_2)):
        if j != i:
            if j > i:
                all_ships_init += [(members_1[i]+","+members_2[j]).lower()]
            elif j < i:
                continue
        elif j == i:
            continue

@st.cache_resource
def get_ship_data():
    ships = {}
    for i in range(len(all_ships_init)):
        ships[f"ship{i+1}"] = all_ships_init[i]
    return ships

ships = get_ship_data()

# Round and ranking functions adapted from:
# https://github.com/pradigunara/sssongs/blob/b4c6eb3c0759f5d8f314a407181899b1c7285608/src/roundCalculator.js
# https://github.com/pradigunara/sssongs/blob/b4c6eb3c0759f5d8f314a407181899b1c7285608/src/songSorter.js

def calculate_rounds_1(ships_count):
    total_rounds = (ships_count * (ships_count-1))/2
    rounds_full_coverage = math.ceil(total_rounds/3)
    min_appearances_ship = 4 #Makes sure that each option appears at least 4 times
    total_appearances = ships_count*min_appearances_ship
    rounds_appearances = math.ceil(total_appearances/3)
    base_rounds = max(rounds_full_coverage, rounds_appearances)
    return math.ceil(base_rounds/5)*5

def calculate_rounds_hybrid(total_ships):
    min_appearances_ship = 3 #Makes sure that each option appears at least 3 times during the hybrid rounds
    min_total_appearances = total_ships*min_appearances_ship
    phase_1_rounds = math.ceil(min_total_appearances/3)
    phase_1_rounds_rounded = math.ceil(phase_1_rounds/5)*5
    phase_1_survivors = math.ceil(total_ships*0.5)
    final_ships = 16
    phase_2_rounds  = math.ceil((phase_1_survivors * 1.2)/3)
    phase_2_rounds_rounded = math.ceil(phase_2_rounds/5)*5
    phase_3_rounds = calculate_rounds_1(final_ships)
    return{
        "phase1": {
            "rounds": phase_1_rounds_rounded,
            "description": "phase 1",
            "survivors": phase_1_survivors,
            "min_appearances": min_appearances_ship
        },
        "phase2": {
            "rounds": phase_2_rounds_rounded,
            "description": "phase 2",
            "survivors": final_ships,
            "elimination_threshold": math.ceil(phase_2_rounds_rounded * 0.3)
        },
        "phase3": {
            "rounds": phase_3_rounds,
            "description": "phase 3",
            "survivors": "top rankings"
        },
        "totalRounds": phase_1_rounds_rounded + phase_2_rounds_rounded + phase_3_rounds,
        "phases": 3
    }

def get_current_phase(current_round, config):
    p1 = config["phase1"]["rounds"]
    p2 = config["phase2"]["rounds"]
    p3 = config["phase3"]["rounds"]

    if current_round <= p1:
        return {
            "phase": 1,
            "phaseRound": current_round,
            "maxPhaseRounds": p1,
            "description": config["phase1"]["description"],
            "type": "discovery"
        }
    elif current_round <= p1 + p2:
        return {
            "phase": 2,
            "phaseRound": current_round - p1,
            "maxPhaseRounds": p2,
            "description": config["phase2"]["description"],
            "type": "elimination"
        }
    else:
        return {
            "phase": 3,
            "phaseRound": current_round - p1 - p2,
            "maxPhaseRounds": p3,
            "description": config["phase3"]["description"],
            "type": "head-to-head"
        }

class shipsorter:
    def __init__(self, ships_dict):
        self.ships = [
            {
                "name": ship_name,
                "score": 0,
                "appearances": 0,
                "eliminated": False,
                "h2hScore": 0,
                "h2hWins": 0,
                "h2hLosses": 0,
                "h2hMatches": 0
            }
            for ship_name in ships_dict.values()
        ]

        self.current_round = 0
        self.history = []
        self.system_config = calculate_rounds_hybrid(len(ships_dict))
        self.total_rounds = self.system_config["totalRounds"]
        self.current_options = []

    def get_current_phase_info(self):
        return get_current_phase(self.current_round + 1, self.system_config)

    def select_three_ships(self):
        available = [s for s in self.ships if not s["eliminated"]]
        if len(available) < 3:
            self.current_options = available
        else:
            self.current_options = random.sample(available, 3)

        for ship in self.current_options:
            ship["appearances"] += 1
        return self.current_options

    def record_winner(self, winner_name):

        winner = next((s for s in self.current_options if s["name"] == winner_name), None)
        if not winner:
            return

        phase_info = self.get_current_phase_info()

        if phase_info["phase"] == 3:
            for ship in self.current_options:
                ship["h2hMatches"] += 1
                if ship["name"] == winner_name:
                    ship["h2hWins"] += 2
                    ship["h2hScore"] += 1
                else:
                    ship["h2hLosses"] += 1
        else:
            winner["score"] += 1

        self.history.append({
            "round": self.current_round + 1,
            "options": [s["name"] for s in self.current_options],
            "winner": winner_name
        })

        self.current_round += 1
        self.check_elimination()

    def check_elimination(self):
        phase_info = self.get_current_phase_info()

        if phase_info["phaseRound"] == phase_info["maxPhaseRounds"]:
            if phase_info["phase"] == 1:
                for s in self.ships:
                    if s["score"] <= 0:
                        s["eliminated"] = True
            elif phase_info["phase"] == 2:
                survivors = sorted(
                    [s for s in self.ships if not s["eliminated"]],
                    key=lambda x: x["score"],
                    reverse=True
                )
                keep_count = self.system_config["phase2"]["survivors"]
                for i, ship in enumerate(survivors):
                    if i >= keep_count:
                        ship["eliminated"] = True

                for s in self.ships:
                    s["h2hScore"] = s["h2hWins"] = s["h2hLosses"] = s["h2hMatches"] = 0

    def get_rankings(self):
        phase = self.get_current_phase_info()["phase"]
        active_ships = [s for s in self.ships if not s["eliminated"]]

        if phase == 3:
            def sort_key(s):
                win_pct = s["h2hWins"] / s["h2hMatches"] if s["h2hMatches"] > 0 else 0
                return -win_pct, -s["h2hMatches"], -s["score"]
        else:
            def sort_key(s):
                return -s["score"]

        return sorted(active_ships, key=sort_key)

    def is_done(self):
        return self.current_round >= self.total_rounds

#Image paths
ships_data= pd.Series(["./image/s1s3.webp","./image/s1s4.webp",
"./image/s1s5.webp",
 "./image/s1s7.webp",
 "./image/s1s8.webp",
 "./image/s1s9.webp",
 "./image/s1s10wav_chan.jpeg",
 "./image/s1s11.jpeg",
 "./image/s1s13.webp",
 "./image/s1s14.webp",
 "./image/s1s15pumpkin030806.jpeg",
 "./image/s1s16.webp",
 "./image/s1s24.webp",
 "./image/s3s4.webp",
 "./image/s3s5.webp",
 "./image/s3s7.webp",
 "./image/s3s8.webp",
 "./image/s3s9chkchk.webp",
 "./image/s3s10.jpeg",
 "./image/s3s11topclass.jpeg",
 "./image/s3s13.jpeg",
 "./image/s3s14.jpeg",
 "./image/s3s15.png",
 "./image/s3s16ourl512o.jpeg",
 "./image/s3s24axharrrrr.jpeg",
 "./image/s4s5.jpeg",
 "./image/s4s7.webp",
 "./image/s4s8.webp",
 "./image/s4s9.jpeg",
 "./image/s4s10.jpeg",
 "./image/s4s11kotoneverdie.jpeg",
 "./image/s4s13.jpeg",
 "./image/s4s14.jpeg",
 "./image/s4s15.jpeg",
 "./image/s4s16.webp",
 "./image/s4s24.jpeg",
 "./image/s5s7.jpeg",
 "./image/s5s8.webp",
 "./image/s5s9kaede_acernus.jpeg",
 "./image/s5s10sodaruno.jpeg",
 "./image/s5s11.jpeg",
 "./image/s5s13a_honeynien.jpeg",
 "./image/s5s14.jpeg",
 "./image/s5s15mo4sheng1.jpeg",
 "./image/s5s16.jpeg",
 "./image/s5s24wavv57.jpeg",
 "./image/s7s8.webp",
 "./image/s7s9.webp",
 "./image/s7s10.webp",
 "./image/s7s11.jpeg",
 "./image/s7s13.webp",
 "./image/s7s14.jpeg",
 "./image/s7s15ssszxy.jpeg",
 "./image/s7s160sp346.jpeg",
 "./image/s7s24.jpeg",
 "./image/s8s9.jpeg",
 "./image/s8s10.jpeg",
 "./image/s8s11.jpeg",
 "./image/s8s13.webp",
 "./image/s8s14sohyunnabi14.jpeg",
 "./image/s8s15.jpeg",
 "./image/s8s16.webp",
 "./image/s8s24.jpeg",
 "./image/s9s10.jpeg",
 "./image/s9s11.webp",
 "./image/s9s13.jpeg",
 "./image/s9s14.jpeg",
 "./image/s9s15kconjapan.jpeg",
 "./image/s9s16.webp",
 "./image/s9s24kflow3onsite.jpeg",
 "./image/s10s11sunriseseoah.jpeg",
 "./image/s10s13.jpeg",
 "./image/s10s14atiu_atr.jpeg",
 "./image/s10s15wordofmyheart02.jpeg",
 "./image/s10s16.jpeg",
 "./image/s10s24refrain0213.png",
 "./image/s11s13.webp",
 "./image/s11s14.webp",
 "./image/s11s15-kttto11.jpeg",
 "./image/s11s16.webp",
 "./image/s11s24.webp",
 "./image/s13s14.jpg",
 "./image/s13s15.jpeg",
 "./image/s13s16wavchichi.jpeg",
 "./image/s13s240602_nien.jpeg",
 "./image/s14s15.jpg",
 "./image/s14s16.jpeg",
 "./image/s14s24.jpeg",
 "./image/s15s16.jpeg",
 "./image/s15s24.jpeg",
 "./image/s16s24.jpeg"], index=[all_ships_init])

#If photo is not from official content (fansites mostly) source will be provided upon hovering the button
def add_cap(x):
    if x == "seoyeon,dahyun":
        return("wav_chan")
    elif x == "seoyeon,xinyu":
        return("pumpkin030806")
    elif x == "jiwoo,kaede":
        return("chkchk magazine")
    elif x == "jiwoo,kotone":
        return("topclass magazine")
    elif x == "jiwoo,mayu":
        return("ourl512o")
    elif x == "jiwoo,jiyeon":
        return("axharrrrr")
    elif x == "chaeyeon,kotone":
        return("kotoneverdie")
    elif x == "yooyeon,kaede":
        return("kaede_acernus")
    elif x == "yooyeon,dahyun":
        return("sodaruno")
    elif x == "yooyeon,nien":
        return("a_honeynien")
    elif x == "yooyeon,xinyu":
        return("mo4sheng1")
    elif x == "yooyeon,jiyeon":
        return("wavv57")
    elif x == "nakyoung,xinyu":
        return("ssszxy")
    elif x == "nakyoung,mayu":
        return("0sp346")
    elif x == "yubin,dahyun":
        return("happyvirus_s8")
    elif x == "yubin,sohyun":
        return("sohyunnabi14")
    elif x == "yubin,xinyu" or x == "dahyun,sohyun":
        return("atiu_atr")
    elif x == "kaede,xinyu":
        return("kcon japan")
    elif x == "kaede,jiyeon":
        return("kflow3 onsite")
    elif x == "dahyun,kotone":
        return("sunriseseoah")
    elif x == "dahyun,xinyu":
        return("wordofmyheart02")
    elif x == "dahyun,mayu":
        return("nme the cover")
    elif x == "dahyun,jiyeon":
        return("refrain0213")
    elif x == "kotone,xinyu":
        return("kttto11")
    elif x == "nien,mayu":
        return("wavchichi")
    elif x == "nien,jiyeon":
        return("0602_nien")
    else:
        return("")

if "sorter" not in st.session_state:
    st.session_state.sorter = shipsorter(ships)

if "selected" not in st.session_state:
    st.session_state.selected = False

def selected_click(ship_name):
    st.session_state.selected = ship_name

sorter = st.session_state.sorter

st.header("duosssorter")
st.markdown(
    ":blue-badge[05z+ only] :blue-badge[better on desktop] :blue-badge[adapted from [@celdaris](https://x.com/celdaris)]"
)

#Mobile-friendly checkbox
on = st.checkbox("images on/off (mobile)", value=True)

#Actual app/executions of functions
if not sorter.is_done():
    if st.session_state.selected:
        selected_ship = st.session_state.selected
        sorter.record_winner(selected_ship)
        st.session_state.selected = False

    phase_info = sorter.get_current_phase_info()
    #st.write(sorter.total_rounds) <-- Uncomment to check how adjustments to the ranking system impact round number

    #Progress bar
    progress = (sorter.current_round + 1) / sorter.total_rounds
    if sorter.current_round < sorter.total_rounds:
        st.progress(progress)
    elif sorter.current_round-1 >= sorter.total_rounds:
        ""

    #Grabbing three pairings and populating image/button options into 3 containers
    current_ships = sorter.select_three_ships()
    cols = st.columns(3)

    for i, col in enumerate(cols):
        ship = current_ships[i]
        with col:
            with st.container(border=True):
                ship_display = ship["name"].replace(",", " ♡ ")
                if on:
                    st.image(ships_data[ship["name"]])
                st.button(f"{ship_display}", key=f"btn_{i}", use_container_width=True,
                          help=add_cap(ship["name"]),
                          on_click=selected_click,
                          kwargs={"ship_name": ship["name"]})

    st.caption("for best results shuffle for neither/none")

    #Shuffle button
    col1, col2, col3 = st.columns([1, 1, 2.32])
    with col3:
        options = ["↺"]
        if st.pills("", options):
            current_ships = sorter.select_three_ships()

#Showing top 10 rankings with image attachment for number one
else:
    st.subheader("top 10", divider = "blue")
    rankings = sorter.get_rankings()
    for idx, ship in enumerate(rankings[:10], 1):
        if idx <2:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.image(ships_data[ship['name']], width = 200, caption = add_cap(ship["name"]))
        st.write(f"{idx}. {ship['name'].replace(',', ' ♡ ')}")
