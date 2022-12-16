#Import Flask Library
from ast import keyword
from email import message
from lib2to3.pgen2.tokenize import untokenize
from turtle import title
from typing import Set
from flask import Flask, render_template, request, session, url_for, redirect, flash
import pymysql.cursors

import bcrypt
import os

#for uploading photo:
from app import app
#from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename

import datetime

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


###Initialize the app from Flask
##app = Flask(__name__)
##app.secret_key = "secret key"

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='FlaskDemo',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE userName=%s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        try:
            passwordBytes = password.encode('utf-8')
            hashed = data['password'].encode('utf-8')
            if bcrypt.checkpw(passwordBytes, hashed):
                #creates a session for the the user
                #session is a built in
                session['username'] = username
                return redirect(url_for('home'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)
        except ValueError:
            error = 'Invalid password'
            return render_template('login.html', error=error)
    else:
        #returns an error message to the html page
        error = 'Invalid username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    profile = request.form['profile']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        try:
            passwordBytes = password.encode('utf-8')
            hashedPassword = bcrypt.hashpw(passwordBytes, bcrypt.gensalt())

            #print(f'hashedPassword={hashedPassword}')
            ins = 'INSERT INTO PERSON (`userName`, `password`, `fName`, `lName`, `email`, `profile`) VALUES(%s, %s, %s, %s, %s, %s)'
            cursor.execute(ins, (username, hashedPassword, fname, lname, email, profile)) #add HASH password here
            conn.commit()
            cursor.close()
            return render_template('index.html')
        except:
            error = "Registering user error"
            return render_template('register.html', error = error)


@app.route('/home')
def home():
    error = request.args.get('error')
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, (user))
    data = cursor.fetchall()

    messages = []
    results = {}
    query = 'SELECT recipeID, title, postedBy FROM Recipe ORDER BY RAND() LIMIT 5'
    cursor.execute(query)
    results = cursor.fetchall()

    if len(results) == 0:
        messages.append("No recipe found!")

    cursor.close()
    return render_template('home.html', username=user, posts=data, messages=messages, results=results, error=error)

@app.route('/recipe_info', methods=['GET', 'POST'])
def recipe_info():
    recipeID = request.args.get('recipeID')
    ingredients = request.args.getlist('ingredients')
    steps = request.args.getlist('steps')
    tags = request.args.getlist('tags')
    pictures = request.args.getlist('pictures')
    revPics = request.args.getlist('revPics')
    title = request.args.get('title')
    numServings = request.args.get('numServings')
    author = request.args.get('author')
    revTitle = request.args.get('revTitle')
    revDesc = request.args.get('revDesc')
    stars = request.args.get('stars')

    return render_template('recipe_info.html', title=title, numServings=numServings, author=author, \
        recipeID=recipeID, ingredients=ingredients, steps=steps, tags=tags, pictures=pictures, revTitle=revTitle, revDesc=revDesc, \
        stars=stars, revPics=revPics)

@app.route('/recipe')
def recipe():
    try:
        cursor = conn.cursor();
        query = 'SELECT unitName FROM Unit'
        cursor.execute(query)
        unit_names = cursor.fetchall()
        units = []
        for unit in unit_names:
            units.append(unit['unitName'])
        cursor.close()
        return render_template('recipe.html', units=units)
    except:
        return redirect(url_for('home', error='Recipe error!'))

@app.route('/recipeAdd', methods=['GET', 'POST'])
def recipeAdd():
    try:
        title = request.form['title']
        numServings = request.form['numServings']
        ingredients = {
            "name": [],
            "amount": [],
            "unit": [],
            "link": []
        }
        steps = []
        tags = []
        related_recipes = []
        pictures = []

        for i, a, u, l in zip(request.form.getlist('ingredient'),
                        request.form.getlist('amount'),
                        request.form.getlist('unit'),
                        request.form.getlist('link')):
            ingredients['name'].append(i)
            ingredients['amount'].append(a)
            ingredients['unit'].append(u)
            ingredients['link'].append(l)
        for s in zip(request.form.getlist('step')):
            steps.append(s[0])
        for t in zip(request.form.getlist('tag')):
            tags.append(t[0])
        for r in zip(request.form.getlist('relatedRecipe')):
            related_recipes.append(r[0])
        for p in zip(request.form.getlist('picture')):
            pictures.append(p[0])
        
        #print(f'title={title}')
        #print(f'numServings={numServings}')
        #print(f'ingredients={ingredients}')
        #print(f'steps={steps}')
        #print(f'tags={tags}')
        #print(f'related_recipes={related_recipes}')

        username = session['username']
        cursor = conn.cursor()
        conn.begin()
        query = 'INSERT INTO Recipe (title, numServings, postedBy) VALUES (%s, %s, %s)'
        cursor.execute(query, (title, numServings, username))
        query = 'SELECT MAX(recipeID) FROM Recipe WHERE title=%s AND numServings=%s AND postedBy=%s'
        cursor.execute(query, (title, numServings, username))
        recipeID = cursor.fetchone()["MAX(recipeID)"]
        #conn.commit()

        step_num = 1
        for step in steps:
            query = 'INSERT INTO Step (stepNo, recipeID, sDesc) VALUES (%s, %s, %s)'
            cursor.execute(query, (step_num, recipeID, step))
            #conn.commit()
            step_num += 1

        for tag in tags:
            query = 'INSERT INTO RecipeTag (recipeID, tagText) VALUES (%s, %s)'
            cursor.execute(query, (recipeID, tag))
            #conn.commit()

        for related_recipe in related_recipes:
            query = 'INSERT INTO RelatedRecipe (recipe1, recipe2) VALUES (%s, %s)'
            cursor.execute(query, (recipeID, related_recipe))
            #conn.commit()

        for picture in pictures:
            query = 'INSERT INTO RecipePicture (recipeID, pictureURL) VALUES (%s, %s)'
            cursor.execute(query, (recipeID, picture))
            #conn.commit()
        
        ingredients_note = []
        for idx in range(len(ingredients['name'])):
            ingredients_note.append(f"{ingredients['name'][idx]} {ingredients['amount'][idx]}{ingredients['unit'][idx]}")
            query = 'SELECT iName FROM Ingredient WHERE iName=%s'
            cursor.execute(query, (ingredients['name'][idx],))
            if cursor.fetchone() is None:
                query = 'INSERT INTO Ingredient (iName, purchaseLink) VALUES (%s, %s)'
                cursor.execute(query, (ingredients['name'][idx], ingredients['link'][idx]))
            query = 'INSERT INTO RecipeIngredient (recipeID, iName, unitName, amount) VALUES (%s, %s, %s, %s)'
            cursor.execute(query, (recipeID, ingredients['name'][idx], ingredients['unit'][idx], ingredients['amount'][idx]))
        conn.commit()
        
        cursor.close()
        return redirect(url_for('recipe_info', title=title, numServings=numServings, author=username, \
            recipeID=recipeID, ingredients=ingredients_note, steps=steps, tags=tags, pictures=pictures, revTitle=None, \
            revDesc=None, stars=None, revPics=None))
    except:
        return redirect(url_for('home', error='Failed to add recipe!'))

@app.route('/search_results')
def search_results():
    messages = ["Please refine your search, you didn't sepcify anything!"]
    results = {}
    return render_template('search_results.html', messages=messages, results=results)

@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        keyword = ''
        tag = ''
        author = ''
        reviewer = ''
        keyword = ''
        star = ''

        if request.method == 'POST':
            keyword = request.form['keyword']
            tag = request.form['tag']
            author = request.form['author']
            reviewer = request.form['reviewer']
            star = request.form['star']
        else:
            author = request.args.get('userName')

        messages = []
        results = {}
        if keyword == '' and tag == '' and author == '' and reviewer == '' and star == '':
            messages.append("Please refine your search, you didn't sepcify anything!")
        else:
            cursor = conn.cursor()
            recipes = []
            query = ''
            flaga = False
            flagb = False
            flagc = False
            if keyword != '' or author != '':
                flaga = True
                query = 'SELECT a.recipeID FROM Recipe AS a'

            if tag != '':
                flagb = True
                if query == '':
                    query = 'SELECT b.recipeID FROM RecipeTag AS b'
                else:
                    query = query + ' JOIN RecipeTag AS b on a.recipeID=b.recipeID'

            if reviewer != '' or star != '':
                flagc = True
                if query == '':
                    query = 'SELECT c.recipeID FROM Review AS c'
                elif flaga:
                    query = query + ' JOIN Review AS c on a.recipeID=c.recipeID'
                else:
                    query = query + ' JOIN Review AS c on b.recipeID=c.recipeID'
            
            query = query + ' WHERE'
            if keyword != '':
                query = query + f' a.title LIKE "%{keyword}%"'
            if author != '':
                if keyword != '':
                    query = query + f' AND a.postedBy="{author}"'
                else:
                    query = query + f' a.postedBy="{author}"'
            if tag != '':
                if flaga:
                    query = query + f' AND b.tagText="{tag}"'
                else:
                    query = query + f' b.tagText="{tag}"'
            if reviewer != '':
                if flaga or flagb:
                    query = query + f' AND c.userName="{reviewer}"'
                else:
                    query = query + f' c.userName="{reviewer}"'
            if star != '':
                if flaga or flagb or reviewer != '':
                    query = query + f' AND c.stars={star}'
                else:
                    query = query + f' c.stars={star}'

            #print(f'query={query}')
            cursor.execute(query)
            for row in cursor.fetchall():
                #print(row)
                recipes.append(row['recipeID'])

            if len(recipes) == 0:
                messages.append("No recipe found!")
            else:
                query = 'SELECT recipeID, title, postedBy FROM Recipe WHERE recipeID IN ('
                for id in recipes:
                    query = query + f' {id},'
                query = query + '0)'
                cursor.execute(query)
                results = cursor.fetchall()
                #print(results)
            cursor.close()

        return render_template('search_results.html', messages=messages, results=results)
    except:
        return redirect(url_for('home', error='Invalid recipe search!'))

@app.route('/view_recipe', methods=['GET', 'POST'])
def view_recipe():
    try:
        #print("enter view_recipe")
        recipeID = request.form['recipeID']
        #print(f'view recipeID={recipeID}')

        steps = []
        tags = []
        ingredients = []

        cursor = conn.cursor();
        query = f'SELECT title, numServings, postedBy FROM Recipe WHERE recipeID={recipeID}'
        cursor.execute(query)
        result = cursor.fetchone()
        title = result['title']
        numServings = result['numServings']
        author = result['postedBy']

        if result is None or len(result) == 0:
            return redirect(url_for('home', error='Invalid receipe id!'))

        query = f'SELECT sDesc FROM Step WHERE recipeID={recipeID} ORDER BY stepNo'
        cursor.execute(query)
        for row in cursor.fetchall():
            steps.append(row['sDesc'])

        query = f'SELECT tagText FROM RecipeTag WHERE recipeID={recipeID}'
        cursor.execute(query)
        for row in cursor.fetchall():
            tags.append(row['tagText'])

        query = f'SELECT iName, unitName, amount FROM RecipeIngredient WHERE recipeID={recipeID}'
        cursor.execute(query)
        for row in cursor.fetchall():
            ingredients.append(f"{row['iName']} {row['amount']}{row['unitName']}")

        username = session['username']
        query = f'SELECT revTitle, revDesc, stars FROM Review WHERE userName="{username}" AND recipeID={recipeID}'
        cursor.execute(query)
        review = cursor.fetchone()
        if review is None:
            review = {}
            review['revTitle'] = None
            review['revDesc'] = None
            review['stars'] = None

        pictures=[]
        query = f'SELECT pictureURL FROM RecipePicture WHERE recipeID={recipeID}'
        cursor.execute(query)
        for row in cursor.fetchall():
            pictures.append(row['pictureURL'])

        revPics=[]
        query = f'SELECT pictureURL FROM ReviewPicture WHERE userName="{username}" AND recipeID={recipeID}'
        cursor.execute(query)
        for row in cursor.fetchall():
            revPics.append(row['pictureURL'])

        cursor.close()
        return redirect(url_for('recipe_info', title=title, numServings=numServings, author=author, \
            recipeID=recipeID, ingredients=ingredients, steps=steps, tags=tags, pictures=pictures, revTitle=review['revTitle'], \
            revDesc=review['revDesc'], stars=review['stars'], revPics=revPics))
    except:
        return redirect(url_for('home', error='Invalid receipe id!'))
        
@app.route('/review', methods=['GET'])
def review():
    try:
        page = request.args.get('page')
        recipeID = request.args.get('recipeID')
        userName = request.args.get('userName')
        limit = 3 * int(page)
        cursor = conn.cursor();
        query = f'SELECT * FROM Review WHERE recipeID={recipeID} ORDER BY userName LIMIT {limit}'
        if userName is not None:
            query = f'SELECT * FROM Review WHERE userName>"{userName}" AND recipeID={recipeID} ORDER BY userName LIMIT {limit}'
        cursor.execute(query)
        reviews = cursor.fetchall()
        #print(f'reviews={reviews}')
        boundry_name = ''
        if len(reviews):
            boundry_name = reviews[len(reviews) - 1]["userName"]
            for review in reviews:
                query = f'SELECT pictureURL FROM ReviewPicture WHERE userName="{review["userName"]}" \
                        AND recipeID={review["recipeID"]}'
                cursor.execute(query)
                review["pictures"] = cursor.fetchall()
        else:
            reviews = None
        cursor.close()
        return render_template('review.html', page=page, recipeID=recipeID, userName=boundry_name, reviews=reviews)
    except:
        return redirect(url_for('home', error='Invalid review!'))

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    try:
        title = request.form['title']
        review = request.form['review']
        star = request.form['star']
        username = session['username']
        revTitle = request.form['revTitle']
        recipeID = request.form['recipeID']
        pictures = []
        for p in zip(request.form.getlist('picture')):
            pictures.append(p[0])

        cursor = conn.cursor();
        query = f'UPDATE Review SET revTitle="{title}", revDesc="{review}", stars={star} WHERE \
            userName="{username}" AND recipeID={recipeID}'
        if revTitle == '':
            query = f'INSERT INTO Review (userName, recipeID, revTitle, revDesc, stars) VALUES \
                ("{username}", {recipeID}, "{title}", "{review}", {star})'
        cursor.execute(query)

        for picture in pictures:
            query = 'INSERT INTO ReviewPicture (userName, recipeID, pictureURL) VALUES (%s, %s, %s)'
            cursor.execute(query, (username, recipeID, picture))
            #conn.commit()
        conn.commit()
        cursor.close()
        return redirect(url_for('review', page=1, recipeID=recipeID, userName=''))
    except:
        return redirect(url_for('home', error='Failed to add review!'))

@app.route('/view_more_reviews', methods=['GET', 'POST'])
def view_more_reviews():
    recipeID = request.form['recipeID']
    page = request.form['page']
    userName = request.form['userName']
    page = int(page)
    return redirect(url_for('review', page=page, recipeID=recipeID, userName=userName))

@app.route('/group')
def group():
    return render_template('group.html')

@app.route('/search_group_results', methods=['GET'])
def search_group_results():
    results = request.args.getlist('results')
    messages = request.args.getlist('messages')
    results_dict = []
    for result in results:
        results_dict.append(eval(result))
    return render_template('search_group_results.html', messages=messages, results=results_dict)

@app.route('/search_group', methods=['GET', 'POST'])
def search_group():
    group = ''
    creater = ''
    description = ''
    joined = 0

    if request.method == 'POST':
        group = request.form['group']
        creater = request.form['creater']
        description = request.form['description']
    else:
        creater = session['username']
        joined = int(request.args.get('joined'))

    cursor = conn.cursor()
    messages = []

    if joined != 0:
        query = f'SELECT gName, gCreator FROM `GroupMembership` WHERE memberName="{creater}"'
        cursor.execute(query)
        results = cursor.fetchall()
        data = []
        for result in results:
            query = f'SELECT * FROM `Group` WHERE gName="{result["gName"]}" AND gCreator="{result["gCreator"]}"'
            cursor.execute(query)
            data.append(cursor.fetchone())
        if len(data) == 0:
            messages.append("No group joined!")
        return redirect(url_for('search_group_results', messages=messages, results=data))
    
    query = 'SELECT * FROM `Group`'

    flag = False
    if group != '':
        flag = True
        query = query + f' WHERE gName="{group}"'
    
    if creater != '':
        if flag:
            query = query + f' AND gCreator="{creater}"'
        else:
            query = query + f' WHERE gCreator="{creater}"'
        flag = True

    if description != '':
        if flag:
            query = query + f' AND gDesc LIKE "%{description}%"'
        else:
            query = query + f' WHERE gDesc LIKE "%{description}%"'
        flag = True

    #print(query)
    cursor.execute(query)
    results = cursor.fetchall()
    if len(results) == 0:
        messages.append("No group found!")
    cursor.close()

    return redirect(url_for('search_group_results', messages=messages, results=results))

@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    try:
        group = ''
        creater = session['username']
        description = ''

        if request.method == 'POST':
            group = request.form['group']
            description = request.form['description']

        cursor = conn.cursor()
        query = 'INSERT INTO `Group` (gName, gCreator, gDesc) VALUES (%s, %s, %s)'
        cursor.execute(query, (group, creater, description))
        cursor = conn.cursor()
        conn.commit()
        cursor.close()
        return redirect(url_for('group_info', gName=group, gCreator=creater, gDesc=description))
    except:
        return redirect(url_for('home', error='Failed to create group!'))

@app.route('/group_info', methods=['GET'])
def group_info():
    try:
        gName = request.args.get('gName')
        gCreator = request.args.get('gCreator')
        gDesc = request.args.get('gDesc')
        owner = None
        need_to_join = None

        username = session['username']
        #print(f'username={username}')
        #print(f'gCreator={gCreator}')
        if gCreator == username:
            owner = True
        else:
            owner = None
        
        if owner is None:
            cursor = conn.cursor();
            query = 'SELECT memberName FROM `GroupMembership` WHERE memberName=%s AND gName=%s AND gCreator=%s'
            cursor.execute(query, (username, gName, gCreator))
            data = cursor.fetchall()
            if len(data) == 0:
                need_to_join = True
            else:
                need_to_join= None
            cursor.close()

        return render_template('group_info.html', gName=gName, gCreator=gCreator, gDesc=gDesc, owner=owner, need_to_join=need_to_join)
    except:
        return redirect(url_for('home', error='Invalid group!'))

@app.route('/group_member', methods=['GET'])
def group_member():
    try:
        gName = request.args.get('gName')
        gCreator = request.args.get('gCreator')
        gDesc = request.args.get('gDesc')

        cursor = conn.cursor();
        query = 'SELECT memberName FROM `GroupMembership` WHERE gName=%s AND gCreator=%s'
        cursor.execute(query, (gName, gCreator))
        data = cursor.fetchall()
        cursor.close()
        return render_template('group_member.html', gName=gName, gCreator=gCreator, gDesc=gDesc, user_list=data)
    except:
        return redirect(url_for('home', error='Failed to search group member!'))

@app.route('/view_group', methods=['GET', 'POST'])
def view_group():
    gName = ''
    gCreator = ''
    gDesc = ''

    if request.method == 'POST':
        gName = request.form['gName']
        gCreator = request.form['gCreator']
        gDesc = request.form['gDesc']
    else:
        gName = request.args.get('gName')
        gCreator = request.args.get('gCreator')
        gDesc = request.args.get('gDesc')

    return redirect(url_for('group_info', gName=gName, gCreator=gCreator, gDesc=gDesc))

@app.route('/join_group', methods=['GET', 'POST'])
def join_group():
    try:
        gName = ''
        gCreator = ''
        gDesc = ''

        if request.method == 'POST':
            gName = request.form['gName']
            gCreator = request.form['gCreator']
            gDesc = request.form['gDesc']

        username = session['username']
        cursor = conn.cursor()
        query = 'INSERT INTO `GroupMembership` (memberName, gName, gCreator) VALUES(%s, %s, %s)'
        cursor.execute(query, (username, gName, gDesc))
        conn.commit()
        cursor.close()

        return redirect(url_for('group_info', gName=gName, gCreator=gCreator, gDesc=gDesc))
    except:
        return redirect(url_for('home', error='Failed to join group!'))

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    try:
        gName = ''
        gCreator = ''
        eName = ''
        eDesc = ''
        eDate = ''
        description = ''

        if request.method == 'POST':
            gName = request.form['gName']
            gCreator = request.form['gCreator']
            eName = request.form['eName']
            eDesc = request.form['eDesc']
            eDate = request.form['eDate']

        cursor = conn.cursor()
        query = 'INSERT INTO `Event` (`eName`, `eDesc`, `eDate`, `gName`, `gCreator`) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (eName, eDesc, eDate, gName, gCreator))
        conn.commit()

        query = 'SELECT MAX(eID) FROM `Event` WHERE eName=%s AND eDesc=%s AND eDate=%s AND gName=%s AND gCreator=%s'
        cursor.execute(query, (eName, eDesc, eDate, gName, gCreator))
        eID = cursor.fetchone()["MAX(eID)"]
        cursor.close()
        return redirect(url_for('group_info', gName=gName, gCreator=gCreator, gDesc=description))
    except:
        return redirect(url_for('home', error='Invalid event creation!'))

@app.route('/search_event_results', methods=['GET'])
def search_event_results():
    results = request.args.getlist('results')
    messages = request.args.getlist('messages')
    results_dict = []
    for result in results:
        #print(f'result={result}')
        '''
        temp = {}
        temp['eID'] = result['eID']
        temp['eName'] = result['eName']
        temp['eDesc'] = result['eDesc']
        temp['eDate'] = str(result['eDate'])
        temp['gName'] = result['gName']
        temp['gCreator'] = result['gCreator']
        results_dict.append(temp)'''
        results_dict.append(eval(result))
    return render_template('search_event_results.html', messages=messages, results=results_dict)

@app.route('/search_event', methods=['GET', 'POST'])
def search_event():
    try:
        eID = ''
        group = ''
        creater = ''
        member = ''
        valid = ''

        if request.method == 'POST':
            eID = request.form['eID']
            group = request.form['group']
            creater = request.form['creater']
            member = request.form['member']
            valid = request.form['valid']
        else:
            group = request.args.get('gName')
            creater = request.args.get('gCreator')
            if group is None and creater is None:
                group = ''
                creater = ''
                member = session['username']

        cursor = conn.cursor()
        messages = []

        query = 'SELECT a.eID, a.eName, a.eDesc, a.eDate, a.gName, a.gCreator FROM `Event` AS a'
        if member != '':
            query = 'SELECT a.eID, a.eName, a.eDesc, a.eDate, a.gName, a.gCreator FROM `Event` AS a \
                    JOIN `RSVP` AS b ON a.eID=b.eID'

        flag = False
        if eID != '':
            flag = True
            query = query + f' WHERE a.eID="{eID}"'

        if group != '':
            if flag:
                query = query + f' AND a.gName="{group}"'
            else:
                query = query + f' WHERE a.gName="{group}"'
            flag = True
        
        if creater != '':
            if flag:
                query = query + f' AND a.gCreator="{creater}"'
            else:
                query = query + f' WHERE a.gCreator="{creater}"'
            flag = True

        if valid == '1':
            if flag:
                query = query + ' AND a.eDate>NOW()'
            else:
                query = query + ' WHERE a.eDate>NOW()'
            flag = True
        
        if member != '':
            if flag:
                query = query + f' AND b.userName="{member}"'
            else:
                query = query + f' WHERE b.userName="{member}"'

        query = query + ' ORDER BY a.eDate DESC'

        #print(query)
        cursor.execute(query)
        results = cursor.fetchall()
        if len(results) == 0:
            messages.append("No group found!")
        cursor.close()

        return redirect(url_for('search_event_results', messages=messages, results=results))
    except:
        return redirect(url_for('home', error='Failed to search event!'))

@app.route('/event_info', methods=['GET'])
def event_info():
    try:
        eID = request.args.get('eID')
        eDesc = request.args.get('eDesc')
        eDate = request.args.get('eDate')
        gName = request.args.get('gName')
        gCreator = request.args.get('gCreator')
        member = None
        rsvp = None

        cursor = conn.cursor()

        username = session['username']
        if gCreator == username:
            member = True
        else:
            query = 'SELECT memberName FROM `GroupMembership` WHERE memberName=%s AND gName=%s AND gCreator=%s'
            cursor.execute(query, (username, gName, gCreator))
            data = cursor.fetchall()
            if len(data):
                member = True
            else:
                member = None

        if member is not None and member is True:
            query = 'SELECT * FROM `RSVP` WHERE userName=%s AND eID=%s'
            cursor.execute(query, (username, eID))
            data = cursor.fetchall()
            if len(data) == 0:
                rsvp = True
            else:
                rsvp = None
        cursor.close()

        return render_template('event_info.html', eID=eID, eDesc=eDesc, eDate=eDate, gName=gName, gCreator=gCreator, member=member, rsvp=rsvp)
    except:
        return redirect(url_for('home', error='Invalid event!'))

@app.route('/view_event', methods=['GET', 'POST'])
def view_event():
    eID = ''
    eDesc = ''
    eDate = ''
    gName = ''
    gCreator = ''

    if request.method == 'POST':
        eID = request.form['eID']
        eDesc = request.form['eDesc']
        eDate = request.form['eDate']
        gName = request.form['gName']
        gCreator = request.form['gCreator']
    else:
        gName = request.args.get('gName')
        gCreator = request.args.get('gCreator')

    return redirect(url_for('event_info', eID=eID, eDesc=eDesc, eDate=eDate, gName=gName, gCreator=gCreator))

@app.route('/event_rsvp', methods=['GET'])
def event_rsvp():
    try:
        eID = request.args.get('eID')
        eDesc = request.args.get('eDesc')
        eDate = request.args.get('eDate')
        gName = request.args.get('gName')
        gCreator = request.args.get('gCreator')

        cursor = conn.cursor()
        query = 'SELECT userName, response FROM `RSVP` WHERE eID=%s'
        cursor.execute(query, (eID))
        results = cursor.fetchall()

        query = 'SELECT pictureURL FROM EventPicture WHERE eID=%s'
        cursor.execute(query, (eID))
        pictures = cursor.fetchall()
        cursor.close()

        return render_template('event_rsvp.html', eID=eID, eDesc=eDesc, eDate=eDate, gName=gName, \
                gCreator=gCreator, results=results, pictures=pictures)
    except:
        return redirect(url_for('home', error='RSVP error!'))

@app.route('/rsvp_event', methods=['GET', 'POST'])
def rsvp_event():
    try:
        eID = ''
        eDesc = ''
        eDate = ''
        gName = ''
        gCreator = ''
        response = ''

        if request.method == 'POST':
            eID = request.form['eID']
            eDesc = request.form['eDesc']
            eDate = request.form['eDate']
            gName = request.form['gName']
            gCreator = request.form['gCreator']
            response = request.form['response'][0]
        else:
            gName = request.args.get('gName')
            gCreator = request.args.get('gCreator')

        username = session['username']
        cursor = conn.cursor()
        query = 'INSERT INTO `RSVP` (userName, eID, response) VALUES(%s, %s, %s)'
        cursor.execute(query, (username, eID, response))
        conn.commit()
        cursor.close()

        return redirect(url_for('event_info', eID=eID, eDesc=eDesc, eDate=eDate, gName=gName, gCreator=gCreator))
    except:
        return redirect(url_for('home', error='Invalid event RSVP!'))

@app.route('/add_EventPic', methods=['POST'])
def add_EventPic():
    try:
        eID = request.form['eID']
        eDesc = request.form['eDesc']
        eDate = request.form['eDate']
        gName = request.form['gName']
        gCreator = request.form['gCreator']
        picURL = request.form['picture']

        cursor = conn.cursor()
        query = 'INSERT INTO `EventPicture` (eID, pictureURL) VALUES(%s, %s)'
        cursor.execute(query, (eID, picURL))
        conn.commit()
        cursor.close()

        return redirect(url_for('event_info', eID=eID, eDesc=eDesc, eDate=eDate, gName=gName, gCreator=gCreator))
    except:
        return redirect(url_for('home', error='Invalid event picture!'))

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = '!@#ABCND%$^*qwehdgaQouY'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
