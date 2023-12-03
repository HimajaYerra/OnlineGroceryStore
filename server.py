import os
from datetime import datetime
import stripe
from flask import Flask, Response, redirect, render_template, request, flash , session
import requests, json
import sqlite3
import secrets
from passlib.hash import pbkdf2_sha256
import pymongo

app=Flask(__name__)
app.secret_key=secrets.token_urlsafe(32)
stripe_keys = {
   'secret_key': os.getenv("STRIPE_SECRET_KEY"),
   'publishable_key': os.getenv("STRIPE_PUBLISHABLE_KEY")
}
stripe.api_key = stripe_keys['secret_key']

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

shoppingHash = {}
orderHash = {}

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



###Registration Page####
@app.route("/register", methods=["GET"])
def registration():
    return render_template("registration.html")

####registered##

@app.route("/registered/", methods=["POST"] )
def registered():
    firstname=request.form.get('firstname')
    lastname=request.form.get('lastname')
    email=request.form.get('emailid')
    dob=request.form.get('dob')
    address=request.form.get('address')
    cardtype=request.form.get('cardtype')
    nameoncard=request.form.get('nameoncard')
    cardnumber=request.form.get('cardnumber')
    expirydate=request.form.get('expiry-date')
    postcode=request.form.get('postcode')
    user=request.form.get('username')
    pword=request.form.get('password')
    pword_rep=request.form.get('psw-repeat')
    if (pword==pword_rep):
     db.customers.insert_one({'firstname':firstname, 'lastname':lastname, 'emailid':email, 'dob':dob,
                              'address':address,'card_type':cardtype, 'name_on_card':nameoncard, 'expity_date':expirydate,'postcode':postcode,
                              'username':user, 'password':pword})     
     return render_template('login.html')
    else:
        messages='Password and Repeat Password is not the same!!'
    flash(messages)
    return render_template('registration.html')

##############
def getTrackingData(curr_status=1):
    trackingData = [
        {"status": 1, "status_name": "Ordered", "status_value": 0},
        {"status": 2, "status_name": "Preparing", "status_value": 0},
        {"status": 3, "status_name": "Shipped", "status_value": 0},
        {"status": 4, "status_name": "Delivery", "status_value": 0},
        {"status": 5, "status_name": "Delivered", "status_value": 0},
    ]
    for t in trackingData:
        if t["status"] <= curr_status:
            t["status_value"] = 100
    if curr_status == len(trackingData)-1:
        trackingData[curr_status-1]["status_value"] = 50 
    return trackingData

def getReturnTrackingData(curr_status=1):
    returnTrackingData = [
        {"status": 1, "status_name": "Return initiated", "status_value": 0},
        {"status": 2, "status_name": "Return shipped", "status_value": 0},
        {"status": 3, "status_name": "Return received", "status_value": 0},
        {"status": 4, "status_name": "Return processing", "status_value": 0},
        {"status": 5, "status_name": "Refund issued", "status_value": 0},
    ]
    for t in returnTrackingData:
        if t["status"] <= curr_status:
            t["status_value"] = 100
    if curr_status == len(returnTrackingData)-1:
        returnTrackingData[curr_status-1]["status_value"] = 50 
    return returnTrackingData


@app.route("/", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/logged/", methods=["POST"] )
def logged():
    print("Here")
    # Get log in info from log in form
    user = request.form["username"].lower()
    pwd = request.form["password"]
    #pwd = str(sha1(request.form["password"].encode('utf-8')).hexdigest())
    # Make sure form input is not blank and re-render log in page if blank
    if user == "" or pwd == "":
        return render_template ( "login.html" )
    # Find out if info in form matches a record in user database
    #query = "SELECT * FROM users WHERE username = :user AND password = :pwd"

     #rows = list(db.customers.find({"username":user,"password":pwd}))
    #   print(rows)

    print(user, pwd)

    adminLogin = False
    rows = list(db.admin.find({"username":user,"password":pwd}))
    print(rows)
    if (len(rows) == 1):
        adminLogin = True
    else:
        rows = list(db.users.find({"username": user, "password": pwd}))

    # If username and password match a record in database, set session variables
    if len(rows) == 1:
        session['uid'] = rows[0]['uid']
        session['user'] = user
        session['time'] = datetime.now()
        #session['uid'] = rows[0]["_id"]
    # Redirect to Home Page
    if 'user' in session:

        #print("line 58")
        return redirect ( "/shop" )

        if adminLogin:
            return redirect("/order_update")
        else:
            return redirect ( "/shop" )

    # If username is not in the database return the log in page
    return render_template ( "login.html", msg="Wrong username or password." )



@app.route("/shop")
def index():
    products = list(db.products.find({}))
    productsLen = len(products)
    shoppingCart = []
    if session and "uid" in session and session["uid"] in shoppingHash:
       shoppingCart = shoppingHash[session["uid"]]
    shopLen = len(shoppingCart)

   # print("here", shoppingCart, shoppingHash)
    #print("Here")


    totItems, total, display = 0, 0, 0
    for i in range(shopLen):
       total += shoppingCart[i]["subTotal"]
       totItems += shoppingCart[i]["qty"]
    return render_template ( "index2.html", products=products, shoppingCart=shoppingCart, productsLen=productsLen, shopLen=shopLen, total=total, totItems=totItems, display=display)

  

@app.route("/order_update")
def order_update():
    products = list(db.products.find({}))
    productsLen = len(products)
    shoppingCart = []
    if session and "uid" in session and session["uid"] in shoppingHash:
       shoppingCart = shoppingHash[session["uid"]]
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    for i in range(shopLen):
       total += shoppingCart[i]["subTotal"]
       totItems += shoppingCart[i]["qty"]
    
    usersList = list(db.users.find({}))
    usersLen = len(usersList)

    return render_template ( "order_update.html", products=products, shoppingCart=shoppingCart, productsLen=productsLen, shopLen=shopLen, total=total, totItems=totItems, display=display, usersList=usersList, usersLen=usersLen, preselected_uid=2, ordersData=[], orderUser="", ordersLen=-1)

@app.route('/fetch_order_history/',methods=["GET"])
def fetch_order_history(uidInput=None):
    usersList = list(db.users.find({}))
    usersLen = len(usersList)
    uid = uidInput if uidInput != None else int(request.args.get('selectedUser'))
    preselected_uid = -1 
    ordersData = []
    orderUser = ""
    if uid:
        preselected_uid = uid
        orders = list(db.orders.find({"ordered_by": uid}))
        for order in orders:
            orderItems = []
            for item in order["order_items"]:
                item_id = item["item_id"]
                items = list(db.products.find({"product_id": item_id}))
                item_name = items[0]["product_name"]
                item_img = items[0]["product_image"]
                orderItems.append({
                   "item_id": item_id,
                   "item_name": item_name,
                   "item_qty": item["item_qty"],
                   "item_price": item["item_price"],
                   "item_img": item_img
                })
            order_delivery_type = order["order_delivery_type"]
            order_payment_method = order["payment_method"]
            order_date = order["order_date"]
            order_total = order["order_total"]
            order_status = order["order_status"]
            order_id = order["order_id"]
            order_return_status = order["order_return_status"]
            tracking_data = getTrackingData(order["order_status"])
            return_tracking_data = getReturnTrackingData(order_return_status)
            order_refund_amount = 0
            if order_return_status > 0:
                allReturns = list(db.returns.find({"original_order_id": order_id}))
                if len(allReturns) == 1:
                    return_order = allReturns[0]
                    order_refund_amount = return_order["return_total"]
            ordersData.append({"orderItems": orderItems, "order_delivery_type": order_delivery_type, "order_payment_method": order_payment_method, "order_date": order_date, "order_total": order_total, "order_status": order_status, "order_id": order_id, "tracking_data": tracking_data, "order_return_status": order_return_status, "return_tracking_data": return_tracking_data, "order_refund_amount": order_refund_amount})
        for user in usersList:
            if user["uid"] == uid:
                orderUser = user["username"]
                break
    return render_template ( "order_update.html", products=[], shoppingCart=[], productsLen=0, shopLen=0, total=0, totItems=0, display=0, usersList=usersList, usersLen=usersLen, preselected_uid=preselected_uid, ordersData=ordersData, orderUser=orderUser, ordersLen=len(ordersData))

@app.route("/update_order_status/")
def update_order_status():
    uid = int(request.args.get("uid"))
    order_id = int(request.args.get("order_id"))
    newstatus = int(request.args.get("status"))
    result = db.orders.update_one({"order_id": order_id}, {"$set": {"order_status": newstatus}}) 
    if result.modified_count > 0:
        print("Updated successfully")
    else:
        print("Not updated")

    return fetch_order_history(uid)

@app.route("/update_return_order_status")
def update_return_order_status():
    uid = int(request.args.get("uid"))
    return_order_id = int(request.args.get("order_id"))
    newstatus = int(request.args.get("status"))
    print(newstatus)
    result = db.returns.update_one({"original_order_id": return_order_id}, {"$set": {"return_status": newstatus}})
    if result.modified_count > 0:
        # Also update orders collection
        ret = db.orders.update_one({"order_id": return_order_id}, {"$set": {"order_return_status": newstatus}})
        if ret.modified_count > 0:
            print("Updated successfully")
    return fetch_order_history(uid)

@app.route("/initiate_return")
def initiate_return():
    uid = int(request.args.get("uid"))
    order_id = int(request.args.get("order_id"))
    orders = list(db.orders.find({"order_id": order_id}))
    allReturns = db.returns.find({})
    maxExistingReturnId = 0
    for eReturn in allReturns:
        if "return_id" in eReturn:
            return_id = int(eReturn["return_id"])
            maxExistingReturnId = max(return_id, maxExistingReturnId)

    returnData = {}
    if len(orders) == 1:
        order = orders[0]
        return_id = maxExistingReturnId + 1
        return_total = 0
        returnItems = []
        for item in order["order_items"]:
            item_id = item["item_id"]
            form_item_id = int(request.args.get("item_id_"+str(item_id), -1))
            if (item_id == form_item_id):
                form_item_return_qty = int(request.args.get("item_id_return_qty_"+str(item_id)))
                form_item_price = int(request.args.get("item_id_price_"+str(item_id)))
                return_total += (form_item_price * form_item_return_qty)
                returnItems.append({"item_id": item_id, "item_qty": form_item_return_qty, "item_price": form_item_price})
        returned_by = order["ordered_by"]
        payment_method = "card"
        payment_id = 1
        return_status = 1
        original_order_id = order["order_id"]
        returnData = {"return_id": return_id, "return_items": returnItems, "return_total": return_total, "return_date": datetime.now(), "returned_by": returned_by, "payment_method": payment_method, "payment_id": payment_id, "return_status": return_status, "original_order_id": original_order_id}
        ret = db.returns.insert_one(returnData)
        if not ret.acknowledged:
            print("Error: Failed to insert into returns collection")
        else:
            # update the return status in the orders table also
            result = db.orders.update_one({"order_id": order_id}, {"$set": {"order_return_status": return_status}})
            if result.modified_count > 0:
                print("Orders updated successfully")
            else:
                print("Not updated")

    return orders_history(uid) 


@app.route("/return")
def returns():
    order_id = int(request.args.get("order_id"))
    uid = int(request.args.get("uid"))
    orders = list(db.orders.find({"order_id": order_id}))
    ordersData = []
    if (len(orders) == 1):
        for order in orders:
            orderItems = []
            for item in order["order_items"]:
                item_id = item["item_id"]
                item_isreturnable = item["item_isreturnable"]
                items = list(db.products.find({"product_id": item_id}))
                item_name = items[0]["product_name"]
                item_img = items[0]["product_image"]
                orderItems.append({
                   "item_id": item_id,
                   "item_name": item_name,
                   "item_qty": item["item_qty"],
                   "item_price": item["item_price"],
                   "item_img": item_img,
                   "item_isreturnable": item_isreturnable
                })
            order_delivery_type = order["order_delivery_type"]
            order_payment_method = order["payment_method"]
            order_date = order["order_date"]
            order_total = order["order_total"]
            order_status = order["order_status"]
            order_id = order["order_id"]
            tracking_data = getTrackingData(order["order_status"])
            ordersData.append({"orderItems": orderItems, "order_delivery_type": order_delivery_type, "order_payment_method": order_payment_method, "order_date": order_date, "order_total": order_total, "order_status": order_status, "order_id": order_id, "tracking_data": tracking_data})
        order = orders[0]
        return render_template("return.html", ordersData=ordersData, ordersLen=len(ordersData), shopLen=0, shoppingCart=[], total=0, uid=uid)
    return redirect("/shop")

@app.route("/update/")
def update():
    products = list(db.products.find({}))
    productsLen = len(products)
    shoppingCart = []
    
    if session and "uid" in session and session["uid"] in shoppingHash:
       shoppingCart = shoppingHash[session["uid"]]
    
    qty = int(request.args.get("quantity"))
    item_id = int(request.args.get("id"))

    if len(shoppingCart) > 0:
        for item in shoppingCart:
            if item["item_id"] == item_id:
                item["qty"] = qty
                item["subTotal"] = item["qty"] * item["price"]
    
    # Update the hash
    if session and "uid" in session and session["uid"] in shoppingHash:
        shoppingHash[session["uid"]] = shoppingCart

    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    for i in range(shopLen):
       total += shoppingCart[i]["subTotal"]
       totItems += shoppingCart[i]["qty"]

    return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )

@app.route("/buy/")
def buy():
    # Initialize shopping cart variables
    totItems, total, display = 0, 0, 0
    qty = int(request.args.get('quantity'))
    sampleNameIdxMap = {}
    if session:
        uid = session['uid']
        shoppingCart = []
        if uid not in shoppingHash:
           shoppingHash[uid] = [] 
        else:
           shoppingCart = shoppingHash[uid]
        for idx, item in enumerate(shoppingCart):
            sampleNameIdxMap[item["samplename"]] = idx


        productId = int(request.args.get('id'))
        goods = list(db.products.find({"product_id":productId}))
        for g in goods:
            item = {}
            price= g["price"]
            item["samplename"] = g["product_name"]
            item["image"] = g["product_image"]
            item["item_id"] = productId
            item["price"] = price 
            if item["samplename"] in sampleNameIdxMap:
               shoppingCart[sampleNameIdxMap[item["samplename"]]]["subTotal"] += qty * price
               shoppingCart[sampleNameIdxMap[item["samplename"]]]["qty"] += qty
            else:
                item["subTotal"] = qty * price
                item["qty"] = qty
                shoppingCart.append(item)
        
        shoppingHash[uid] = shoppingCart
        
        # Insert selected shirt into shopping cart
        # Rebuild shopping cart
        shopLen = len(shoppingCart)
        for i in range(shopLen):
            total += shoppingCart[i]["subTotal"]
            totItems += shoppingCart[i]["qty"]
        # Select all shirts for home page view
        #shirts = db.execute("SELECT * FROM shirts ORDER BY samplename ASC")
        products = list(db.products.find({}))
        productsLen = len(products)
        # Go back to home page
        #return render_template ("index2.html", shoppingCart=shoppingCart, products=products, shopLen=shopLen, productsLen=productsLen, total=total, totItems=totItems, display=display, session=session )
        return render_template ("index2.html", shoppingCart=shoppingCart, products=products, shopLen=shopLen, productsLen=productsLen, total=total, totItems=totItems, display=display )

@app.route("/filter/")
def filter():
    if request.args.get('category'):
        query = request.args.get('category')
        #shirts = db.execute("SELECT * FROM shirts WHERE typeClothes = :query ORDER BY samplename ASC", query=query )
        products=list(db.products.find({"category":query}))
        productsLen = len(products)
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    if 'user' in session:
        # Rebuild shopping cart
        #shoppingCart = db.execute("SELECT samplename, image, SUM(qty), SUM(subTotal), price, id FROM cart GROUP BY samplename")
        shopLen = len(shoppingCart)
        for i in range(shopLen):
            total += shoppingCart[i]["SUM(subTotal)"]
            totItems += shoppingCart[i]["SUM(qty)"]
        # Render filtered view
       # return render_template ("index.html", shoppingCart=shoppingCart, products=products, shopLen=shopLen, productsLen=productsLen, total=total, totItems=totItems, display=display, session=session )
    # Render filtered view
    return render_template ( "index2.html", products=products, shoppingCart=shoppingCart, productsLen=productsLen, shopLen=shopLen, total=total, totItems=totItems, display=display)

@app.route("/checkout/")
def checkout():
    # Update purchase history of current customer
    shoppingCart = []
    uid = None
    if session and "uid" in session and session["uid"] in shoppingHash:
       shoppingCart = shoppingHash[session["uid"]]
       uid = session["uid"]

    if len(shoppingCart) > 0:
        total = 0
        totItems = 0
        for item in shoppingCart:
           total += item["subTotal"]
           totItems += item["qty"]
        return render_template("checkout.html", shoppingCart=shoppingCart, shopLen=len(shoppingCart), total=total, totItems=totItems, key=stripe_keys["publishable_key"], session = session, uid=uid)
    return redirect('/shop')

@app.route("/remove/", methods=["GET"])
def remove():
    shoppingCart = []
    if session and "uid" in session and session["uid"] in shoppingHash:
       shoppingCart = shoppingHash[session["uid"]]
    
    item_id = int(request.args.get("id"))

    newShoppingCart = []
    if len(shoppingCart) > 0:
        for item in shoppingCart:
            if item["item_id"] != item_id:
                newShoppingCart.append(item)
    
    shoppingCart = newShoppingCart

    # Update the hash
    if session and "uid" in session and session["uid"] in shoppingHash:
        shoppingHash[session["uid"]] = shoppingCart
    
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    for i in range(shopLen):
       total += shoppingCart[i]["subTotal"]
       totItems += shoppingCart[i]["qty"]

    return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )

@app.route("/cart/")
def cart():
    products = list(db.products.find({}))
    productsLen = len(products)
    shoppingCart = []
    if session and "uid" in session and session["uid"] in shoppingHash:
        shoppingCart = shoppingHash[session["uid"]]
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    for i in range(shopLen):
        total += shoppingCart[i]["subTotal"]
        totItems += shoppingCart[i]["qty"]
    return render_template ( "cart.html", products=products, shoppingCart=shoppingCart, productsLen=productsLen, shopLen=shopLen, total=total, totItems=totItems, display=display)

@app.route("/logout/")
def logout():
    # clear shopping hash
    if session and "uid" in session and session["uid"] in shoppingHash:
       del shoppingHash[session["uid"]]
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")

@app.route("/order/success", methods=["GET"])
def order_success():
    uid = int(request.args.get('uid'))
    order = {}
    if uid in orderHash:
        order = orderHash[uid]
    # Insert the order into orders collection if payment is successful
    ret = db.orders.insert_one(order)
    if not ret.acknowledged:
        print("Error: Failed to insert into orders collection")
    else:
        orderHash[uid] = [] 
        shoppingHash[uid] = []
    return redirect('/shop') 

@app.route('/payment', methods=['POST'])
def payment():
    uid = int(request.form["uid"])
    address1 = request.form["address1"]
    address2 = request.form["address2"]
    city = request.form["city"]
    state = request.form["state"]
    zipcode = request.form["zip"]

    shoppingCart = []
    if uid in shoppingHash:
        shoppingCart = shoppingHash[uid]
    if len(shoppingCart) > 0:
        itemIdToItemNameMap = {}

        # Create an order
        allOrders = db.orders.find({})
        maxExistingOrderId = 0
        for eOrder in allOrders:
            if "order_id" in eOrder:
                order_id = int(eOrder["order_id"])
                maxExistingOrderId = max(order_id, maxExistingOrderId)
        order = {}
        order["order_id"] = maxExistingOrderId + 1
        order["order_items"] = []
        order["order_total"] = 0

        for item in shoppingCart:
            itemIdToItemNameMap[item["item_id"]] = item["samplename"]
            itemIsReturnable = False
            order["order_total"] += item["subTotal"]
            foundItem = list(db.products.find({"product_id": item["item_id"]}))
            if (len(foundItem) == 1):
                foundItemCategory = list(db.categories.find({"category_name": foundItem[0]["category"]}))
                if (len(foundItemCategory) == 1):
                    if (foundItemCategory[0]["isreturnable"]):
                        itemIsReturnable = True
            order["order_items"].append({"item_id": item["item_id"], "item_qty": item["qty"], "item_price": item["price"], "item_isreturnable": itemIsReturnable})

        order["order_date"] = datetime.now()
        order["ordered_by"] = session["uid"]
        order["order_delivery_type"] = "delivery"
        order["payment_method"] = "card"
        order["payment_id"] = 1
        order["delivery_address"] = {"line1": address1, "city": city, "state": state, "postcode": zipcode}
        order["order_status"] = 1
        order["order_isreturnable"] = False
        for o in order["order_items"]:
            if o["item_isreturnable"]:
                order["order_isreturnable"] = True
                break

        order["order_return_status"] = 0
        

        # Make a stripe payment
        stripeItems = []
        for item in order["order_items"]:
           stripeItems.append({"price_data": {"currency": "usd", "product_data": {"name": itemIdToItemNameMap[item["item_id"]]}, "unit_amount": item["item_price"]*100}, "quantity": item["item_qty"]})
        
        orderHash[uid] = order

        stripeSession = stripe.checkout.Session.create(
            #line_items=[
            #   {
            #    'price_data': {
            #        'currency': 'usd',
            #        'product_data': {
            #            'name': 'T-shirt',
            #        },
            #        'unit_amount': 2000,
            #    },
            #    'quantity': 1,
            #    }
            #],
            line_items = stripeItems,
            mode='payment',
            success_url='http://localhost:5000/order/success?uid='+str(uid),
            
            cancel_url='http://localhost:5000/shop',
        )

        # Insert the order into orders collection if payment is successful
        #if "paid" in stripeSession.payment_status:
        #    try:
        #        ret = db.orders.insert_one(order)
        #        if not ret["acknowledged"]:
        #            print("Error: Failed to insert into orders collection")
        #        else:
        #           del shoppingHash[uid]
        #    except:
        #        print("Error: Exception caught when trying to insert in to orders collection")
        return redirect(stripeSession.url, code=303)
    return redirect('/shop')

@app.route('/orders/')
def orders_history(user_id = None):
    shoppingCart = []
    
    if session and "uid" in session and session["uid"] in shoppingHash:
       shoppingCart = shoppingHash[session["uid"]]
    
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    for i in range(shopLen):
       total += shoppingCart[i]["subTotal"]
       totItems += shoppingCart[i]["qty"]

    uid = user_id
    ordersData = []
    if uid is None and session and "uid" in session:
        uid = session["uid"]
    if uid:
        orders = list(db.orders.find({"ordered_by": uid}))
        for order in orders:
            orderItems = []
            for item in order["order_items"]:
                item_id = item["item_id"]
                item_isreturnable = item["item_isreturnable"]
                items = list(db.products.find({"product_id": item_id}))
                item_name = items[0]["product_name"]
                item_img = items[0]["product_image"]
                orderItems.append({
                   "item_id": item_id,
                   "item_name": item_name,
                   "item_qty": item["item_qty"],
                   "item_price": item["item_price"],
                   "item_img": item_img,
                   "item_isreturnable": item_isreturnable
                })
            order_id = order["order_id"]
            order_delivery_type = order["order_delivery_type"]
            order_payment_method = order["payment_method"]
            order_date = order["order_date"]
            order_total = order["order_total"]
            order_isreturnable = order["order_isreturnable"]
            order_status = order["order_status"]
            order_return_status = order["order_return_status"]
            tracking_data = getTrackingData(order_status)
            return_tracking_data = getReturnTrackingData(order_return_status)
            order_refund_amount = 0
            if order_return_status > 0:
                allReturns = list(db.returns.find({"original_order_id": order_id}))
                if len(allReturns) == 1:
                    return_order = allReturns[0]
                    order_refund_amount = return_order["return_total"]

            ordersData.append({"order_id": order_id, "orderItems": orderItems, "order_delivery_type": order_delivery_type, "order_payment_method": order_payment_method, "order_date": order_date, "order_total": order_total, "order_isreturnable": order_isreturnable, "order_status": order_status, "order_return_status": order_return_status, "tracking_data": tracking_data, "return_tracking_data": return_tracking_data, "order_refund_amount": order_refund_amount})
    return render_template("orders.html", ordersData=ordersData, ordersLen=len(ordersData), shopLen=shopLen, shoppingCart=shoppingCart, total=total, totItems=totItems, uid=uid)

if __name__ == '__main__':
    app.run(port=5000, debug=True) #port > 1024
