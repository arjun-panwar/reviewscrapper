# doing necessary imports

from flask import Flask, render_template, request, jsonify
# from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
import csv
from flask_cors import CORS,cross_origin

app = Flask(__name__)


def homePage():
    return render_template("index.html")

@app.route('/',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()

def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")  # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient(
                "mongodb+srv://arjun:arjun2001@cluster0.0h5a3.mongodb.net/crawlerDB?retryWrites=true&w=majority")  # opening a connection to Mongo
            db = dbConn['crawlerDB']  # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            if reviews.count() > 500:  # if there is a collection with searched keyword and it has records in it
                # now we will open a file for writing
                file="static/"+searchString +".csv"
                data_file = open(file, 'w')

                # create the csv writer object
                csv_writer = csv.writer(data_file)

                # Counter variable used for writing
                # headers to the CSV file
                count = 0
                i = 0

                for review in reviews:
                    if count == 0:
                        # Writing headers of CSV file
                        header = review.keys()
                        csv_writer.writerow(header)
                        count += 1

                    # Writing data of CSV file
                    csv_writer.writerow(review.values())
                    i=i+1

                data_file.close()
                return render_template('results.html',result = searchString,total=i )  # show the results to user
            else:

                table = db[searchString]  # creating a collection with the same name as search string. Tables and Collections are analogous.

                if reviews.count() > 0:
                    table.delete_many({})
                reviews = []  # initializing an empty list for reviews

                flipkart_url = "https://www.flipkart.com/search?q=" + searchString  # preparing the URL to search the product on flipkart
                uClient = uReq(flipkart_url)  # requesting the webpage from the internet
                flipkartPage = uClient.read()  # reading the webpage
                uClient.close()  # closing the connection to the web server
                flipkart_html = bs(flipkartPage, "html.parser")  # parsing the webpage as HTML
                bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})  # seacrhing for appropriate tag to redirect to the product link
                 # the first 3 members of the list do not contain relevant information, hence deleting them.
                box = bigboxes[3]  # taking the first iteration (for demo)
                productLink = "https://www.flipkart.com" + box.div.div.div.a['href']  # extracting the actual product link
                prodRes = requests.get(productLink)  # getting the product page from server
                prod_html = bs(prodRes.text, "html.parser")  # parsing the product page as HTML

                rev_link_boxs = prod_html.findAll("div", {"class": "_1AtVbE col-12-12"})

                j=0
                running = True
                del rev_link_boxs[0:7]
                while running:
                     try:
                        link_box= rev_link_boxs[j].find("div", {"class": "col JOpGWq"})
                        rpLink = "https://www.flipkart.com" + link_box.a['href']
                        running = False
                     except:
                         j=j+1
                page = True
                p=1
                lpage=True
                lastp=2
                i=0

                while p<lastp:
                    rpLink=rpLink[0:(rpLink.find("&aid=") + 5)] + "overall&page="+str(p)
                    revpRes = requests.get(rpLink)  # getting the review page from server
                    revp_html = bs(revpRes.text, "html.parser")  # parsing the product page as HTML


                    commentboxes = revp_html.find_all('div', {'class': "_1AtVbE col-12-12"})  # finding the HTML section containing the customer comments

                    #  iterating over the comment section to get the details of customer and their comments
                    while lpage:
                        last=commentboxes[-1]
                        lastp = int(last.div.div.find_all('span')[0].text[10:].replace(",", ""))
                        lpage=False
                    p=p+1

                    del commentboxes[0:4]
                    del commentboxes[-1]
                    for commentbox in commentboxes:
                        try:
                            name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text


                        except:

                            name = 'No Name'

                        try:
                            rating = (commentbox.div.div.div.div.text)[0:1]

                        except:
                            rating = 'No Rating'

                        try:
                            commentHead = commentbox.div.div.div.p.text
                        except:
                            commentHead = 'No Comment Heading'
                        try:
                            comtag = commentbox.div.div.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                        except:
                            custComment = 'No Customer Comment'
                        # fw.write(searchString+","+name.replace(",", ":")+","+rating + "," + commentHead.replace(",", ":") + "," + custComment.replace(",", ":") + "\n")
                        i = i + 1
                        mydict = {"_id":i, "Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                                  "Comment": custComment}  # saving that detail to a dictionary
                        x = table.insert_one(
                            mydict)  # insertig the dictionary containing the rview comments to the collection
                        reviews.append(mydict)
                        # appending the comments to the review list



                # now we will open a file for writing
                file = "static/" + searchString + ".csv"
                data_file = open(file, 'w')
                # create the csv writer object
                csv_writer = csv.writer(data_file)

                # Counter variable used for writing
                # headers to the CSV file
                count = 0

                for review in reviews:
                    if count == 0:
                        # Writing headers of CSV file
                        header = review.keys()
                        csv_writer.writerow(header)
                        count += 1

                    # Writing data of CSV file
                    csv_writer.writerow(review.values())

                data_file.close()
                return render_template('results.html', result=searchString,total=i )
        except Exception as e:
            dbConn = pymongo.MongoClient("mongodb+srv://arjun:arjun2001@cluster0.0h5a3.mongodb.net/crawlerDB?retryWrites=true&w=majority")  # opening a connection to Mongo
            db = dbConn['crawlerDB']  # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            if reviews.count() > 500:  # if there is a collection with searched keyword and it has records in it
                # now we will open a file for writing
                file = "static/" + searchString + ".csv"
                data_file = open(file, 'w')

                # create the csv writer object
                csv_writer = csv.writer(data_file)

                # Counter variable used for writing
                # headers to the CSV file
                count = 0

                for review in reviews:
                    if count == 0:
                        # Writing headers of CSV file
                        header = review.keys()
                        csv_writer.writerow(header)
                        count += 1

                    # Writing data of CSV file
                    csv_writer.writerow(review.values())

                data_file.close()
                return render_template('results.html', result=searchString,total=i )  # show the results to user
            else:
                print('The Exception message is: ', e)
                return 'something is wrong'
    else:
        return render_template('index.html')


if __name__ == "__main__":
    #app.run(port=8028, debug=True)  # running the app on the local machine on port 8000
    app.run(debug=True)
