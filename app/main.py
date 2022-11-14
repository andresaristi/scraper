# Importing necessary modules

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

tasks = []
val = ""

@app.route('/')
def index():
  return """<html>
    <body>     
       <form action = "http://localhost:5000/login" method = "post">
          <p>Enter category :</p>
          <p><input type = "text" name = "cat" /></p>
          <p><input type = "submit" value = "Download CSV" /></p> 
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

@app.route('/succes/<c>')
def success(c):
    val = c
    response = Response('The CSV file has been generated for category %s!' % c)

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
        url = "https://www.coursera.org/search?query="+str(c)+"&page=1&index=prod_all_launched_products_term_optimization&entityTypeDescription=Courses"
        driver.get(url)
        num = driver.find_elements(By.CSS_SELECTOR, '.box.number')
        pages=int(num[-1].text)
        driver.close()
        for i in range(1,pages+1):
            driver = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                           options=firefox_options)
            url = "https://www.coursera.org/search?query="+str(c)+"&page="+str(i)+"&index=prod_all_launched_products_term_optimization&entityTypeDescription=Courses"
            driver.get(url)
            courses= driver.find_elements(By.CSS_SELECTOR, '[data-click-key="search.search.click.search_card"]')
            links = []
            for course in courses:
                data = course.text.split("\n")
                if data[0]!='Free':
                    course_provider.append(data[0])
                    course_name.append(data[1])
                else:
                    course_provider.append(data[1])
                    course_name.append(data[2])
                url1 = str(course.get_attribute('href'))
                links.append(url1)
            for link in links:
                driver1 = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                            options=firefox_options)
                driver1.get(link)
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
                elements = driver1.find_elements(By.XPATH, "//span[contains(text(), 'ratings')]")
                if(len(elements) > 0):
                    res = re.search(r"^([^r]+)([r])",elements[0].text)
                    if res:
                        course_rating.append(res.group(1).strip())
                    else:
                        course_rating.append(0)
                else:
                    course_rating.append(0) 
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
        courses_info = [[name, provider, description, enrrolled, ratings] for name, provider, description, enrrolled, ratings in zip(course_name,course_provider,course_description,course_enrolled,course_rating)]
        courses_by_search = pd.DataFrame(courses_info)
        courses_by_search.columns = ["Name","Provider","Description","# enrolled","# ratings"]
        print(courses_by_search)
        courses_by_search.to_csv('courses_'+c+'.csv',index=False)

        #resp.headers["Content-Disposition"] = "attachment; filename=coursera_results.csv"
        #resp.headers["Content-Type"] = "text/csv"
        #return resp

    return response

def data(c):
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
  url = "https://www.coursera.org/search?query="+str(c)+"&page=1&index=prod_all_launched_products_term_optimization&entityTypeDescription=Courses"
  driver.get(url)
  num = driver.find_elements(By.CSS_SELECTOR, '.box.number')
  pages=int(num[-1].text)
  driver.close()
  for i in range(1,pages+1):
      driver = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                           options=firefox_options)
      url = "https://www.coursera.org/search?query="+str(c)+"&page="+str(i)+"&index=prod_all_launched_products_term_optimization&entityTypeDescription=Courses"
      driver.get(url)
      courses= driver.find_elements(By.CSS_SELECTOR, '[data-click-key="search.search.click.search_card"]')
      links = []
      for course in courses:
          data = course.text.split("\n")
          if data[0]!='Free':
              course_provider.append(data[0])
              course_name.append(data[1])
          else:
              course_provider.append(data[1])
              course_name.append(data[2])
          url1 = str(course.get_attribute('href'))
          links.append(url1)
      for link in links:
          driver1 = webdriver.Chrome(service=Service('/usr/local/bin/geckodriver'),
                            options=firefox_options)
          driver1.get(link)
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
          elements = driver1.find_elements(By.XPATH, "//span[contains(text(), 'ratings')]")
          if(len(elements) > 0):
              res = re.search(r"^([^r]+)([r])",elements[0].text)
              if res:
                  course_rating.append(res.group(1).strip())
              else:
                  course_rating.append(0)
          else:
              course_rating.append(0) 
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
  courses_info = [[name, provider, description, enrrolled, ratings] for name, provider, description, enrrolled, ratings in zip(course_name,course_provider,course_description,course_enrolled,course_rating)]
  courses_by_search = pd.DataFrame(courses_info)
  courses_by_search.columns = ["Name","Provider","Description","# enrolled","# ratings"]
  print(courses_by_search)
  courses_by_search.to_csv('coursera_'+c+'.csv',index=False)

  
if __name__ == '__main__':
  app.run(debug=True)
