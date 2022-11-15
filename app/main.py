# Importing necessary modules
from github import Github
from flask import Flask, make_response, redirect, url_for, Response  
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
import re
from time import sleep
import flask
import queue
import pandas as pd

app= Flask(__name__)

# Global variable where the category item is saved
val = ""

# Simple interface to receive the category for the search
@app.route('/')
def index():
  return """<html>
    <body>     
       <form action = "http://localhost:5000/login" method = "post">
          <p>Enter category :</p>
          <p><input type = "text" name = "cat" /></p>
          <p><input type = "submit" value = "Generate CSV" /></p> 
       </form>     
    </body>
 </html>"""
 
@app.route('/login', methods=['POST', 'GET'])
def login():
    if flask.request.method == 'POST':
        category = flask.request.form['cat']
        return redirect(url_for('success', c=category))
    else:
        category = flask.request.args.get('cat')
        return redirect(url_for('success', c=category))

# Function to indicate the success of the search
@app.route('/succes/<c>')
def success(c):
    val = c
    response = Response('Generating CSV File to https://github.com/andresaristi/files/blob/main/files/coursera_%s.csv! be patient, it make take some minutes ...' % c.replace(" ","%20"))

    # Function that runs after the request
    @response.call_on_close
    def data():
        c = val
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        driver = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                          options=firefox_options)

        # Declaring the lists where the info about the courses will be stored
        course_name = []
        course_provider = []
        course_description =[]
        course_rating = []
        course_enrolled = []

        # Coursera's url
        url = "https://www.coursera.org/search?query="+str(c)+"&page=1&index=prod_all_launched_products_term_optimization&entityTypeDescription=Courses"
        driver.get(url)

        # num will give the elements with the page numbers
        num = driver.find_elements(By.CSS_SELECTOR, '.box.number')
        # We take the last one as the number of pages to iterate
        pages=int(num[-1].text)
        driver.close()
        # We iterate through the pages
        for i in range(1,pages+1):
            driver = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                           options=firefox_options)
            url = "https://www.coursera.org/search?query="+str(c)+"&page="+str(i)+"&index=prod_all_launched_products_term_optimization&entityTypeDescription=Courses"
            driver.get(url)
            # Getting all the courses
            courses= driver.find_elements(By.CSS_SELECTOR, '[data-click-key="search.search.click.search_card"]')
            links = []
            for course in courses:
                # We will take the provider and the name of the course from the course's card
                data = course.text.split("\n")
                if data[0]!='Free':
                    course_provider.append(data[0])
                    course_name.append(data[1])
                else:
                    course_provider.append(data[1])
                    course_name.append(data[2])
                # We get the link to the course to get the other info
                url1 = str(course.get_attribute('href'))
                links.append(url1)
            # We iterate through the links to the courses
            for link in links:
                driver1 = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                            options=firefox_options)
                driver1.get(link)
                # We get the element with the students enrolled
                elements = driver1.find_elements(By.XPATH, "//span[contains(text(), 'enrolled')]")
                if(len(elements) > 0):
                    course_enrolled.append(re.search(r"[0-9,.]+",elements[0].text)[0])
                else:
                    elements = driver1.find_elements(By.XPATH, "//span[contains(text(), 'ratings')]")  
                    if len(elements) > 0:
                        res = re.search(r"([0-9,.]+)( already enrolled)",elements[0].text)
                        if res:
                            course_enrolled.append(res.group(1))
                        else:
                            course_enrolled.append(0)     
                    else:
                        course_enrolled.append(0)
                # We get the element with the ratings        
                elements = driver1.find_elements(By.XPATH, "//span[contains(text(), 'ratings')]")
                if(len(elements) > 0):
                    res = re.search(r"^([^r]+)([r])",elements[0].text)
                    if res:
                        course_rating.append(res.group(1).strip())
                    else:
                        course_rating.append(0)
                else:
                    course_rating.append(0) 
                # We get the element with the description of the course
                elements = driver1.find_elements(By.XPATH, '//div[contains(@class, "About")]')
                if len(elements) > 0:
                    text = ""
                    paragraphs= elements[0].find_elements(By.CSS_SELECTOR, 'p')
                    for paragraph in paragraphs:
                        if len(paragraph.text) > 200:
                            text += "\n\n"+paragraph.text
                    course_description.append(text.strip("\n"))
                driver1.close()
        driver.close()
        # We create a list with the info to be pase to the dataframe
        courses_info = [[name, provider, description, enrrolled, ratings] for name, provider, description, enrrolled, ratings in zip(course_name,course_provider,course_description,course_enrolled,course_rating)]
        # We create the dataframe
        courses_by_search = pd.DataFrame(courses_info)
        courses_by_search.columns = ["Name","Provider","Description","# enrolled","# ratings"]
        # We print the dataframe to console
        print(courses_by_search)
        # Authenticating to github
        g = Github(token)
        repository = g.get_user().get_repo('files')
        filename = 'files/coursera_'+c+'.csv'
        all_files = []
        contents = repository.get_contents("")
        csv = courses_by_search.to_csv(index=False)
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repository.get_contents(file_content.path))
            else:
                file = file_content
                all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))
        # Updating or creating a new file
        if filename in all_files:
            contents = repository.get_contents(filename)
            repository.update_file(contents.path, "update_file via PyGithub", csv, contents.sha)
        else:
            repository.create_file(filename, "create_file via PyGithub", csv)
    return response

if __name__ == '__main__':
  app.run(debug=True)
