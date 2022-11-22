from bs4 import BeautifulSoup as bs
import requests
import json
import numpy as np

# class for scraping fight stats
class UFC_FIGHT():
    def __init__(self, fight_path, fight_location, fight_date):
        self.fight_path = fight_path
        self.fight_location = fight_location
        self.fight_date = fight_date
        self.fight_soup = bs(requests.get(self.fight_path).content, "lxml")
        self.header_fight_winner = ['WINNER']
        self.header_fight_infos = ['BOUT','WIN_METHOD', 'LAST_ROUND', 'LAST_ROUND_TIME', 'ROUNDS', 'REFEREE']
        self.headers_fight_tables = ['FIGHTER_R', 'FIGHTER_B', 'KD_R', 'KD_B', 
                                        'SIG_STR_R', 'SIG_STR_ATT_R', 'SIG_STR_B', 'SIG_STR_ATT_B',
                                        'TOTAL_STR_R', 'TOTAL_STR_ATT_R', 'TOTAL_STR_B', 'TOTAL_STR_ATT_B',
                                        'TAKEDOWN_R', 'TAKEDOWN_ATT_R','TAKEDOWN_B', 'TAKEDOWN_ATT_B', 
                                        'SUB_ATT_R', 'SUB_ATT_B', 'REV_R', 'REV_B', 'CTRL_R', 'CTRL_B', 
                                        'STR_HEAD_R', 'STR_HEAD_ATT_R', 'STR_HEAD_B', 'STR_HEAD_ATT_B',
                                        'STR_BODY_R', 'STR_BODY_ATT_R', 'STR_BODY_B', 'STR_BODY_ATT_B',
                                        'STR_LEG_R', 'STR_LEG_ATT_R', 'STR_LEG_B', 'STR_LEG_ATT_B',
                                        'DISTANCE_R', 'DISTANCE_ATT_R', 'DISTANCE_B', 'DISTANCE_ATT_B',
                                        'CLINCH_R', 'CLINCH_ATT_R', 'CLINCH_B', 'CLINCH_ATT_B',
                                        'GROUND_R', 'GROUND_ATT_R', 'GROUND_B', 'GROUND_ATT_B', 
                                        'LOCATION', 'DATE']
 
        self.headers_all = self.header_fight_winner + self.header_fight_infos + self.headers_fight_tables

    def get_winner(self):
        results = self.fight_soup.select('.b-fight-details__person-status')
        red = results[0].get_text(strip=True)
        blue = results[1].get_text(strip=True)
        winner = []
        if red == "W" and blue=="L":
            winner.append("red")
        elif red == "L" and blue=="W":
            winner.append("blue")
        else:
            winner.append("draw/NC")
        return winner
    
    def get_fight_infos(self):
        bout = self.fight_soup.find("div", class_="b-fight-details__fight-head").get_text(strip=True)
        infos = [bout]

        for i in self.fight_soup.find("p", class_="b-fight-details__text"):
            info = i.get_text(strip=True)
            if info != '':
                if len(info.split(":")) == 3:
                    x = (info.split(":")[-2] + ":" + info.split(":")[-1])
                else:
                    x = info.split(":")[-1]
                infos.append(x)
        return infos


    def get_fight_tables(self):        
        headers = self.fight_soup.find_all("thead", class_="b-fight-details__table-head")
        bodies_all = self.fight_soup.find_all("tbody",class_="b-fight-details__table-body")
        indices = [0,-2] # Get only tables with total stats (not on round basis)
        bodies_totals = [bodies_all[i] for i in indices]

        columns_names = []
        column_values = []
        
        for head,body in zip(headers,bodies_totals):
            if head is not None:
                for i in head.find_all("th", class_="b-fight-details__table-col"):
                    columns_names.append(i.get_text(strip=True))

            values = body.find_all("td", class_="b-fight-details__table-col")
            if len(values) <= 10:
                for value in values:
                    column_values.append(value)

        column_name_val_filter = []

        for i,u in zip(columns_names, column_values):
            if '%' not in i:
                i = i.split(" ")[0]
                val = i,u
                if val not in column_name_val_filter:
                    column_name_val_filter.append(val)                                            

        values = []
        for i in column_name_val_filter:
            tag = i[1].find_all("p")
            for content in tag:
                text = content.get_text(strip=True)
                if 'of' in text: 
                    text_split = [item for item in text.split(" ") if not 'of' in item]
                    for i in text_split:
                        values.append(i)
                else:
                    values.append(text)  
        # in case of missing values on the website
        values = [v.replace('---', '') for v in values]
        # append the attribute values passed by the UFC_LINK class
        values.append(self.fight_location)
        values.append(self.fight_date)
        return values
    
    # Executes all previously defined instance methods
    def get_fight_all(self):
        stats = {}
        try:
            values = self.get_winner() + self.get_fight_infos() + self.get_fight_tables()
            for k,v in zip(self.headers_all, values):
                stats[f"{k}"] = v
            return stats
        except:
            print('no fight stats')


# Class for scraping all necessary links and infos
# location and date of the fight are available only on the parent pages, so they get collected along with the links
class UFC_LINKS():
    def __init__(self, main_page):
        self.main_page = main_page
        self.link_soup = bs(requests.get(self.main_page).content, "lxml")
        self.event_links = []
        self.event_locations = []
        self.event_date = []
        self.fight_locations = []
        self.fight_links = []
        self.fight_date = []
        self.fighter_links = []
        
        
    # "n" = index event_row: to limit the number of links. If not defined, all are collected
    def get_event_links(self, n=None):
        self.event_links.clear()
        self.event_locations.clear()
        self.event_date.clear()
        events = self.link_soup.find_all("tr", class_="b-statistics__table-row")[1:n]
    # get event link and event location to later join to the main output
        for event in events:
            try:
                self.event_links.append(event.select(".b-link.b-link_style_black")[0]['href'])
                self.event_locations.append(event.select(".b-statistics__table-col.b-statistics__table-col_style_big-top-padding")[0].get_text(strip=True))
                self.event_date.append(event.select(".b-statistics__date")[0].get_text(strip=True))
            except:
                pass

    def get_fight_n_fighter_links(self):
        self.fight_links.clear()
        self.fighter_links.clear()
        
        for event_link, event_location, event_date in zip(self.event_links, self.event_locations, self.event_date):
            r = requests.get(event_link)
            soup = bs(r.content, "lxml")
            fights = soup.find_all("tr", class_="b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click")
            for fight in fights:
                self.fight_links.append(fight['data-link'])
                self.fight_locations.append(event_location)
                self.fight_date.append(event_date)
                for fighter in fight.find_all("a", class_='b-link b-link_style_black'):
                    if fighter['href'] not in self.fighter_links:
                        self.fighter_links.append(fighter['href'])

    @staticmethod
    def save_items(filepath, data):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    def save_links(self):
        event_links = {}
        fight_links = {}
        fighter_links = {}

        # save event links, with the location of the event
        if len(self.event_links) != 0:
            for n,i,j,u in zip(np.arange(len(self.event_links)), self.event_links, self.event_locations, self.event_date):
                event_links[str(n)] = [i,j,u]         
            
            self.save_items('../links/event_links.json', event_links)
       
        # save fight links, with the location of the event
        if len(self.fight_links) != 0:    
            for n,i,j,u in zip(np.arange(len(self.fight_links)), self.fight_links, self.fight_locations, self.fight_date):
                fight_links[str(n)] = [i,j,u]
            
            self.save_items('../links/fight_links.json', fight_links)

        # save fighter links
        if len(self.fighter_links) != 0: 
            for n,i in zip(np.arange(len(self.fighter_links)), self.fighter_links):
                fighter_links[str(n)] = i
            
            self.save_items('../links/fighter_links.json', fighter_links)


# class for scraping fighter stats
class UFC_FIGHTER():
    def __init__(self, fighter_path):
        self.fighter_path = fighter_path
        self.fighter_soup = bs(requests.get(self.fighter_path).content, "lxml")
        self.headers_fighter_infos = ["NAME","RECORD","HEIGHT", "WEIGHT", "REACH", "STANCE", "DOB", 
                                        "SIG_STR_L_PM", "SIG_STR_ACC", "SIG_STR_ABS_PM", "SIG_STR_DEF", 
                                        "AVG_TAKEDOWN_15_MIN", "TAKEDOWN_ACC", "TAKEDOWN_DEF", "AVG_SUB_ATT_15_MIN"]

    def get_fighter_infos(self):       
        fighter_values = self.fighter_soup.select(".b-list__box-list-item.b-list__box-list-item_type_block")
        fighter_name  = self.fighter_soup.find("span", class_="b-content__title-highlight").get_text(strip=True)
        fighter_record = self.fighter_soup.find("span", class_="b-content__title-record").get_text(strip=True)

        values = [fighter_name, fighter_record]

        for value in fighter_values:
            try:
                values.append(value.get_text(strip=True).split(":")[1])
            except:
                pass
        
        fighter_stats = {}
        for k,v in zip(self.headers_fighter_infos, values):
            fighter_stats[f"{k}"] = v
        
        return fighter_stats