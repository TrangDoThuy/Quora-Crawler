from selenium import webdriver
from bs4 import BeautifulSoup
import time
import os

DEBUG = 1

def crawlTopicHierarchy(topic):
    if (DEBUG): print ("In crawlTopicHierarchy()...")
    # Create files for topic names and topic URLs
    str_file_topic_names = "topic_names_"+topic+".txt"
    file_topic_names = open(str_file_topic_names, mode = 'w')
    
    str_file_topic_urls = "topic_urls_"+topic+".txt"
    file_topic_urls = open(str_file_topic_urls, mode = 'w')

    # Starting node link
    url = 'https://www.quora.com/topic/'+topic

    depth = 0
    topic_names_hierarchy = ""

    # Create stack to keep track of links to visit and visited
    urls_to_visit = []
    urls_to_visit_without_depth = []
    urls_visited = []
    # Add root to stack
    urls_to_visit.append([url, depth])

    #if (DEBUG): print urls_to_visit

    while (len(urls_to_visit)):
        # Pop stack of stack to get URL and current depth
        url, current_depth = urls_to_visit.pop(0)
        if (DEBUG): print ('Current url:{0} current depth:{1} depth:{2}'.format(url, str(current_depth), str(depth)))
        page_name = url[21:].split('?')[0]
        if (DEBUG): print (page_name)
        
        urls_visited.append([url, page_name])

        print("current depth = ", current_depth)
        print("depth = ",depth)
        if (current_depth < depth):
            for i in range(depth - current_depth):
                j = topic_names_hierarchy.rfind(" ")
                if (j != -1):
                    topic_names_hierarchy = topic_names_hierarchy[:j]
            depth = current_depth

        # Record topic Name
        file_topic_names.write(page_name[7:] + '\n')

        depth += 1
        if(depth>3):
            break;
        # Record topic URL
        file_topic_urls.write(url + '\n')

        url_about = url.split('?')[0] + "/about?share=1"

        chromedriver = "chromedriver"   # Needed?
        os.environ["webdriver.chrome.driver"] = chromedriver    # Needed?
        browser = webdriver.Chrome()
        browser.get(url_about)

        # Fetch /about page
        src_updated = browser.page_source
        src = ""
        while src != src_updated:
            time.sleep(.5)
            src = src_updated
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            src_updated = browser.page_source

        html_source = browser.page_source

        soup = BeautifulSoup(html_source, features = "lxml")
        #raw_topics = soup.find_all(attrs={"class":"topic_name"})
        #print (raw_topics)

        # Split to get just child topics

        split_html = html_source.split('Related Topics')
        
        if (len(split_html) == 1):
            print("stop here")
            browser.quit()
        else:
            split_html = split_html[1]
            # Split to separate child topics
            split_child = split_html.split('<a class="q-box qu-cursor--pointer qu-hover--textDecoration--none qu-userSelect--text Link___StyledBox-t2xg9c-0 roKEj" ')
            child_count = 0
            print("len(split_child) ",len(split_child))

            for i in range(1, len(split_child)):
                end=int(split_child[i].index('"', 10))
                link_url = split_child[i][6:end]
                if link_url not in urls_to_visit_without_depth:
                    urls_to_visit.append([link_url, depth])
                    urls_to_visit_without_depth.append(link_url)
                child_count += 1

            browser.quit()
            if (topic_names_hierarchy):
                topic_names_hierarchy += " " + page_name
            else:
                topic_names_hierarchy += page_name
            if (DEBUG): print ("Links read: " + str(child_count))

    # File cleanup
    file_topic_names.close()
    file_topic_urls.close()
    

    return urls_visited

# Crawl each topic url and save each question url
def crawlTopicQuestions(topic_urls,main_topic):
    if (DEBUG): print ("In crawlTopicQuestions()...", topic_urls)
    
    str_question_urls = "question_urls_"+main_topic+".txt"
    file_question_urls = open(str_question_urls, mode = 'w')
    
    str_file_topic_urls = "topic_urls_"+main_topic+".txt"
    file_topic_urls = open(str_file_topic_urls, mode = 'w')
    
    # Create a topic page and download all question text and URL
    #file_question_urls =  open("question_urls.txt", mode = 'w')
    #file_topic_urls = open("topic_urls.txt", mode = 'r')

    total = 0

    for topic in range(len(topic_urls)):
        current_url = topic_urls[topic][0]
        current_topic = topic_urls[topic][1]
        if (not current_url): # Needed?
            break

        # Open browser
        chromedriver = "chromedriver"   # Needed?
        os.environ["webdriver.chrome.driver"] = chromedriver    # Needed?
        browser = webdriver.Chrome()
        browser.get(current_url)

        # Fetch current page
        #fw = open("page", mode = 'w')
        src_updated = browser.page_source
        src = ""
        while src != src_updated:
            time.sleep(.5)
            src = src_updated
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            src_updated = browser.page_source
        
        html_source = browser.page_source
        #print(html_source)
        #fw.write(html_source.encode('utf8'))
        #fw.close()
        browser.quit()
        
        split_html = html_source.split("<a class=\"q-box qu-display--block qu-cursor--pointer qu-hover--textDecoration--underline qu-userSelect--text Link___StyledBox-t2xg9c-0 roKEj\"")
        total = 0
        for i in range(1,len(split_html)):

            end=int(split_html[i].index('"', 10))
            link_url = split_html[i][7:end]
            file_question_urls.write(link_url + " " + current_topic + '\n')
            total += 1
    print ("Total questions:{0}".format(str(total)))
    return 0

def normalize(part):
    while(("<" in part)and(">" in part)) :
        index_start = part.find("<")
        index_end = part.find(">",index_start)
        sub = part[index_start:index_end+1]
        part = part.replace(sub,"")
    if("Continue Reading" in part):
        index = part.find("Continue Reading")
        part = part[:index]
    if("window." in part):
        index = part.find("window.")
        part = part[:index]
    #print(part)
    return part;

# Crawl a question URL and save data into a csv file
def crawlQuestionData(main_topic):
    if (DEBUG): print ("In crawlQuestionData...")
    
    # Open question url file
    str_question_urls = "question_urls_"+main_topic+".txt"
    file_question_urls = open(str_question_urls, mode = 'r')
    
    str_data_urls = "data_"+main_topic+".txt"
    file_data = open(str_data_urls, mode = 'w', encoding = 'utf-8')
    
    # file_question_urls = open(file, mode = 'r')
    # file_data = open("answers.txt", mode = 'w')
    # file_users = open("users.txt", mode = 'w')
    
    current_line = file_question_urls.readline()
    while (current_line):
        if (DEBUG): print ("***", current_line)
        
        print ("***", current_line)
        question_id = current_line.split(" ")[0]
        current_topic = current_line.split(" ")[1].rstrip('\n')
        if (DEBUG): print (question_id, "-", current_topic)
    
        # Open browser to current_question_url
        chromedriver = "chromedriver"   # Needed?
        os.environ["webdriver.chrome.driver"] = chromedriver    # Needed?
        browser = webdriver.Chrome()
        browser.get(question_id)
    
        # Fetch page
        src_updated = browser.page_source
        src = ""
        while src != src_updated:
            time.sleep(.5)
            src = src_updated
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            src_updated = browser.page_source
            
        html_source = browser.page_source
        browser.quit()
        
        if("class=\"q-text puppeteer_test_question_title\" style=\"box-sizing: border-box;\"><span class=\"q-box qu-userSelect--text\" style=\"box-sizing: border-box;\"><span style=\"background: none;\">" not in html_source ):
            current_line = file_question_urls.readline()
            continue
            # Find question text
        question_text = html_source.split("class=\"q-text puppeteer_test_question_title\" style=\"box-sizing: border-box;\"><span class=\"q-box qu-userSelect--text\" style=\"box-sizing: border-box;\"><span style=\"background: none;\">")[1]
        question_text = question_text.split("</span>")[0]
        file_data.write(question_text+'\n')
        #question_text = "{{{" + question_text[len(question_text)-1] + "}}}"
        if (DEBUG): print ("Question text:{0}".format(question_text))
        
        answer_list = []
        
        # Split html to parts
        split_html = html_source.split('<div class="q-relative spacing_log_answer_content puppeteer_test_answer_content" style="box-sizing: border-box; position: relative;">')
        if (DEBUG): print ("Length of split_html:{0}".format(len(split_html)))
        if(len(split_html)<30):
            current_line = file_question_urls.readline()
            continue
        for i in range(1, len(split_html)-2):
            if(i>10):
                break
            #print("****") 
            part = split_html[i]
            part = normalize(part)
            #print("******")
            answer_list.append(part)
            file_data.write(part+"\n\n")
        current_line = file_question_urls.readline()

    file_question_urls.close()
    file_data.close()
    # file_users.close()
    return 0

def main():
    topic_list = ['Jobs-and-Careers','Money','Relationships','Sex','Life-and-Living-2']
    for main_topic in topic_list:
        topics = crawlTopicHierarchy(main_topic)
        crawlTopicQuestions(topics,main_topic)
        crawlQuestionData(main_topic)
        #crawlQuestionData("question_urls.txt")
    return 0

if __name__ == "__main__": main()

