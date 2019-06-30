import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///stories.db")


@app.route("/")
def home():
    # TODO
    return render_template("home.html")

@app.route("/create", methods=['GET', 'POST'])
@login_required
def create():
    if request.method == "POST":

        if not request.form.get('storyname'):
            return apology("must enter storyname", 400)

        if not request.form.get('storygenre'):
            return apology("must enter genre", 400)

        storyname = request.form.get('storyname')
        genre = request.form.get('storygenre')
        creator = db.execute("SELECT username FROM users WHERE id=:userid", userid=session['user_id'])
        creator = creator[0]['username']
        
        #testduplicates
        testerduplicates = db.execute("SELECT * FROM stories WHERE userid=:userid AND storyname=:storyname", userid=session['user_id'], storyname=storyname)
        if len(testerduplicates) != 0:
            return apology("Story already exists by this user and with this name!", 400)
        
        db.execute("INSERT into stories (storyname, userid, genre, username) VALUES (:storyname, :userid, :genre, :username)", storyname=storyname, userid=session['user_id'], genre=genre, username=creator)
        storyid = db.execute("SELECT storyid FROM stories WHERE storyname=:storyname AND userid=:userid", storyname=storyname, userid=session['user_id'])
        storyid = storyid[0]["storyid"]
        db.execute("INSERT into storycards (storyid, cardname, cardtype, cardtext) VALUES (:storyid, 'start', 'start', 'Placeholder_Text')", storyid=storyid)
        return render_template("create.html")
    else:
        return render_template("create.html")

@app.route("/edit", methods=['GET', 'POST'])
@login_required
def edit():

    if request.method == "POST":
        if not request.form.get('stories'):
            return apology('no story found', 400)

        storyname = request.form.get('stories')
        storyid = db.execute("SELECT storyid FROM stories WHERE storyname=:storyname AND userid=:userid", storyname=storyname, userid=session['user_id'])
        storyid = storyid[0]["storyid"]
        requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)

        cards = db.execute("SELECT cardname, cardtext FROM storycards WHERE storyid=:storyid AND cardtype=:cardtype", storyid=storyid, cardtype='start')
        cardtext = cards[0]["cardtext"]
        cardname = cards[0]["cardname"]
        
        description = db.execute("SELECT desc FROM stories WHERE storyid=:storyid", storyid=storyid)
        description = description[0]["desc"]        

        counter, children = getchildren(storyid, cardname)

        return render_template("editor.html", carddesc=description, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)

    else:
        userstories = db.execute("SELECT storyname FROM stories WHERE userid=:userid", userid=session['user_id'])
        return render_template("edit.html", userstories=userstories)

@app.route("/editor", methods=['GET', 'POST'])
@login_required
def editor():
    
    carddesc = request.form["carddesc"]
    
    if request.form["submit"] == "0" or request.form["submit"] == "1" or request.form["submit"] == "2" or request.form["submit"] == "3" or request.form["submit"] == "4":

        n = request.form["submit"]

        nextcard = request.form[n]

        currentcard = request.form["cardname"]
        cardtext = request.form["editedtext"]
        storyid = request.form["storyid"]
        storyname = request.form["storyname"]
        carddesc = request.form["carddesc"]
        
        requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)
        cards = db.execute("SELECT cardname, cardtext FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=nextcard)

        if len(cards) == 0:
            return apology("Card not found", 400)

        cardtext = cards[0]["cardtext"]
        cardname = cards[0]["cardname"]

        counter, children = getchildren(storyid, nextcard)

        return render_template("editor.html", carddesc=carddesc, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)


    if request.form["submit"] == 'Save':



        currentcard = request.form["cardname"]
        cardtext = request.form["editedtext"]
        storyid = request.form["storyid"]
        storyname = request.form["storyname"]



        db.execute("UPDATE storycards SET cardtext = :cardtext WHERE storyid = :storyid AND cardname = :cardname", cardtext=cardtext, storyid=storyid, cardname=currentcard)
        requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)

        counter, children = getchildren(storyid, currentcard)

        return render_template("editor.html", carddesc=carddesc, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=currentcard, storyid=storyid, counter=counter, children=children)


    if request.form["submit"] == 'Go':

        currentcard = request.form["cardname"]
        cardtext = request.form["editedtext"]
        storyid = request.form["storyid"]
        storyname = request.form["storyname"]


        # VIEW DIFFERENT CARD
        if not request.form.get('action'):
            return apology('no action selected', 400)

        if request.form.get('action') == '0':

            if not request.form.get('card'):
                return apology('no card selected', 400)

            nextcard = request.form.get('card')

            requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)
            cards = db.execute("SELECT cardname, cardtext FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=nextcard)
            cardtext = cards[0]["cardtext"]
            cardname = cards[0]["cardname"]

            counter, children = getchildren(storyid, nextcard)

            return render_template("editor.html", carddesc=carddesc, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)

        # DELETE
        if request.form.get('action') == '1':

            if not request.form.get('card'):
                return apology('no card selected', 400)

            tobedeletedcard = request.form.get('card')

            prevcard = db.execute("SELECT parent FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=tobedeletedcard)
            previouscard = prevcard[0]["parent"]


            if previouscard == 'NULL':
                return apology('cannot delete parent', 400)

            parentcard = db.execute("SELECT child1, child2, child3, child4, child5 FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=previouscard)
            if parentcard[0]['child1'] == tobedeletedcard:
                db.execute("UPDATE storycards SET child1 = :kill WHERE storyid=:storyid AND cardname=:cardname", kill=None, storyid=storyid, cardname=previouscard)
            elif parentcard[0]['child2'] == tobedeletedcard:
                db.execute("UPDATE storycards SET child2 = :kill WHERE storyid=:storyid AND cardname=:cardname", kill=None, storyid=storyid, cardname=previouscard)
            elif parentcard[0]['child3'] == tobedeletedcard:
                db.execute("UPDATE storycards SET child3 = :kill WHERE storyid=:storyid AND cardname=:cardname", kill=None, storyid=storyid, cardname=previouscard)
            elif parentcard[0]['child4'] == tobedeletedcard:
                db.execute("UPDATE storycards SET child4 = :kill WHERE storyid=:storyid AND cardname=:cardname", kill=None, storyid=storyid, cardname=previouscard)
            elif parentcard[0]['child5'] == tobedeletedcard:
                db.execute("UPDATE storycards SET child5 = :kill WHERE storyid=:storyid AND cardname=:cardname", kill=None, storyid=storyid, cardname=previouscard)

            db.execute("DELETE FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=tobedeletedcard)

            cards = db.execute("SELECT cardtext, cardname FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=previouscard)
            cardtext = cards[0]["cardtext"]
            cardname = cards[0]["cardname"]
            requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)

            counter, children = getchildren(storyid, previouscard)

            return render_template("editor.html", carddesc=carddesc, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)

        # RENAME
        if request.form.get('action') == '2':

            if not request.form.get('card'):
                return apology('no card selected', 400)

            toberenamedcard = request.form.get('card')
            newcardname = request.form.get('renameto')
            db.execute("UPDATE storycards SET parent = :newcardname WHERE storyid=:storyid AND parent = :toberenamedcard", newcardname=newcardname, storyid=storyid, toberenamedcard=toberenamedcard)
            db.execute("UPDATE storycards SET cardname = :newcardname WHERE storyid=:storyid AND cardname=:cardname", newcardname=newcardname,storyid=storyid, cardname=toberenamedcard)
            db.execute("UPDATE storycards SET child1 = :newcardname WHERE storyid=:storyid AND child1=:toberenamedcard", storyid=storyid, newcardname=newcardname, toberenamedcard=toberenamedcard)
            db.execute("UPDATE storycards SET child2 = :newcardname WHERE storyid=:storyid AND child2=:toberenamedcard", storyid=storyid, newcardname=newcardname, toberenamedcard=toberenamedcard)
            db.execute("UPDATE storycards SET child3 = :newcardname WHERE storyid=:storyid AND child3=:toberenamedcard", storyid=storyid, newcardname=newcardname, toberenamedcard=toberenamedcard)
            db.execute("UPDATE storycards SET child4 = :newcardname WHERE storyid=:storyid AND child4=:toberenamedcard", storyid=storyid, newcardname=newcardname, toberenamedcard=toberenamedcard)
            db.execute("UPDATE storycards SET child5 = :newcardname WHERE storyid=:storyid AND child5=:toberenamedcard", storyid=storyid, newcardname=newcardname, toberenamedcard=toberenamedcard)
                                                            
            cards = db.execute("SELECT cardtext, cardname FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=newcardname)
            cardtext = cards[0]["cardtext"]
            cardname = cards[0]["cardname"]
            requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)

            counter, children = getchildren(storyid, currentcard)

            return render_template("editor.html", carddesc=carddesc, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)

        # CREATE
        if request.form.get('action') == '3':

            if not request.form.get('childofcard'):
                return apology('no card selected', 400)

            if not request.form.get('namenewcard'):
                return apology('Must give a name to your new card!', 400)

            parent = request.form.get('childofcard')
            newcardname = request.form.get('namenewcard')

            duplicatetester = db.execute("SELECT * FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=newcardname)

            if len(duplicatetester) > 0:
                return apology('A card with this name already exists in this story.', 400)

            counter, children = getchildren(storyid, parent)

            if counter >= 5:
                return apology('this card has max number of children(5)', 400)

            # amend the parent card to add child
            parentcard = db.execute("SELECT child1, child2, child3, child4, child5 FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=parent)
            if parentcard[0]['child1'] == None:
                db.execute("UPDATE storycards SET child1 = :newcardname WHERE storyid=:storyid AND cardname=:cardname", newcardname=newcardname, storyid=storyid, cardname=parent)
            elif parentcard[0]['child2'] == None:
                db.execute("UPDATE storycards SET child2 = :newcardname WHERE storyid=:storyid AND cardname=:cardname", newcardname=newcardname, storyid=storyid, cardname=parent)
            elif parentcard[0]['child3'] == None:
                db.execute("UPDATE storycards SET child3 = :newcardname WHERE storyid=:storyid AND cardname=:cardname", newcardname=newcardname, storyid=storyid, cardname=parent)
            elif parentcard[0]['child4'] == None:
                db.execute("UPDATE storycards SET child4 = :newcardname WHERE storyid=:storyid AND cardname=:cardname", newcardname=newcardname, storyid=storyid, cardname=parent)
            elif parentcard[0]['child5'] == None:
                db.execute("UPDATE storycards SET child5 = :newcardname WHERE storyid=:storyid AND cardname=:cardname", newcardname=newcardname, storyid=storyid, cardname=parent)

            #insert new record
            db.execute("INSERT INTO storycards (storyid, cardname, cardtype, parent, cardtext) VALUES (:storyid, :newcardname, 'child', :parent, 'Placeholder_Text')", storyid=storyid, newcardname=newcardname, parent=parent)

            cards = db.execute("SELECT cardtext, cardname FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=newcardname)
            cardtext = cards[0]["cardtext"]
            cardname = cards[0]["cardname"]
            requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)
            counter, children = getchildren(storyid, newcardname)
            return render_template("editor.html", carddesc=carddesc, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, children=children, counter=counter)

      # description change
        if request.form.get('action') == '4':

            if not request.form.get('changedesc'):
                return apology('no description inputted', 400)

            tobechangeddesc = request.form.get('carddesc')
            newdesc = request.form.get('changedesc')
            cardname= request.form.get('cardname')

            db.execute("UPDATE stories SET desc = :newdesc WHERE storyid=:storyid", storyid=storyid, newdesc=newdesc)

            cards = db.execute("SELECT cardtext, cardname FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=cardname)
            cardtext = cards[0]["cardtext"]
            cardname = cards[0]["cardname"]
            description = db.execute("SELECT desc FROM stories WHERE storyid=:storyid", storyid=storyid)
            description = description[0]["desc"]
            requestedstory = db.execute("SELECT * FROM storycards WHERE storyid=:storyid", storyid=storyid)

            counter, children = getchildren(storyid, currentcard)

            return render_template("editor.html", carddesc=description, requestedstory=requestedstory, storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)


    card = request.form.get("card")
    return render_template("editor.html")


@app.route("/browse")
def browse():
    # if request.method =="GET":
    adventure = db.execute("SELECT * FROM stories WHERE genre = 'Adventure'")
    comedy = db.execute("SELECT * FROM stories WHERE genre = 'Comedy'")
    drama = db.execute("SELECT * FROM stories WHERE genre = 'Drama'")
    romance = db.execute("SELECT * FROM stories WHERE genre = 'Romance'")
    other = db.execute("SELECT * FROM stories WHERE genre = 'Other'")

    return render_template("browse.html", adventure=adventure, comedy=comedy, drama=drama, romance=romance, other=other)

@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method =="POST":
        searchquery = request.form["query"]
        searchmethod = request.form["searchtype"]
        
        searchquery = "%" + searchquery + "%"
        
        if searchmethod == "name":
            results = db.execute("SELECT storyname, username, desc, genre FROM stories WHERE storyname LIKE :s", s=searchquery)
            return render_template("search.html", searchresults=results)

        if searchmethod == "desc":
            results = db.execute("SELECT storyname, username, desc, genre FROM stories WHERE desc LIKE :s", s=searchquery)
            return render_template("search.html", searchresults=results)
            
    stories = db.execute("SELECT storyname, username, desc, genre FROM stories")
    return render_template("search.html", searchresults=stories)

@app.route("/viewer", methods=["POST", "GET"])
def viewer():
    
    if request.form['FROM'] == "BROWSER":

    
        storyname = request.form["storybutton"]
        author = request.form["storyauthor"]

        print(storyname + author)    
        storyid = db.execute("SELECT storyid FROM stories WHERE storyname=:storyname AND username=:username", storyname=storyname, username=author)
        storyid = storyid[0]["storyid"]
        cardname = db.execute("SELECT cardname from storycards WHERE storyid=:storyid AND cardtype='start'", storyid=storyid)
        cardname = cardname[0]["cardname"]
        
        counter, children = getchildren(storyid, cardname)
        
        cards = db.execute("SELECT cardname, cardtext FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=cardname)
        cardtext = cards[0]["cardtext"]
    
        counter, children = getchildren(storyid, cardname)
    
        return render_template("viewer.html", storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)
    
    else:     
        if request.form["submit"] == "0" or request.form["submit"] == "1" or request.form["submit"] == "2" or request.form["submit"] == "3" or request.form["submit"] == "4":

            n = request.form["submit"]
    
            nextcard = request.form[n]
    
            currentcard = request.form["cardname"]
            cardtext = request.form["cardtext"]
            storyid = request.form["storyid"]
            storyname = request.form["storyname"]
    
            cards = db.execute("SELECT cardname, cardtext FROM storycards WHERE storyid=:storyid AND cardname=:cardname", storyid=storyid, cardname=nextcard)
    
            if len(cards) == 0:
                return apology("Card not found", 400)
    
            cardtext = cards[0]["cardtext"]
            cardname = cards[0]["cardname"]
    
            counter, children = getchildren(storyid, cardname)
    
            return render_template("viewer.html", storyname=storyname, cardtext=cardtext, cardname=cardname, storyid=storyid, counter=counter, children=children)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must re-enter password", 400)

        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords do not match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) == 1:
            return apology("username exists!", 400)

        # hash the password
        passwordhashed = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                   username=request.form.get("username"), hash=passwordhashed)

        # Remember which user has logged in
        # session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/check", methods=["GET"])
def check():

    username = request.args.get("username")

    names = db.execute("SELECT username FROM users")
    for row in names:
        if username == row['username']:
            return jsonify(False)
    return jsonify(True)

@app.route("/checkduplicatestoryname", methods=["GET"])
def checkduplicatestoryname():

    storyname = request.args.get("storyname")
    userid = session["user_id"]

    names = db.execute("SELECT storyname FROM stories WHERE userid=:userid", userid=userid)
    for row in names:
        if storyname == row['storyname']:
            return jsonify(False)
    return jsonify(True)
    
@app.route("/checkduplicatecardname", methods=["GET"])
def checkduplicatecardname():

    cardname = request.args.get("cardname")
    storyid = request.args.get("storyid")

    names = db.execute("SELECT cardname FROM storycards WHERE storyid=:storyid", storyid=storyid)
    for row in names:
        if cardname == row['cardname']:
            return jsonify(False)
    return jsonify(True)
    
def listoptions(storyid, cardname):
    # purpose is to put the children of a card in a list
    storyid = storyid
    cardname = cardname
    childlisttemp = db.execute("SELECT child1, child2, child3, child4, child5 FROM storycards WHERE storyid = :storyid AND cardname=:cardname", storyid=storyid, cardname=cardname)
    childlist = [];
    for n in range(1, 5):
        if childlisttemp[n] != 'NULL':
            childlist[n] = childlisttemp[n]
    return(childlist)

def getchildren(storyid, cardname):
    storyid = storyid
    cardname = cardname
    counter = 0
    childlisttemp = db.execute("SELECT child1, child2, child3, child4, child5 FROM storycards WHERE storyid = :storyid AND cardname=:cardname", storyid=storyid, cardname=cardname)
    childlist = []
    
    print(storyid)
    
    print(cardname)
    
    print(childlisttemp)
    
    if not childlisttemp:
        return (0, childlist)
    
    if childlisttemp[0]['child1'] != None:
        counter += 1;
        childlist.append(childlisttemp[0]['child1'])

    if childlisttemp[0]['child2'] != None:
        counter += 1;
        childlist.append(childlisttemp[0]['child2'])

    if childlisttemp[0]['child3'] != None:
        counter += 1;
        childlist.append(childlisttemp[0]['child3'])

    if childlisttemp[0]['child4'] != None:
        counter += 1;
        childlist.append(childlisttemp[0]['child4'])

    if childlisttemp[0]['child5'] != None:
        counter += 1;
        childlist.append(childlisttemp[0]['child5'])

    return (counter, childlist)

