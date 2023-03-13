from flask import Flask, render_template, request,  jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen, Request
import logging
import pymongo
logging.basicConfig(filename="app.log", level=logging.INFO)
 
app = Flask(__name__)

@app.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')

@app.route('/movie', methods=['POST', 'GET'])
def index():
    if request.method=='POST':
        try:
            searchString = request.form['content'].replace(" ","")
            imdbUrl = "https://www.imdb.com/find/?q=" + searchString
            req = Request( url=imdbUrl, headers={'User-Agent': 'Mozilla/5.0'})
            imdbPage = urlopen(req).read()
            imdbHtml = bs(imdbPage, 'html.parser')
            titleBox = imdbHtml.find("section", {"data-testid":"find-results-section-title"})
            movieSelect = titleBox.find_all('div',{'class':'sc-17bafbdb-2 ffAEHI'})[0].find('ul').find('li').find_all('div',{'class':'ipc-metadata-list-summary-item__c'})[0].find('div').a['href']
            moviePageLink = "https://www.imdb.com" + movieSelect
            req = Request( url=moviePageLink, headers={'User-Agent': 'Mozilla/5.0'})
            mainMoviePage = urlopen(req).read()
            mainMovieHtml = bs(mainMoviePage, 'html.parser')
            movieReviewSelect = mainMovieHtml.find_all('section', {'data-testid':"UserReviews"})[0].div.div.a['href']
            movieReviewPageLink = "https://www.imdb.com" + movieReviewSelect
            finalLink = movieReviewPageLink.split("reviews")[0].strip() + "reviews?sort=reviewVolume&dir=desc&ratingFilter=0"


            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Movie Name, Rating, Review Heading, Review detail \n"
            fw.write(headers)
            reviews = []

            req = Request( url=finalLink, headers={'User-Agent': 'Mozilla/5.0'})
            reviewPage = urlopen(req).read()
            reviewPageHtml = bs(reviewPage, 'html.parser')
            reviewsList = reviewPageHtml.find_all('div', {'class':'lister-item-content'})

            movieTitle = reviewPageHtml.find_all('div',{'class':'subpage_title_block__right-column'})[0].div.h3.a.text.strip()
            for review in reviewsList:
        
                try:
                    rating = review.div.span.span.text + "/10"
                except:
                    rating = 'No Rating'
                    logging.info("rating")
                    
                try:
                    reviewHeading = review.find('a').text.strip()
                except:
                    commentHead = 'No Comment Heading'
                    logging.info(commentHead)
                    
                try:
                    reviewDetail = review.find_all('div',{'class':'content'})[0].div.text.strip()
                except Exception as e:
                    logging.info(e)

                mydict = {"Movie Name": movieTitle, "Rating": rating, "Review Heading": reviewHeading,
                            "Review detail": reviewDetail}
                reviews.append(mydict)
            logging.info("log my final result {}".format(reviews))
            
            client = pymongo.MongoClient("mongodb+srv://mongodbfirst:mongodbfirst@<password>.v394uy7.mongodb.net/?retryWrites=true&w=majority")
            db =client['imdb_reviews_db']
            coll= db['imdb_reviews_collections']
            coll.insert_many(reviews)


            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            logging.info(e)
            return 'something is wrong'
    # return render_template('results.html')

    else:
        return render_template('index.html')


if __name__=="__main__":
    app.run(host="0.0.0.0")
