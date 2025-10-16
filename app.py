from flask import Flask, render_template, request, session
from bs4 import BeautifulSoup
from datetime import date
import random
import requests

import os
from dotenv import load_dotenv

# my files
from db import get_fact, save_fact, init_db

app = Flask(__name__)
load_dotenv()
app.secret_key = os.environ.get('SECRET_KEY')
init_db()

currentDate = date.today().day, date.today().month
correctAnswer = ""

@app.route("/api")
def api():
    return "Hello, Vercel!"

@app.route('/on_submit', methods=['POST'])
def on_submit():
    getFacts()
    return '', 204

def getFacts():
    correct = getFactFromToday()
    choices = []
    
    choices.append(correct)
    
    # 3 random facts from random days that arent cur day
    choices.append(getFactNotFromToday())
    choices.append(getFactNotFromToday())
    choices.append(getFactNotFromToday())

    random.shuffle(choices)
    
    # finds right index after shuffle
    correct_index = next(i for i, choice in enumerate(choices) if choice[0] == correct[0])
    session['correct_answer_index'] = correct_index
    
    return choices

@app.route("/getFactFromToday", methods=['POST'])
def getFactFromTodayRoute():
    return GetRandomFact(GetInfoFromDay(getDate()))

def getFactFromToday():
    result = GetRandomFact(GetInfoFromDay(getDate()))
    while not result or not result[0] or result[0].startswith("No facts"):
        print(f"Invalid fact for today, retrying...")
        result = GetRandomFact(GetInfoFromDay(GetRandomDay(getDate())))
    return result

@app.route("/getFactNotFromToday", methods=['POST'])
def getFactNotFromTodayRoute():
    return GetRandomFact(GetInfoFromDay(GetRandomDay(getDate())))

def getFactNotFromToday():
    result = GetRandomFact(GetInfoFromDay(GetRandomDay(getDate())))
    while not result or not result[0] or result[0].startswith("No facts"):
        print(f"Invalid fact, retrying...")
        result = GetRandomFact(GetInfoFromDay(GetRandomDay(getDate())))
    return result

@app.route("/checkAnswer", methods=['POST'])
def checkAnswer():
    userAnswer = request.form.get("answer")
    correctAnswer = session.get('correct_answer')
    return str(userAnswer == correctAnswer)

@app.route("/getDate", methods=['POST'])
def getDateRoute():
    global currentDate
    return str(currentDate)

def getDate():
    global currentDate
    return currentDate

@app.route("/change_date", methods=['POST'])
def changeDate():
    global currentDate
    day = int(request.form.get("days", currentDate[0]))
    month = int(request.form.get("months", currentDate[1]))
    # defaults day and month to currentDate
    currentDate = day, month
    print(currentDate)
    return '', 204
    
# end of wrapper functions

def GetRandomDay(cur):
    # retuns a day != cur
    month = random.randint(1,12)
    day = random.randint(1,31)
    
    # picks a new day until day doesnt match
    while(day == cur[0] and month == cur[1]):
        month = random.randint(1,12)
        day = random.randint(1,31)
        
        # keeps day in bound
        if(month == 2 and day > 28):
            day = 28
        if((month == 4 or month == 6 or month == 9 or month == 11) and day > 30 ):
            day = 30
    
    return day, month
    
def GetInfoFromDay(day):
    # checks if day is already recorded
    day_str = f"{day[0]}/{day[1]}" 
    db_facts = get_fact(day_str)
    if db_facts is not None:
        return db_facts, day
    
    # returns list of info from day
    # returns day
    info = []
    months = {
        1: "january",
        2: "february",
        3: "march",
        4: "april",
        5: "may",
        6: "june",
        7: "july",
        8: "august",
        9: "september",
        10: "october",
        11: "november",
        12: "december"
    }
    # goes to random day on website
    website = "https://www.onthisday.com/events/" + str(months[day[1]]) + "/" + str(day[0])
    # events / birthdays / deaths / weddings
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}
    # gets code from website
    response = requests.get(website, headers=headers)
    #print(response.status_code)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    #print(soup.prettify())
    
    # grabs all "event" classes and all <p> in ".grid" class
    
    # grab plain txt
    events = soup.find_all('li', class_='event')
    for item in events:
        txt = item.get_text(strip=True)
        
        # adds space between year and text
        spaces = 0
        for index, char in enumerate(txt):
            if spaces == 4:
                break
            elif char.isdigit():
                spaces += 1
            elif txt[index+1] == 'B' and txt[index+2] == 'C':
                spaces += 3
                break
            else:
                break
            
        txt = txt[:spaces] + " " + txt[spaces:]            
        info.append(txt)
        #print(txt)  
        
        
    # grabs the big boxes
    grids = soup.find_all('div', class_='section--poi')
    
    if grids:
        for grid_item in grids:
            p = grid_item.find('p')
            
            if p:
                parts = list(p.children)
                formatted = []
                
                for part in parts:
                    if hasattr(part, 'get_text'):
                        formatted.append(part.get_text(strip=True))
                    else:
                        text_part = part.strip()
                        if text_part:
                            formatted.append(text_part)
                
                txt = ' '.join(formatted)
                info.append(txt)
                #print(txt)
    # stores info
    info_str = "\n".join(info)
    save_fact(day_str, info_str)
    return info, day
    
def GetRandomFact(input):
    facts = input[0]
    day = input[1]
    
    if not facts or len(facts) == 0:
        # if today is bad ten pick another random day
        print(f"No facts found for {day[0]}/{day[1]}, trying different day...")
        return GetRandomFact(GetInfoFromDay(GetRandomDay(day)))
    return random.choice(facts), day
  
# Show one question at a time using getFacts
@app.route("/", methods=["GET", "POST"])
def quiz():
    global currentDate
    
    months = ["", "January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    
    # GET request - new question
    choices = getFacts()
    options = [pair[0] for pair in choices]
    options_dates = [f"{months[pair[1][1]]} {pair[1][0]}" for pair in choices]
    
    current_date_str = f"{months[currentDate[1]]} {currentDate[0]}"
    correct_answer_index = session.get('correct_answer_index')
    
    return render_template(
        "quiz.html",
        options=options,
        options_dates=options_dates,
        correct_answer_index=correct_answer_index,
        current_date=current_date_str,
        current_month=currentDate[1],
        current_day=currentDate[0]
    )

if __name__ == "__main__":
    # starts website
    app.run(host='0.0.0.0', debug=False)