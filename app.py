from flask import Flask, render_template, request, session
from bs4 import BeautifulSoup
from datetime import date
import random
import requests

# my files
from db import get_fact, save_fact, init_db

app = Flask(__name__)
init_db()


@app.route('/on_submit', methods=['POST'])
def on_submit():
    getFacts()
    return '', 204

# get 4 facts
def getFacts():
    # facts = [
    #     ("Paris", "Capital of France"),
    #     ("Berlin", "Capital of Germany"),
    #     ("London", "Capital of UK"),
    #     ("Madrid", "Capital of Spain"),
    # ]
    
    correct = GetRandomFact(GetInfoFromDay(getDate()))
    choices = []
    
    choices.append(correct)
    
    # 3 random facts from random days that arent cur day
    choices.append(GetRandomFact(GetInfoFromDay(GetRandomDay(getDate()))))
    choices.append(GetRandomFact(GetInfoFromDay(GetRandomDay(getDate()))))
    choices.append(GetRandomFact(GetInfoFromDay(GetRandomDay(getDate()))))

    random.shuffle(choices)
    return choices, correct

def getDate():    
    return date.today().day, date.today().month


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
    
    if not facts:
        # Return a default value or an error message if no facts are found
        return "No facts found for this date.", day
    # returns one item from list of pairs
    # the returned thing is <fact,date>
    return random.choice(facts), day
  
# Show one question at a time using getFacts
@app.route("/", methods=["GET", "POST"])
def quiz():
    result = None
    if request.method == "POST":
        user = request.form.get("answer")
        correct = request.form.get("correct_answer")
        result= user == correct
        
        # print("User:", repr(user))
        # print("Correct:", repr(correct))
        # print("Equal?", user == correct)
        print(result)
    
    
    choices, correct = getFacts()
    date = str(getDate()[1]) + "/" + str(getDate()[0])
    question_text = "What happened on " + date + ""
    options = [pair[0] for pair in choices]
    
    return render_template(
        "quiz.html",
        title="quiz",
        quiz_title="quiz",
        question={
            'question_text': question_text,
            'options': options,
            'correct_answer': correct[0]
        },
        result=result
    )

if __name__ == "__main__":
    # starts website
    app.run(host='0.0.0.0')
    #GetInfoFromDay(getDate())
    
    #loads all days
    # for m in range(1,13):
    #     for d in range(1,32):
    #         day_tuple = (d, m)
    #         GetInfoFromDay(day_tuple)
    #         print(str(m) + "/" + str(d))