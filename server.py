from datetime import datetime
from flask import Flask, Response, redirect, render_template, request, flash , session
import requests, json
import sqlite3
import secrets
from passlib.hash import pbkdf2_sha256
import pymongo

app=Flask(__name__)
app.secret_key=secrets.token_urlsafe(32)
#cursor=conn.cursor()
'''uri = "mongodb+srv://<username>:<password>@grocerystoredb.hkslphq.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
db = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    db.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)'''

try:
    mongo = pymongo.MongoClient(
        host = 'localhost',
        port = 27017,
        serverSelectionTimeoutMS = 1000
    )
    db = mongo.groceryStore #connect to assgn
    mongo.server_info() #trigger exception if cannot connect to db
except:
    print("Error -connect to db")

@app.route("/", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/logged/", methods=["POST"] )
def logged():
    # Get log in info from log in form
    user = request.form["username"].lower()
    pwd = request.form["password"]
    #pwd = str(sha1(request.form["password"].encode('utf-8')).hexdigest())
    # Make sure form input is not blank and re-render log in page if blank
    if user == "" or pwd == "":
        return render_template ( "login.html" )
    # Find out if info in form matches a record in user database
    #query = "SELECT * FROM users WHERE username = :user AND password = :pwd"
    rows = list(db.admin.find({"username":user,"password":pwd}))
    print(rows)
    # If username and password match a record in database, set session variables
    if len(rows) == 1:
        session['user'] = user
        session['time'] = datetime.now()
        #session['uid'] = rows[0]["_id"]
    # Redirect to Home Page
    if 'user' in session:
        print("line 58")
        return redirect ( "/shop" )
    # If username is not in the database return the log in page
    return render_template ( "login.html", msg="Wrong username or password." )



@app.route("/shop")
def index():
    products = list(db.products.find({}))
    #print(len(products),"***********")
    #shirts = db.execute("SELECT * FROM shirts ORDER BY onSalePrice")
    productsLen = len(products)
    # Initialize variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
        #shoppingCart = db.execute("SELECT samplename, image, SUM(qty), SUM(subTotal), price, id FROM cart GROUP BY samplename")
        #shopLen = len(shoppingCart)
        #for i in range(shopLen):
            #total += shoppingCart[i]["SUM(subTotal)"]
            #totItems += shoppingCart[i]["SUM(qty)"]
   
    #return render_template ("index.html", shoppingCart=shoppingCart, shirts=products, shopLen=shopLen, shirtsLen=productsLen, total=total, totItems=totItems, display=display )
    return render_template ( "index2.html", products=products, shoppingCart=shoppingCart, shirtsLen=productsLen, shopLen=shopLen, total=total, totItems=totItems, display=display)

@app.route("/update/")
def update():
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    qty = int(request.args.get('quantity'))
    
    if session:
        # Store id of the selected shirt
        id = int(request.args.get('id'))
        #db.execute("DELETE FROM cart WHERE id = :id", id=id)
        # Select info of selected shirt from database
        goods = list(db.products.find({"product_id":id}))
        #goods = db.execute("SELECT * FROM shirts WHERE id = :id", id=id)
        # Extract values from selected shirt record
        # Check if shirt is on sale to determine price
        for g in goods:
          item = {}
          price= g[0]["price"]
          item["samplename"] = g[0]["product_name"]
          item["image"] = g[0]["product_image"]
          item["subTotal"] = qty * price
          item["qty"] = qty
          shoppingCart.append(item)
        # Insert selected shirt into shopping cart
        #db.execute("INSERT INTO cart (id, qty, samplename, image, price, subTotal) VALUES (:id, :qty, :samplename, :image, :price, :subTotal)", id=id, qty=qty, samplename=samplename, image=image, price=price, subTotal=subTotal)
        #shoppingCart = db.execute("SELECT samplename, image, SUM(qty), SUM(subTotal), price, id FROM cart GROUP BY samplename")
        shopLen = len(shoppingCart)
        # Rebuild shopping cart
        for i in range(shopLen):
            total += shoppingCart[i]["subTotal"]
            totItems += shoppingCart[i]["qty"]
        # Go back to cart page
        return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )

@app.route("/buy/")
def buy():
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    qty = int(request.args.get('quantity'))
    if session:
        # Store id of the selected shirt
        id = int(request.args.get('id'))
        # Select info of selected shirt from database
        #goods = db.execute("SELECT * FROM shirts WHERE id = :id", id=id)
        goods = list(db.products.find({"product_id":id}))
        # Extract values from selected shirt record
        # Check if shirt is on sale to determine price
        for g in goods:
          item = {}
          price= g[0]["price"]
          item["samplename"] = g[0]["product_name"]
          item["image"] = g[0]["product_image"]
          item["subTotal"] = qty * price
          item["qty"] = qty
          shoppingCart.append(item)
        
        # Insert selected shirt into shopping cart
        #db.execute("INSERT INTO cart (id, qty, samplename, image, price, subTotal) VALUES (:id, :qty, :samplename, :image, :price, :subTotal)", id=id, qty=qty, samplename=samplename, image=image, price=price, subTotal=subTotal)
        #shoppingCart = db.execute("SELECT samplename, image, SUM(qty), SUM(subTotal), price, id FROM cart GROUP BY samplename")
        shopLen = len(shoppingCart)
        # Rebuild shopping cart
        for i in range(shopLen):
            total += shoppingCart[i]["subTotal"]
            totItems += shoppingCart[i]["qty"]
        # Select all shirts for home page view
        #shirts = db.execute("SELECT * FROM shirts ORDER BY samplename ASC")
        products = list(db.products.find({}))
        shirtsLen = len(products)
        # Go back to home page
        return render_template ("index2.html", shoppingCart=shoppingCart, shirts=products, shopLen=shopLen, shirtsLen=shirtsLen, total=total, totItems=totItems, display=display, session=session )

@app.route("/filter/")
def filter():
    if request.args.get('category'):
        query = request.args.get('category')
        #shirts = db.execute("SELECT * FROM shirts WHERE typeClothes = :query ORDER BY samplename ASC", query=query )
        products=list(db.products.find({"category":query}))
    if request.args.get('id'):
        query = int(request.args.get('id'))
        shirts = db.execute("SELECT * FROM shirts WHERE id = :query ORDER BY samplename ASC", query=query)
    if request.args.get('kind'):
        query = request.args.get('kind')
        shirts = db.execute("SELECT * FROM shirts WHERE kind = :query ORDER BY samplename ASC", query=query)
    if request.args.get('price'):
        query = request.args.get('price')
        shirts = db.execute("SELECT * FROM shirts ORDER BY onSalePrice ASC")
    shirtsLen = len(shirts)
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    if 'user' in session:
        # Rebuild shopping cart
        shoppingCart = db.execute("SELECT samplename, image, SUM(qty), SUM(subTotal), price, id FROM cart GROUP BY samplename")
        shopLen = len(shoppingCart)
        for i in range(shopLen):
            total += shoppingCart[i]["SUM(subTotal)"]
            totItems += shoppingCart[i]["SUM(qty)"]
        # Render filtered view
        return render_template ("index.html", shoppingCart=shoppingCart, shirts=shirts, shopLen=shopLen, shirtsLen=shirtsLen, total=total, totItems=totItems, display=display, session=session )
    # Render filtered view
    return render_template ( "index2.html", shirts=shirts, shoppingCart=shoppingCart, shirtsLen=shirtsLen, shopLen=shopLen, total=total, totItems=totItems, display=display)

@app.route("/checkout/")
def checkout():
    #order = db.execute("SELECT * from cart") we have to have this as a global object and fetch from there
    # Update purchase history of current customer
    order = []
    for item in order:
        db.execute("INSERT INTO purchases (uid, id, samplename, image, quantity) VALUES(:uid, :id, :samplename, :image, :quantity)", uid=session["uid"], id=item["id"], samplename=item["samplename"], image=item["image"], quantity=item["qty"] )
    # Clear shopping cart
    db.execute("DELETE from cart")
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    # Redirect to home page
    return redirect('/')

@app.route("/remove/", methods=["GET"])
def remove():
    # Get the id of shirt selected to be removed
    out = int(request.args.get("id"))
    # Remove shirt from shopping cart
    db.execute("DELETE from cart WHERE id=:id", id=out)
    # Initialize shopping cart variables
    totItems, total, display = 0, 0, 0
    # Rebuild shopping cart
    shoppingCart = db.execute("SELECT samplename, image, SUM(qty), SUM(subTotal), price, id FROM cart GROUP BY samplename")
    shopLen = len(shoppingCart)
    for i in range(shopLen):
        total += shoppingCart[i]["SUM(subTotal)"]
        totItems += shoppingCart[i]["SUM(qty)"]
    # Turn on "remove success" flag
    display = 1
    # Render shopping cart
    return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )


########################################################################################################
@app.route('/old')
def login_old():
  url=requests.get('https://dog.ceo/api/breeds/image/random')
  image=json.loads(url.text)
  return render_template('index2.html',imagefile=image['message'])

@app.route('/login1',methods=['POST'])
def login1(): #when users entry username and password
  user=request.form.get('username')
  pword=request.form.get('password')
  documents = list(db.admin.find({"username":user,"password":pword}))
  #("SELECT username,password FROM admindata")  # id username password
  #row=cursor.fetchall()
  if len(documents)>0:
    #if (user==item[0] and pbkdf2_sha256.verify(pword,item[1])):
    url=requests.get('https://dog.ceo/api/breeds/image/random')
    image=json.loads(url.text)
    return render_template('index.html',imagefile=image['message'])
  url=requests.get('https://dog.ceo/api/breeds/image/random')
  image=json.loads(url.text)
  return render_template('login.html',imagefile=image['message'])

@app.route('/signup')
def signup():
  return render_template('signup.html')

@app.route('/signup1', methods=['POST'])
def signup1():
  user=request.form.get('username')
  pword=request.form.get('password')
  pword_rep=request.form.get('psw-repeat')
  if (pword==pword_rep):
    cursor.execute("SELECT username,password FROM user")  # id username password
    row=cursor.fetchall()
    for item in row:
      if (user==item[0] and pbkdf2_sha256.verify(pword,item[1])):
        url=requests.get('https://dog.ceo/api/breeds/image/random')
        image=json.loads(url.text)
        return render_template('index.html',imagefile=image['message'])
    cursor.execute('INSERT INTO user(username, password) VALUES(?,?)',(user,pbkdf2_sha256.hash(pword),))
    conn.commit()
    url=requests.get('https://dog.ceo/api/breeds/image/random')
    image=json.loads(url.text)
    return render_template('login.html',imagefile=image['message'])
  else:
    messages='Password and Repeat Password is not the same!!'
    flash(messages)
    return render_template('signup.html')

@app.route('/nature')
def nature():
  return render_template('nature.html')

@app.route('/dogs')
def dogs():
  n=20
  imglist=[]
  for i in range(n): #i: 0 to n-1
    url=requests.get('https://dog.ceo/api/breeds/image/random')
    image=json.loads(url.text)
    imglist.append([i+1,image['message']]) 
    #imglist = [ [1,'xxxxx'], [2,'BBBBB'] ]  total = n
  return render_template('dogs.html', data=imglist, total=n)

if __name__ == '__main__':
    app.run(port=5000, debug=True) #port > 1024
